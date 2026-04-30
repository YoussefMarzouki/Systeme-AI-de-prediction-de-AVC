from datetime import datetime
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository

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
            "sexe": patient.sexe
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

        new_patient = Patient(
            cin=cin_val,
            nom=data['nom'],
            prenom=data['prenom'],
            dateNaissance=dob,
            age=age,
            sexe=data['sexe']
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
            patient.cin = cin_val if cin_val and str(cin_val).strip() else None
        if 'nom' in data:
            patient.nom = data['nom']
        if 'prenom' in data:
            patient.prenom = data['prenom']
        if 'sexe' in data:
            patient.sexe = data['sexe']

        self.patient_repo.update()
        return self._serialize_patient(patient)

    def delete_patient(self, patient_id: str) -> None:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise Exception("Patient introuvable")
        self.patient_repo.delete(patient)

    def check_cin(self, cin: str) -> bool:
        if not cin:
            return False
        patient = self.patient_repo.get_by_cin(cin)
        return patient is not None

    def search_patients(self, query: str):
        patients = self.patient_repo.search(query)
        return [self._serialize_patient(p) for p in patients]
