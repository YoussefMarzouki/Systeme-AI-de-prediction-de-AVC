from app.models.donnees_cliniques import DonneesCliniques
from app.models.dossier_patient import DossierPatient
from app.repositories.donnees_cliniques_repository import DonneesCliniquesRepository
from app.repositories.dossier_repository import DossierRepository

class DonneesCliniquesService:
    def __init__(self, donnees_repo: DonneesCliniquesRepository, dossier_repo: DossierRepository):
        self.donnees_repo = donnees_repo
        self.dossier_repo = dossier_repo

    def _serialize_donnees(self, donnees: DonneesCliniques) -> dict:
        return {
            "id": donnees.id,
            "dateSaisie": str(donnees.dateSaisie) if donnees.dateSaisie else None,
            "fast": donnees.fast,
            "tension": donnees.tension,
            "age": donnees.age,
            "notes": donnees.notes,
            "dossier_id": donnees.dossier_id
        }

    def list_donnees_cliniques(self) -> list[dict]:
        return [self._serialize_donnees(entry) for entry in self.donnees_repo.list_all()]

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
        return [self._serialize_donnees(e) for e in entries]

    def get_donnees_cliniques(self, donnees_id: str) -> dict:
        donnees = self.donnees_repo.get_by_id(donnees_id)
        if not donnees:
            raise Exception("Donnees cliniques introuvables")
        return self._serialize_donnees(donnees)

    def update_donnees_cliniques(self, donnees_id: str, data: dict) -> dict:
        donnees = self.donnees_repo.get_by_id(donnees_id)
        if not donnees:
            raise Exception("Donnees cliniques introuvables")

        if 'fast' in data:
            donnees.fast = data['fast']
        if 'tension' in data:
            donnees.tension = data['tension']
        if 'age' in data:
            donnees.age = data['age']
        if 'notes' in data:
            donnees.notes = data['notes']
        if 'dossier_id' in data:
            dossier = self.dossier_repo.get_by_id(data['dossier_id'])
            if not dossier:
                raise Exception(f"Dossier {data['dossier_id']} introuvable")
            donnees.dossier_id = data['dossier_id']

        self.donnees_repo.update()
        return self._serialize_donnees(donnees)

    def delete_donnees_cliniques(self, donnees_id: str) -> None:
        donnees = self.donnees_repo.get_by_id(donnees_id)
        if not donnees:
            raise Exception("Donnees cliniques introuvables")
        self.donnees_repo.delete(donnees)
