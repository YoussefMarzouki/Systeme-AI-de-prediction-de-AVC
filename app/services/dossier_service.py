from app.models.dossier_patient import DossierPatient
from app.models.donnees_cliniques import DonneesCliniques
from app.models.analyses import AnalyseIA, EvaluationRisque
from app.models.patient import Patient
from app.core.db import db
from app.repositories.dossier_repository import DossierRepository
from datetime import date
import json

class DossierService:
    def __init__(self, dossier_repo: DossierRepository):
        self.dossier_repo = dossier_repo

    def _serialize_dossier(self, dossier: DossierPatient) -> dict:
        return {
            "idDossier": dossier.idDossier,
            "dateCreation": str(dossier.dateCreation) if dossier.dateCreation else None,
            "statut": dossier.statut,
            "patient_id": dossier.patient_id,
            "agent_id": dossier.agent_id,
            "medecin_id": dossier.medecin_id,
        }

    def list_dossiers(self) -> list[dict]:
        return [self._serialize_dossier(dossier) for dossier in self.dossier_repo.list_all()]

    def create_dossier(self, patient_id: str, creator_id: str, is_medecin: bool) -> str:
        new_dossier = DossierPatient(
            patient_id=patient_id,
            agent_id=creator_id if not is_medecin else None,
            medecin_id=creator_id if is_medecin else None
        )
        dossier = self.dossier_repo.create(new_dossier)
        return str(dossier.idDossier)

    def get_dossier(self, dossier_id: str) -> dict:
        dossier = self.dossier_repo.get_by_id(dossier_id)
        if not dossier:
            raise Exception("Dossier introuvable")
        return self._serialize_dossier(dossier)

    def update_dossier(self, dossier_id: str, data: dict) -> dict:
        dossier = self.dossier_repo.get_by_id(dossier_id)
        if not dossier:
            raise Exception("Dossier introuvable")

        if 'statut' in data:
            dossier.statut = data['statut']
        if 'patient_id' in data:
            dossier.patient_id = data['patient_id']
        if 'agent_id' in data:
            dossier.agent_id = data['agent_id']
        if 'medecin_id' in data:
            dossier.medecin_id = data['medecin_id']

        self.dossier_repo.update()
        return self._serialize_dossier(dossier)

    def delete_dossier(self, dossier_id: str) -> None:
        dossier = self.dossier_repo.get_by_id(dossier_id)
        if not dossier:
            raise Exception("Dossier introuvable")
        self.dossier_repo.delete(dossier)

    def get_evaluated_dossiers(self) -> list:
        from app.models.rapport import Rapport
        from app.models.image_irm import ImageIRM
        from app.models.donnees_cliniques import DonneesCliniques

        results = db.session.query(DossierPatient, Patient).join(
            Patient, DossierPatient.patient_id == Patient.id
        ).order_by(DossierPatient.dateCreation.desc()).all()

        # Add any patients without a dossier as an "empty" row so they show up for intake
        patients_with_dossier = set(dossier.patient_id for dossier, p in results)
        patients_without_dossier = Patient.query.filter(
            ~Patient.id.in_(patients_with_dossier) if patients_with_dossier else True
        ).all()

        evaluated_list = []
        
        # Add patients that have dossiers
        for dossier, patient in results:
            rapport = self._latest_visible_rapport(dossier.idDossier)
            modifier_id = rapport.modifie_par_id if rapport else None
            modifier_name = None
            if modifier_id:
                from app.models.user import Utilisateur
                u = Utilisateur.query.get(modifier_id)
                modifier_name = u.nom if u else modifier_id

            statut_rapport = rapport.statut if rapport else 'NO_REPORT'
            prediction_data = rapport.contenu if rapport else None
            prediction_content = self._content_dict(prediction_data)

            image = ImageIRM.query.filter_by(dossier_id=dossier.idDossier).order_by(ImageIRM.dateAcquisition.desc()).first()
            image_url = image.cheminStockage if image else None

            donnees = DonneesCliniques.query.filter_by(dossier_id=dossier.idDossier).order_by(DonneesCliniques.dateSaisie.desc()).first()
            tension = donnees.tension if donnees else None
            # Important: use an empty array if no symptom notes exist, and an array with just notes string if it exists
            symptoms_array = []
            if donnees and donnees.notes:
                symptoms_array = [donnees.notes]

            eval_risque = self._latest_evaluation_for_dossier(dossier.idDossier)
            risk_level = prediction_content.get('risk_level') or (eval_risque.niveau if eval_risque else 'UNKNOWN')
            fused_probability = self._first_number(
                prediction_content.get('fused_probability'),
                prediction_content.get('probability'),
                eval_risque.scoreGlobal if eval_risque else None
            )
            
            # Determine correct status
            current_status = dossier.statut
            if current_status == "OUVERT" and donnees and not image_url:
                current_status = "PENDING_MRI"

            evaluated_list.append({
                "patient_id": patient.id,
                "patient_name": f"{patient.nom} {patient.prenom}",
                "patient_cin": patient.cin,
                "patient_age": self._patient_age(patient),
                "patient_email": patient.email,
                "patient_telephone": patient.telephone,
                "dossier_status": current_status,
                "risk_level": risk_level,
                "fused_probability": fused_probability,
                "date": str(dossier.dateCreation.date()),
                "dossier_id": dossier.idDossier,
                "modifie_par_id": modifier_id,
                "modifie_par_name": modifier_name,
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
                "patient_age": self._patient_age(patient),
                "patient_email": patient.email,
                "patient_telephone": patient.telephone,
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
            rapport = self._latest_visible_rapport(dossier.idDossier)
            rapport_versions = (
                Rapport.query.filter_by(dossier_id=dossier.idDossier)
                .order_by(Rapport.dateGeneration.asc(), Rapport.dateModification.asc())
                .all()
            )
            rapport_content = self._content_dict(rapport.contenu if rapport else None)
            eval_risque = self._latest_evaluation_for_dossier(dossier.idDossier)
            risk_level = rapport_content.get('risk_level') or (eval_risque.niveau if eval_risque else None)
            fused_probability = self._first_number(
                rapport_content.get('fused_probability'),
                rapport_content.get('probability'),
                eval_risque.scoreGlobal if eval_risque else None
            )
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

            version_items = []
            for index, version in enumerate(rapport_versions, start=1):
                version_content = self._content_dict(version.contenu)
                modifier_name = None
                if version.modifie_par_id:
                    modifier = Utilisateur.query.get(version.modifie_par_id)
                    modifier_name = modifier.nom if modifier else version.modifie_par_id

                version_items.append({
                    "id": version.idRapport,
                    "statut": version.statut,
                    "version_number": version_content.get("version_number") or index,
                    "version_type": version_content.get("version_type") or ("SPECIALIST_REVIEW" if version.modifie_par_id else "ORIGINAL_AI"),
                    "previous_rapport_id": version_content.get("previous_rapport_id"),
                    "dateGeneration": str(version.dateGeneration) if version.dateGeneration else None,
                    "dateModification": str(version.dateModification) if version.dateModification else None,
                    "modifie_par": modifier_name,
                    "contenu": version.contenu,
                    "is_current": rapport.idRapport == version.idRapport if rapport else False,
                })

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
                "risk_level": risk_level,
                "fused_probability": fused_probability,
                "rapport": rapport_info,
                "rapport_versions": version_items,
                "clinical_data": clinical_entries,
                "image_urls": image_urls,
            })

        return {
            "patient_id": patient.id,
            "patient_name": f"{patient.nom} {patient.prenom}",
            "patient_cin": patient.cin,
            "patient_age": self._patient_age(patient),
            "patient_email": patient.email,
            "patient_telephone": patient.telephone,
            "patient_sexe": patient.sexe,
            "total_consultations": len(history),
            "consultations": history,
        }

    def _patient_age(self, patient: Patient):
        if patient.age is not None:
            return patient.age

        dob = patient.dateNaissance
        if not dob:
            return None

        if isinstance(dob, str):
            try:
                dob = date.fromisoformat(dob[:10])
            except ValueError:
                return None

        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _latest_evaluation_for_dossier(self, dossier_id: str):
        return db.session.query(EvaluationRisque).outerjoin(
            AnalyseIA, EvaluationRisque.analyse_ia_id == AnalyseIA.idAnalyse
        ).filter(
            EvaluationRisque.dossier_id == dossier_id
        ).order_by(
            AnalyseIA.dateAnalyse.desc().nullslast()
        ).first()

    def _latest_visible_rapport(self, dossier_id: str):
        from app.models.rapport import Rapport

        reviewed = (
            Rapport.query.filter(
                Rapport.dossier_id == dossier_id,
                Rapport.statut != "UNVALIDATED",
            )
            .order_by(Rapport.dateGeneration.desc(), Rapport.dateModification.desc())
            .first()
        )
        if reviewed:
            return reviewed

        return (
            Rapport.query.filter_by(dossier_id=dossier_id)
            .order_by(Rapport.dateGeneration.desc(), Rapport.dateModification.desc())
            .first()
        )

    def _content_dict(self, content):
        if isinstance(content, dict):
            return content
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    def _first_number(self, *values):
        for value in values:
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None
