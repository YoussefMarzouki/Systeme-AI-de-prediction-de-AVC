from datetime import datetime
from app.models.patient import Patient
from app.models.dossier_patient import DossierPatient
from app.models.donnees_cliniques import DonneesCliniques
from app.repositories.patient_repository import PatientRepository
from app.core.db import db
import json

class PatientService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    def create_patient(self, data: dict, current_user_id: str) -> str:
        # Assuming date string 'YYYY-MM-DD'
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

    def _get_or_create_dossier(self, patient_id: str):
        # Chercher le dossier le plus récent
        dossier = db.session.query(DossierPatient).filter_by(patient_id=patient_id).order_by(DossierPatient.dateCreation.desc()).first()
        if not dossier:
            dossier = DossierPatient(patient_id=patient_id)
            db.session.add(dossier)
            db.session.flush() # assigned ID
        return dossier

    def add_clinical_info(self, patient_id: str, data: dict) -> str:
        dossier = self._get_or_create_dossier(patient_id)
        
        donnees = DonneesCliniques(
            dossier_id=dossier.idDossier,
            fast=data.get('fast'),
            tension=data.get('tension'),
            age=data.get('age'),
            notes=data.get('notes')
        )
        db.session.add(donnees)
        db.session.flush()
        return donnees.id

    def add_symptoms(self, patient_id: str, data: dict) -> str:
        # data is expected to contain a 'symptoms' key with a list of symptoms, or just a list directly
        symptoms_list = data.get('symptoms', [])
        notes = "Symptoms: " + json.dumps(symptoms_list)
        
        dossier = self._get_or_create_dossier(patient_id)
        donnees = DonneesCliniques(
            dossier_id=dossier.idDossier,
            notes=notes
        )
        db.session.add(donnees)
        db.session.flush()
        return donnees.id

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
