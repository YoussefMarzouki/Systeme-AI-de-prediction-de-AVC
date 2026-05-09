import bcrypt
from app.core.db import db
from app.models.user import Medecin
from flask_jwt_extended import create_access_token
from app.repositories.utilisateur_repository import UtilisateurRepository


class AuthService:
    def __init__(self, repo: UtilisateurRepository):
        self.repo = repo

    def _check_password(self, user, password: str) -> bool:
        stored_password = user.motDePasse or ""
        is_bcrypt_hash = stored_password.startswith(("$2a$", "$2b$", "$2y$"))

        if is_bcrypt_hash:
            return bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))

        # Compatibility with old seeded accounts stored in plain text.
        if stored_password == password:
            user.motDePasse = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            db.session.commit()
            return True

        return False

    def _serialize_user(self, user) -> dict:
        data = {
            "id": user.id,
            "nom": user.nom,
            "email": user.email,
            "type": user.type,
            "etat": user.etat,
        }
        if isinstance(user, Medecin):
            data["specialiste"] = bool(user.specialiste)
        return data

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user:
            raise Exception("Email ou mot de passe incorrect")

        if user.etat != "actif":
            raise Exception("Compte desactive. Contactez l'administrateur")

        if not self._check_password(user, password):
            raise Exception("Email ou mot de passe incorrect")

        user_data = self._serialize_user(user)
        token = create_access_token(
            identity=user.id,
            additional_claims=user_data,
        )

        return {
            "token": token,
            "user": user_data,
        }
