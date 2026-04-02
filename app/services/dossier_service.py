from app.models.dossier_patient import DossierPatient
from app.models.donnees_cliniques import DonneesCliniques
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
