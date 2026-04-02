from app.core.db import db
from app.models.dossier_patient import DossierPatient

class DossierRepository:
    def create(self, dossier: DossierPatient) -> DossierPatient:
        db.session.add(dossier)
        db.session.commit()
        return dossier

    def get_by_id(self, dossier_id: str) -> DossierPatient:
        return DossierPatient.query.get(dossier_id)
