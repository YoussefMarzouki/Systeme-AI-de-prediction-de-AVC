from app.core.db import db
from app.models.donnees_cliniques import DonneesCliniques

class DonneesCliniquesRepository:
    def create(self, donnees: DonneesCliniques) -> DonneesCliniques:
        db.session.add(donnees)
        db.session.commit()
        return donnees
