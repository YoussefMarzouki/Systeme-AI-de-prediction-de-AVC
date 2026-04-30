from flask import Blueprint, request, jsonify
from app.services.prediction_service import PredictionService
from app.core.db import db
from app.models.analyses import AnalyseIA, AnalyseSymptomes, EvaluationRisque
from app.models.image_irm import ImageIRM
from app.models.donnees_cliniques import DonneesCliniques
import uuid

prediction_bp = Blueprint('prediction', __name__)
prediction_service = PredictionService()


def _normalize_prediction_result(result):
    """Keep a stable report shape even when the model API returns aliases."""
    normalized = dict(result or {})

    if normalized.get("symptom_probability") is None and normalized.get("probability") is not None and not normalized.get("predicted_class"):
        normalized["symptom_probability"] = normalized.get("probability")
    if normalized.get("symptom_response") is None:
        normalized["symptom_response"] = normalized.get("response") or normalized.get("ai_assessment")
    if normalized.get("symptom_urgency") is None:
        normalized["symptom_urgency"] = normalized.get("urgency")
    if normalized.get("image_probability") is None and normalized.get("probability") is not None and normalized.get("predicted_class"):
        normalized["image_probability"] = normalized.get("probability")

    image_probability = normalized.get("image_probability")
    symptom_probability = normalized.get("symptom_probability")
    if normalized.get("fused_probability") is None and image_probability is not None and symptom_probability is not None:
        normalized["fused_probability"] = (0.6 * float(image_probability)) + (0.4 * float(symptom_probability))

    return normalized


def _merge_report_content(existing_content, new_result):
    """Merge sequential symptom-only and image-only predictions into one report."""
    content = dict(existing_content or {})
    result = _normalize_prediction_result(new_result)

    for key, value in result.items():
        if value is not None:
            content[key] = value

    image_probability = content.get("image_probability")
    symptom_probability = content.get("symptom_probability")
    if image_probability is not None and symptom_probability is not None:
        content["fused_probability"] = (0.6 * float(image_probability)) + (0.4 * float(symptom_probability))

    return content

