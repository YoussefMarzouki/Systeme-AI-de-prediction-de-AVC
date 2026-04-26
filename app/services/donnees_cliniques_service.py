from app.models.donnees_cliniques import DonneesCliniques
from app.models.dossier_patient import DossierPatient
from app.repositories.donnees_cliniques_repository import DonneesCliniquesRepository
from app.repositories.dossier_repository import DossierRepository

class DonneesCliniquesService:
    def __init__(self, donnees_repo: DonneesCliniquesRepository, dossier_repo: DossierRepository):
        self.donnees_repo = donnees_repo
        self.dossier_repo = dossier_repo

    def add_donnees_cliniques(self, dossier_id: str, data: dict) -> str:
        """Add clinical data (FAST score, tension, notes) to an existing dossier."""
        dossier = self.dossier_repo.get_by_id(dossier_id)
        if not dossier:
            raise Exception(f"Dossier {dossier_id} introuvable")

        donnees = DonneesCliniques(
            dossier_id=dossier_id,
            fast=data.get('fast'),
            tension=data.get('tension'),
            age=data.get('age'),
            notes=data.get('notes')
        )
        saved = self.donnees_repo.create(donnees)
        return str(saved.id)

    def get_by_dossier(self, dossier_id: str) -> list:
        """Retrieve all clinical data records for a dossier."""
        entries = self.donnees_repo.get_by_dossier(dossier_id)
        return [{
            "id": e.id,
            "dateSaisie": str(e.dateSaisie) if e.dateSaisie else None,
            "fast": e.fast,
            "tension": e.tension,
            "age": e.age,
            "notes": e.notes,
            "dossier_id": e.dossier_id
        } for e in entries]
