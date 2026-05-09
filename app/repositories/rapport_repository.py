from app.models.rapport import Rapport
from app.core.db import db


class RapportRepository:
    def list_all(self) -> list[Rapport]:
        return Rapport.query.order_by(Rapport.dateGeneration.desc()).all()

    def create(self, rapport: Rapport) -> Rapport:
        db.session.add(rapport)
        db.session.commit()
        return rapport

    def get_by_id(self, rapport_id: str) -> Rapport:
        return Rapport.query.get(rapport_id)

    def get_by_dossier(self, dossier_id: str) -> Rapport:
        return Rapport.query.filter_by(dossier_id=dossier_id).order_by(Rapport.dateGeneration.desc()).first()

    def get_pending_by_dossier(self, dossier_id: str, statuses: list[str]) -> Rapport:
        return (
            Rapport.query.filter(
                Rapport.dossier_id == dossier_id,
                Rapport.statut.in_(statuses),
            )
            .order_by(Rapport.dateGeneration.desc())
            .first()
        )

    def list_by_dossier_ids(self, dossier_ids: list[str]) -> list[Rapport]:
        if not dossier_ids:
            return []
        return Rapport.query.filter(Rapport.dossier_id.in_(dossier_ids)).order_by(Rapport.dateGeneration.desc()).all()

    def list_by_statuses(self, statuses: list[str]):
        return Rapport.query.filter(Rapport.statut.in_(statuses)).order_by(Rapport.dateGeneration.desc()).all()

    def update(self) -> None:
        db.session.commit()

    def delete(self, rapport: Rapport) -> None:
        db.session.delete(rapport)
        db.session.commit()
