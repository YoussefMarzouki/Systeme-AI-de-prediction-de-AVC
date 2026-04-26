from datetime import datetime
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository

class PatientService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

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
        return {
            "id": patient.id,
            "cin": patient.cin,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "dateNaissance": str(patient.dateNaissance),
            "age": patient.age,
            "sexe": patient.sexe
        }

    def check_cin(self, cin: str) -> bool:
        if not cin:
            return False
        patient = self.patient_repo.get_by_cin(cin)
        return patient is not None

    def search_patients(self, query: str):
        patients = self.patient_repo.search(query)
        return [{
            "id": p.id,
            "cin": p.cin,
            "nom": p.nom,
            "prenom": p.prenom,
            "dateNaissance": str(p.dateNaissance),
            "age": p.age,
            "sexe": p.sexe
        } for p in patients]
