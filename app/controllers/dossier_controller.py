from flask import Blueprint, request, jsonify
import uuid
from app.services.dossier_service import DossierService
from app.repositories.dossier_repository import DossierRepository
from app.core.db import db

dossier_bp = Blueprint('dossier', __name__)

dossier_repo = DossierRepository()
dossier_service = DossierService(dossier_repo)


@dossier_bp.route('/api/v1/dossiers', methods=['POST'])
def create_dossier():
    """Créer un nouveau dossier patient
    ---
    tags:
      - Dossiers
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - patient_id
          properties:
            patient_id:
              type: string
              example: "uuid-du-patient"
            is_medecin:
              type: boolean
              example: false
    responses:
      201:
        description: Dossier créé avec succès
        schema:
          type: object
          properties:
            status:
              type: string
            idDossier:
              type: string
      400:
        description: Erreur de création
    """
    data = request.json
    current_user_id = request.headers.get('User-ID')
    is_medecin = data.get('is_medecin', False)
    try:
        id_dossier = dossier_service.create_dossier(data['patient_id'], current_user_id, is_medecin)
        db.session.commit()
        return jsonify({"status": "success", "idDossier": id_dossier}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@dossier_bp.route('/api/v1/dossiers/evaluated', methods=['GET'])
def get_evaluated_dossiers():
    """Récupérer tous les dossiers évalués
    ---
    tags:
      - Dossiers
    responses:
      200:
        description: Liste des dossiers évalués avec scores de risque
      500:
        description: Erreur serveur
    """
    try:
        data = dossier_service.get_evaluated_dossiers()
        return jsonify({"status": "success", "records": data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@dossier_bp.route('/api/v1/patients/<string:patient_id>/history', methods=['GET'])
def get_patient_history(patient_id):
    """Récupérer l'historique complet des consultations d'un patient
    ---
    tags:
      - Dossiers
    parameters:
      - name: patient_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Historique du patient
      500:
        description: Erreur serveur
    """
    try:
        data = dossier_service.get_patient_history(patient_id)
        return jsonify({"status": "success", "history": data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
