from app.core.db import db
from app.models.user import Utilisateur


class UtilisateurRepository:
    def list_all(self) -> list[Utilisateur]:
        return Utilisateur.query.order_by(Utilisateur.nom.asc()).all()

    def create(self, user: Utilisateur) -> Utilisateur:
        db.session.add(user)
        db.session.commit()
        return user

    def get_by_id(self, user_id: str) -> Utilisateur:
        return Utilisateur.query.get(user_id)

    def get_by_email(self, email: str) -> Utilisateur:
        return Utilisateur.query.filter_by(email=email).first()

    def search(self, query: str) -> list[Utilisateur]:
        search_filter = f"%{query}%"
        return Utilisateur.query.filter(
            (Utilisateur.nom.ilike(search_filter))
            | (Utilisateur.email.ilike(search_filter))
            | (Utilisateur.id.ilike(search_filter))
        ).all()

    def update(self) -> None:
        db.session.commit()

    def delete(self, user: Utilisateur) -> None:
        db.session.delete(user)
        db.session.commit()
