from app.models.dossier_patient import DossierPatient
from app.models.donnees_cliniques import DonneesCliniques
from app.models.analyses import EvaluationRisque
from app.models.patient import Patient
from app.core.db import db
from app.repositories.dossier_repository import DossierRepository
from app.repositories.donnees_cliniques_repository import DonneesCliniquesRepository

class DossierService:
    def __init__(self, dossier_repo: DossierRepository, donnees_repo: DonneesCliniquesRepository):
        self.dossier_repo = dossier_repo
        self.donnees_repo = donnees_repo

    def create_dossier(self, patient_id: str, creator_id: str, is_medecin: bool) -> str:
        new_dossier = DossierPatient(
            patient_id=patient_id,
            agent_id=creator_id if not is_medecin else None,
            medecin_id=creator_id if is_medecin else None
        )
        dossier = self.dossier_repo.create(new_dossier)
        return str(dossier.idDossier)

    def add_donnees_cliniques(self, dossier_id: str, data: dict) -> str:
        # Implicit check if dossier exists
        self.dossier_repo.get_by_id(dossier_id)
        
        donnees = DonneesCliniques(
            dossier_id=dossier_id,
            fast=data.get('fast'),
            tension=data.get('tension'),
            age=data.get('age'),
            notes=data.get('notes')
        )
        saved_donnees = self.donnees_repo.create(donnees)
        return str(saved_donnees.id)

    def get_evaluated_dossiers(self) -> list:
        from app.models.rapport import Rapport
        from app.models.image_irm import ImageIRM
        from app.models.donnees_cliniques import DonneesCliniques
        
        results = db.session.query(DossierPatient, Patient, EvaluationRisque).join(
            Patient, DossierPatient.patient_id == Patient.id
        ).join(
            EvaluationRisque, DossierPatient.idDossier == EvaluationRisque.dossier_id
        ).order_by(EvaluationRisque.id.desc()).all()
        
        evaluated_list = []
        for dossier, patient, eval_risque in results:
            
            # To fetch modification data for the new dashboard additions
            rapport = Rapport.query.filter_by(dossier_id=dossier.idDossier).first()
            modifier = rapport.modifie_par_id if rapport else None
            statut_rapport = rapport.statut if rapport else 'NO_REPORT'
            prediction_data = rapport.contenu if rapport else None
            
            image = ImageIRM.query.filter_by(dossier_id=dossier.idDossier).order_by(ImageIRM.dateAcquisition.desc()).first()
            image_url = image.cheminStockage if image else None
            
            donnees = DonneesCliniques.query.filter_by(dossier_id=dossier.idDossier).order_by(DonneesCliniques.dateSaisie.desc()).first()
            tension = donnees.tension if donnees else None
            symptoms = [donnees.notes] if donnees and donnees.notes else ['Historically Logged Assessment']

            evaluated_list.append({
                "patient_id": patient.id,
                "patient_name": f"{patient.nom} {patient.prenom}",
                "patient_cin": patient.cin,
                "dossier_status": dossier.statut,
                "risk_level": eval_risque.niveau,
                "fused_probability": eval_risque.scoreGlobal,
                "date": str(dossier.dateCreation.date()),
                "dossier_id": dossier.idDossier,
                "modifie_par_id": modifier,
                "statut_rapport": statut_rapport,
                "prediction_data": prediction_data,
                "imageUrl": image_url,
                "tension": tension,
                "symptoms": symptoms
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
            # Evaluation
            eval_risque = EvaluationRisque.query.filter_by(dossier_id=dossier.idDossier).first()

            # Rapport + modification tracking
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
                }

            # Clinical data
            donnees_list = DonneesCliniques.query.filter_by(dossier_id=dossier.idDossier)\
                .order_by(DonneesCliniques.dateSaisie.desc()).all()
            clinical_entries = []
            for d in donnees_list:
                clinical_entries.append({
                    "date": str(d.dateSaisie) if d.dateSaisie else None,
                    "fast": d.fast,
                    "tension": d.tension,
                    "notes": d.notes,
                })

            # Images
            images = ImageIRM.query.filter_by(dossier_id=dossier.idDossier)\
                .order_by(ImageIRM.dateAcquisition.desc()).all()
            image_urls = [img.cheminStockage for img in images if img.cheminStockage]

            # Agent / Medecin who created the dossier
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