@prediction_bp.route('/api/v1/dossiers/<string:dossier_id>/predict', methods=['POST'])
def run_prediction(dossier_id):
    """Lancer une prédiction IA fusionnée pour un dossier
    ---
    tags:
      - Prédictions
    parameters:
      - name: dossier_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            image_url:
              type: string
              description: URL de l'image IRM
              example: "https://res.cloudinary.com/xxx/image.jpg"
            symptoms_text:
              type: string
              description: Texte des symptômes pour le RAG
              example: "Age 65. Symptoms: Paralysie faciale, Faiblesse du bras"
    responses:
      200:
        description: Résultat de la prédiction avec score de risque
        schema:
          type: object
          properties:
            status:
              type: string
            dossier_id:
              type: string
            prediction:
              type: object
              properties:
                image_probability:
                  type: number
                symptom_probability:
                  type: number
                fused_probability:
                  type: number
                risk_level:
                  type: string
      400:
        description: Aucune donnée fournie
      500:
        description: Erreur serveur
    """
    data = request.json
    image_url = data.get('image_url')
    symptoms_text = data.get('symptoms_text')
    
    try:
        if image_url and symptoms_text:
            result = prediction_service.predict_fused(image_url, symptoms_text)
        elif image_url:
            result = prediction_service.predict_image(image_url)
        elif symptoms_text:
            result = prediction_service.predict_symptoms(symptoms_text)
        else:
            return jsonify({"error": "No input data provided"}), 400
            
        result = _normalize_prediction_result(result)

        # Store prediction logic in DB
        try:
            image_record = None
            donnees_record = None
            
            if image_url:
                image_record = ImageIRM.query.filter_by(dossier_id=dossier_id, cheminStockage=image_url).order_by(ImageIRM.dateAcquisition.desc()).first()
                if not image_record:
                    # Fallback to the latest image for this dossier
                    image_record = ImageIRM.query.filter_by(dossier_id=dossier_id).order_by(ImageIRM.dateAcquisition.desc()).first()
            
            if symptoms_text:
                donnees_record = DonneesCliniques.query.filter_by(dossier_id=dossier_id).order_by(DonneesCliniques.dateSaisie.desc()).first()
            
            analyse_ia_record = None
            analyse_symptomes_record = None
            
            # Save Image Prediction
            if result.get("image_probability") is not None and image_record:
                analyse_ia_record = AnalyseIA.query.filter_by(image_id=image_record.idImage).first()
                if analyse_ia_record:
                    analyse_ia_record.probabiliteAVC = result.get("image_probability", 0.0)
                    analyse_ia_record.scoreConfiance = result.get("confidence", 0.0)
                    analyse_ia_record.modeleVersion = "ResNet18-v1"
                else:
                    analyse_ia_record = AnalyseIA(
                        probabiliteAVC=result.get("image_probability", 0.0),
                        scoreConfiance=result.get("confidence", 0.0),
                        modeleVersion="ResNet18-v1",
                        image_id=image_record.idImage
                    )
                    db.session.add(analyse_ia_record)
                
            # Save Symptom Prediction
            if result.get("symptom_probability") is not None and donnees_record:
                analyse_symptomes_record = AnalyseSymptomes.query.filter_by(donnees_cliniques_id=donnees_record.id).first()
                if analyse_symptomes_record:
                    analyse_symptomes_record.valeur = result.get("symptom_probability", 0.0)
                    analyse_symptomes_record.methode = "Groq-RAG"
                else:
                    analyse_symptomes_record = AnalyseSymptomes(
                        valeur=result.get("symptom_probability", 0.0),
                        methode="Groq-RAG",
                        donnees_cliniques_id=donnees_record.id
                    )
                    db.session.add(analyse_symptomes_record)
                
            db.session.flush() # Commit to get IDs without ending transaction
                
            # GENERATE OR UPDATE RAPPORT
            from app.models.rapport import Rapport
            from app.models.dossier_patient import DossierPatient
            from app.models.user import Medecin

            dossier = DossierPatient.query.get(dossier_id)
            if dossier:
                medecin_referent = dossier.medecin_id
                # If no medecin is assigned to the dossier, assign the first available medecin
                if not medecin_referent:
                    first_medecin = Medecin.query.first()
                    medecin_referent = first_medecin.id if first_medecin else 'SYSTEM'
                    
                # Look for an existing report, if none exists, create one
                rapport = Rapport.query.filter_by(dossier_id=dossier_id).first()
                if not rapport:
                    rapport = Rapport(
                        medecin_id=medecin_referent,
                        dossier_id=dossier_id,
                        statut='GENERATED',
                        contenu=result
                    )
                    db.session.add(rapport)
                else:
                    rapport.contenu = _merge_report_content(rapport.contenu, result)
                    rapport.statut = 'UPDATED'

            # Global Evaluation (Risk level): only when both required analyses exist.
            if not analyse_ia_record:
                latest_image = ImageIRM.query.filter_by(dossier_id=dossier_id).order_by(ImageIRM.dateAcquisition.desc()).first()
                if latest_image:
                    analyse_ia_record = AnalyseIA.query.filter_by(image_id=latest_image.idImage).first()

            if not analyse_symptomes_record:
                latest_donnees = DonneesCliniques.query.filter_by(dossier_id=dossier_id).order_by(DonneesCliniques.dateSaisie.desc()).first()
                if latest_donnees:
                    analyse_symptomes_record = AnalyseSymptomes.query.filter_by(donnees_cliniques_id=latest_donnees.id).first()

            if analyse_ia_record and analyse_symptomes_record:
                eval_record = EvaluationRisque.query.filter(
                    (EvaluationRisque.analyse_ia_id == analyse_ia_record.idAnalyse)
                    | (EvaluationRisque.analyse_symptomes_id == analyse_symptomes_record.id)
                ).first()

                score_global = result.get(
                    "fused_probability",
                    result.get("image_probability", result.get("symptom_probability", 0.0))
                )
                if eval_record:
                    eval_record.scoreGlobal = score_global
                    eval_record.niveau = result.get("risk_level", "UNKNOWN")
                    eval_record.dossier_id = dossier_id
                    eval_record.analyse_ia_id = analyse_ia_record.idAnalyse
                    eval_record.analyse_symptomes_id = analyse_symptomes_record.id
                else:
                    db.session.add(EvaluationRisque(
                        scoreGlobal=score_global,
                        niveau=result.get("risk_level", "UNKNOWN"),
                        dossier_id=dossier_id,
                        analyse_ia_id=analyse_ia_record.idAnalyse,
                        analyse_symptomes_id=analyse_symptomes_record.id
                    ))

            db.session.commit()
        except Exception as db_err:
            print("Failed to save prediction to DB:", db_err)
            db.session.rollback()

        return jsonify({
            "status": "success",
            "dossier_id": dossier_id,
            "prediction": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
