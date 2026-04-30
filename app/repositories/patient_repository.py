from app.core.db import db
from app.models.patient import Patient

class PatientRepository:
    def list_all(self) -> list[Patient]:
        return Patient.query.order_by(Patient.nom.asc(), Patient.prenom.asc()).all()

    def create(self, patient: Patient) -> Patient:
        db.session.add(patient)
        db.session.commit()
        return patient

    def get_by_id(self, patient_id: str) -> Patient:
        return Patient.query.get(patient_id)

    def get_by_cin(self, cin: str) -> Patient:
        return Patient.query.filter_by(cin=cin).first()

    def search(self, query: str):
        search_filter = f"%{query}%"
        return Patient.query.filter(
            (Patient.nom.ilike(search_filter)) | 
            (Patient.prenom.ilike(search_filter)) |
            (Patient.cin.ilike(search_filter)) |
            (Patient.id.ilike(search_filter))
        ).all()

    def update(self) -> None:
        db.session.commit()

    def delete(self, patient: Patient) -> None:
        db.session.delete(patient)
        db.session.commit()
