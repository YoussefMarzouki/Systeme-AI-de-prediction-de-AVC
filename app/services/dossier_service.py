from app.models.dossier_patient import DossierPatient
from app.models.donnees_cliniques import DonneesCliniques
from app.models.analyses import EvaluationRisque
from app.models.patient import Patient
from app.core.db import db
from app.repositories.dossier_repository import DossierRepository

class DossierService:
    def __init__(self, dossier_repo: DossierRepository):
        self.dossier_repo = dossier_repo

    def create_dossier(self, patient_id: str, creator_id: str, is_medecin: bool) -> str:
        new_dossier = DossierPatient(
            patient_id=patient_id,
            agent_id=creator_id if not is_medecin else None,
            medecin_id=creator_id if is_medecin else None
        )
        dossier = self.dossier_repo.create(new_dossier)
        return str(dossier.idDossier)

    def get_evaluated_dossiers(self) -> list:
        from app.models.rapport import Rapport
        from app.models.image_irm import ImageIRM
        from app.models.donnees_cliniques import DonneesCliniques

        results = db.session.query(DossierPatient, Patient, EvaluationRisque).join(
            Patient, DossierPatient.patient_id == Patient.id
        ).outerjoin(
            EvaluationRisque, DossierPatient.idDossier == EvaluationRisque.dossier_id
        ).order_by(DossierPatient.dateCreation.desc()).all()

        # Add any patients without a dossier as an "empty" row so they show up for intake
        patients_with_dossier = set(dossier.patient_id for dossier, p, er in results)
        patients_without_dossier = Patient.query.filter(
            ~Patient.id.in_(patients_with_dossier) if patients_with_dossier else True
        ).all()

        evaluated_list = []
        
        # Add patients that have dossiers
        for dossier, patient, eval_risque in results:
            rapport = Rapport.query.filter_by(dossier_id=dossier.idDossier).first()
            modifier = rapport.modifie_par_id if rapport else None
            statut_rapport = rapport.statut if rapport else 'NO_REPORT'
            prediction_data = rapport.contenu if rapport else None

            image = ImageIRM.query.filter_by(dossier_id=dossier.idDossier).order_by(ImageIRM.dateAcquisition.desc()).first()
            image_url = image.cheminStockage if image else None

            donnees = DonneesCliniques.query.filter_by(dossier_id=dossier.idDossier).order_by(DonneesCliniques.dateSaisie.desc()).first()
            tension = donnees.tension if donnees else None
            # Important: use an empty array if no symptom notes exist, and an array with just notes string if it exists
            symptoms_array = []
            if donnees and donnees.notes:
                symptoms_array = [donnees.notes]

            risk_level = eval_risque.niveau if eval_risque else 'UNKNOWN'
            
            # Determine correct status
            current_status = dossier.statut
            if current_status == "OUVERT" and donnees and not image_url:
                current_status = "PENDING_MRI"

            evaluated_list.append({
                "patient_id": patient.id,
                "patient_name": f"{patient.nom} {patient.prenom}",
                "patient_cin": patient.cin,
                "dossier_status": current_status,
                "risk_level": risk_level,
                "fused_probability": eval_risque.scoreGlobal if eval_risque else None,
                "date": str(dossier.dateCreation.date()),
                "dossier_id": dossier.idDossier,
                "modifie_par_id": modifier,
                "statut_rapport": statut_rapport,
                "prediction_data": prediction_data,
                "imageUrl": image_url,
                "tension": tension,
                "symptoms": symptoms_array
            })

        # Add patients without any dossier yet
        for patient in patients_without_dossier:
            evaluated_list.append({
                "patient_id": patient.id,
                "patient_name": f"{patient.nom} {patient.prenom}",
                "patient_cin": patient.cin,
                "dossier_status": "NO_DOSSIER",
                "risk_level": "UNKNOWN",
                "fused_probability": None,
                "date": "N/A",
                "dossier_id": None,
                "modifie_par_id": None,
                "statut_rapport": "NO_REPORT",
                "prediction_data": None,
                "imageUrl": None,
                "tension": None,
                "symptoms": []
            })
            
        return evaluated_list

    def get_patient_history(self, patient_id: str) -> list:
        """Get the full consultation history for a patient, ordered chronologically."""
        from app.models.rapport import Rapport
        from app.models.image_irm import ImageIRM
        from app.models.analyses import AnalyseIA, AnalyseSymptomes
        from app.models.user import Utilisateur

        patient = Patient.query.get(patient_id)
        if not patient:
            raise Exception("Patient introuvable")

        dossiers = DossierPatient.query.filter_by(patient_id=patient_id)\
            .order_by(DossierPatient.dateCreation.desc()).all()

        history = []
        for dossier in dossiers:
            eval_risque = EvaluationRisque.query.filter_by(dossier_id=dossier.idDossier).first()

            rapport = Rapport.query.filter_by(dossier_id=dossier.idDossier).first()
            rapport_info = None
            if rapport:
                modifier_name = None
                if rapport.modifie_par_id:
                    modifier = Utilisateur.query.get(rapport.modifie_par_id)
                    modifier_name = modifier.nom if modifier else rapport.modifie_par_id
                rapport_info = {
                    "id": rapport.idRapport,
                    "statut": rapport.statut,
                    "dateGeneration": str(rapport.dateGeneration) if rapport.dateGeneration else None,
                    "dateModification": str(rapport.dateModification) if rapport.dateModification else None,
                    "modifie_par": modifier_name,
                    "contenu": rapport.contenu
                }

            donnees_list = DonneesCliniques.query.filter_by(dossier_id=dossier.idDossier)\
                .order_by(DonneesCliniques.dateSaisie.desc()).all()
            clinical_entries = [{
                "date": str(d.dateSaisie) if d.dateSaisie else None,
                "fast": d.fast,
                "tension": d.tension,
                "notes": d.notes,
            } for d in donnees_list]

            images = ImageIRM.query.filter_by(dossier_id=dossier.idDossier)\
                .order_by(ImageIRM.dateAcquisition.desc()).all()
            image_urls = [img.cheminStockage for img in images if img.cheminStockage]

            created_by = None
            if dossier.medecin_id:
                u = Utilisateur.query.get(dossier.medecin_id)
                created_by = u.nom if u else dossier.medecin_id
            elif dossier.agent_id:
                u = Utilisateur.query.get(dossier.agent_id)
                created_by = u.nom if u else dossier.agent_id

            history.append({
                "dossier_id": dossier.idDossier,
                "dateCreation": str(dossier.dateCreation) if dossier.dateCreation else None,
                "statut": dossier.statut,
                "created_by": created_by,
                "risk_level": eval_risque.niveau if eval_risque else None,
                "fused_probability": eval_risque.scoreGlobal if eval_risque else None,
                "rapport": rapport_info,
                "clinical_data": clinical_entries,
                "image_urls": image_urls,
            })

        return {
            "patient_id": patient.id,
            "patient_name": f"{patient.nom} {patient.prenom}",
            "patient_cin": patient.cin,
            "patient_age": patient.age,
            "patient_sexe": patient.sexe,
            "total_consultations": len(history),
            "consultations": history,
        }
