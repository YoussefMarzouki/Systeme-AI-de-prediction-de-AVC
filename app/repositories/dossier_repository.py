from app.core.db import db
from app.models.dossier_patient import DossierPatient

class DossierRepository:
    def list_all(self) -> list[DossierPatient]:
        return DossierPatient.query.order_by(DossierPatient.dateCreation.desc()).all()

    def create(self, dossier: DossierPatient) -> DossierPatient:
        db.session.add(dossier)
        db.session.commit()
        return dossier

    def get_by_id(self, dossier_id: str) -> DossierPatient:
        return DossierPatient.query.get(dossier_id)

    def update(self) -> None:
        db.session.commit()

    def delete(self, dossier: DossierPatient) -> None:
        db.session.delete(dossier)
        db.session.commit()
