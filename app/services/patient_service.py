from datetime import datetime
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository

from app.core.validation import validate_email_format, validate_cin_format, validate_phone_format


class PatientService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    def _serialize_patient(self, patient: Patient) -> dict:
        return {
            "id": patient.id,
            "cin": patient.cin,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "dateNaissance": str(patient.dateNaissance),
            "age": patient.age,
            "sexe": patient.sexe,
            "email": patient.email,
            "telephone": patient.telephone,
            "adresse": patient.adresse,
        }

    def list_patients(self) -> list[dict]:
        return [self._serialize_patient(patient) for patient in self.patient_repo.list_all()]

    def create_patient(self, data: dict, current_user_id: str) -> str:
        dob = datetime.strptime(data['dateNaissance'], '%Y-%m-%d').date()
        today = datetime.today().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        cin_val = data.get('cin')
        if not cin_val or str(cin_val).strip() == '':
            cin_val = None
        else:
            cin_val = str(cin_val).strip()
            if not validate_cin_format(cin_val):
                raise Exception("Le CIN doit comporter exactement 8 chiffres")

        email_val = self._clean_optional(data.get('email'))
        if email_val and not validate_email_format(email_val):
            raise Exception("Format de l'email incorrect")

        phone_val = self._clean_optional(data.get('telephone'))
        if phone_val and not validate_phone_format(phone_val):
            raise Exception("Le numero de telephone doit comporter 8 chiffres et commencer par 20/21/22/50/51/52/53/90/91/92")

        new_patient = Patient(
            cin=cin_val,
            nom=data['nom'],
            prenom=data['prenom'],
            dateNaissance=dob,
            age=age,
            sexe=data['sexe'],
            email=email_val,
            telephone=phone_val,
            adresse=self._clean_optional(data.get('adresse')),
        )
        patient = self.patient_repo.create(new_patient)
        return str(patient.id)

    def get_patient(self, patient_id: str) -> dict:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise Exception("Patient introuvable")
        return self._serialize_patient(patient)

    def update_patient(self, patient_id: str, data: dict) -> dict:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise Exception("Patient introuvable")

        if 'dateNaissance' in data:
            dob = datetime.strptime(data['dateNaissance'], '%Y-%m-%d').date()
            today = datetime.today().date()
            patient.dateNaissance = dob
            patient.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if 'cin' in data:
            cin_val = data.get('cin')
            if cin_val and str(cin_val).strip():
                cin_val = str(cin_val).strip()
                if not validate_cin_format(cin_val):
                    raise Exception("Le CIN doit comporter exactement 8 chiffres")
                patient.cin = cin_val
            else:
                patient.cin = None
        if 'nom' in data:
            patient.nom = data['nom']
        if 'prenom' in data:
            patient.prenom = data['prenom']
        if 'sexe' in data:
            patient.sexe = data['sexe']
        if 'email' in data:
            email_val = self._clean_optional(data.get('email'))
            if email_val and not validate_email_format(email_val):
                raise Exception("Format de l'email incorrect")
            patient.email = email_val
        if 'telephone' in data:
            phone_val = self._clean_optional(data.get('telephone'))
            if phone_val and not validate_phone_format(phone_val):
                raise Exception("Le numero de telephone doit comporter 8 chiffres et commencer par 20/21/22/50/51/52/53/90/91/92")
            patient.telephone = phone_val
        if 'adresse' in data:
            patient.adresse = self._clean_optional(data.get('adresse'))

        self.patient_repo.update()
        return self._serialize_patient(patient)

    def _clean_optional(self, value):
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def delete_patient(self, patient_id: str) -> None:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise Exception("Patient introuvable")
        self._delete_patient_dependencies(patient_id)
        self.patient_repo.delete(patient)

    def _delete_patient_dependencies(self, patient_id: str) -> None:
        from app.core.db import db
        from app.models.analyses import AnalyseIA, AnalyseSymptomes, EvaluationRisque
        from app.models.donnees_cliniques import DonneesCliniques
        from app.models.dossier_patient import DossierPatient
        from app.models.image_irm import ImageIRM
        from app.models.rapport import Rapport

        dossiers = DossierPatient.query.filter_by(patient_id=patient_id).all()
        for dossier in dossiers:
            dossier_id = dossier.idDossier

            EvaluationRisque.query.filter_by(dossier_id=dossier_id).delete(synchronize_session=False)
            Rapport.query.filter_by(dossier_id=dossier_id).delete(synchronize_session=False)

            images = ImageIRM.query.filter_by(dossier_id=dossier_id).all()
            for image in images:
                AnalyseIA.query.filter_by(image_id=image.idImage).delete(synchronize_session=False)
                db.session.delete(image)

            clinical_entries = DonneesCliniques.query.filter_by(dossier_id=dossier_id).all()
            for entry in clinical_entries:
                AnalyseSymptomes.query.filter_by(donnees_cliniques_id=entry.id).delete(synchronize_session=False)
                db.session.delete(entry)

            db.session.delete(dossier)
        db.session.flush()

    def check_cin(self, cin: str) -> bool:
        if not cin:
            return False
        patient = self.patient_repo.get_by_cin(cin)
        return patient is not None

    def search_patients(self, query: str):
        patients = self.patient_repo.search(query)
        return [self._serialize_patient(p) for p in patients]
