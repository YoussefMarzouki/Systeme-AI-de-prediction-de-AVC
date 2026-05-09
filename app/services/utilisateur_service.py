import bcrypt
from app.models.user import Utilisateur, Medecin, AgentAccueil, Admin
from app.repositories.utilisateur_repository import UtilisateurRepository


TYPE_MAP = {
    "medecin": Medecin,
    "agent_accueil": AgentAccueil,
    "admin": Admin,
}


class UtilisateurService:
    def __init__(self, repo: UtilisateurRepository):
        self.repo = repo

    def _serialize(self, user: Utilisateur) -> dict:
        data = {
            "id": user.id,
            "nom": user.nom,
            "email": user.email,
            "etat": user.etat,
            "type": user.type,
        }
        if isinstance(user, Medecin):
            data["specialiste"] = user.specialiste
        return data

    def list_utilisateurs(self) -> list[dict]:
        return [self._serialize(u) for u in self.repo.list_all()]

    def get_utilisateur(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("Utilisateur introuvable")
        return self._serialize(user)

    def create_utilisateur(self, data: dict) -> str:
        if self.repo.get_by_email(data["email"]):
            raise Exception("Un utilisateur avec cet email existe deja")

        user_type = data.get("type", "medecin")
        cls = TYPE_MAP.get(user_type, Utilisateur)

        hashed = bcrypt.hashpw(
            data["motDePasse"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user = cls(
            nom=data["nom"],
            email=data["email"],
            motDePasse=hashed,
            etat=data.get("etat", "actif"),
        )
        if isinstance(user, Medecin) and "specialiste" in data:
            user.specialiste = data["specialiste"]

        saved = self.repo.create(user)
        return saved.id

    def update_utilisateur(self, user_id: str, data: dict) -> dict:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("Utilisateur introuvable")

        if "nom" in data:
            user.nom = data["nom"]
        if "email" in data:
            existing = self.repo.get_by_email(data["email"])
            if existing and existing.id != user_id:
                raise Exception("Cet email est deja utilise")
            user.email = data["email"]
        if "etat" in data:
            user.etat = data["etat"]
        if "motDePasse" in data and data["motDePasse"]:
            user.motDePasse = bcrypt.hashpw(
                data["motDePasse"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        if isinstance(user, Medecin) and "specialiste" in data:
            user.specialiste = data["specialiste"]

        self.repo.update()
        return self._serialize(user)

    def delete_utilisateur(self, user_id: str) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("Utilisateur introuvable")
        self.repo.delete(user)

    def search_utilisateurs(self, query: str) -> list[dict]:
        return [self._serialize(u) for u in self.repo.search(query)]
