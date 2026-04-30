from app.core.db import db
from app.models.donnees_cliniques import DonneesCliniques

class DonneesCliniquesRepository:
    def list_all(self) -> list[DonneesCliniques]:
        return DonneesCliniques.query.order_by(DonneesCliniques.dateSaisie.desc()).all()

    def create(self, donnees: DonneesCliniques) -> DonneesCliniques:
        db.session.add(donnees)
        db.session.commit()
        return donnees

    def get_by_id(self, donnees_id: str) -> DonneesCliniques:
        return DonneesCliniques.query.get(donnees_id)

    def get_by_dossier(self, dossier_id: str) -> list:
        return DonneesCliniques.query.filter_by(dossier_id=dossier_id)\
            .order_by(DonneesCliniques.dateSaisie.desc()).all()

    def get_latest_by_dossier(self, dossier_id: str) -> DonneesCliniques:
        return DonneesCliniques.query.filter_by(dossier_id=dossier_id)\
            .order_by(DonneesCliniques.dateSaisie.desc()).first()

    def update(self) -> None:
        db.session.commit()

    def delete(self, donnees: DonneesCliniques) -> None:
        db.session.delete(donnees)
        db.session.commit()
