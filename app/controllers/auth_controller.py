from flask import Blueprint, request, jsonify
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

auth_repo = UtilisateurRepository()
auth_service = AuthService(auth_repo)


@auth_bp.route("/api/v1/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "")
    password = data.get("motDePasse", "")

    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400

    try:
        result = auth_service.login(email, password)
        return jsonify({"status": "success", **result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401
