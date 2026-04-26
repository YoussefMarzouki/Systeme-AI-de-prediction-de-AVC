from app.core.db import db
from app.models.donnees_cliniques import DonneesCliniques

class DonneesCliniquesRepository:
    def create(self, donnees: DonneesCliniques) -> DonneesCliniques:
        db.session.add(donnees)
        db.session.commit()
        return donnees

    def get_by_dossier(self, dossier_id: str) -> list:
        return DonneesCliniques.query.filter_by(dossier_id=dossier_id)\
            .order_by(DonneesCliniques.dateSaisie.desc()).all()

    def get_latest_by_dossier(self, dossier_id: str) -> DonneesCliniques:
        return DonneesCliniques.query.filter_by(dossier_id=dossier_id)\
            .order_by(DonneesCliniques.dateSaisie.desc()).first()
