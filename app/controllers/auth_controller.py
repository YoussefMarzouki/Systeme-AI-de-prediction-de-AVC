from flask import Blueprint, request, jsonify
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

auth_repo = UtilisateurRepository()
auth_service = AuthService(auth_repo)


@auth_bp.route("/api/v1/auth/login", methods=["POST"])
def login():
    """Authentifier un utilisateur et obtenir un token JWT
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - motDePasse
          properties:
            email:
              type: string
              example: "admin@hopital.tn"
            motDePasse:
              type: string
              example: "password123"
    responses:
      200:
        description: Authentification réussie
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            token:
              type: string
              example: "jwt.token.here"
            role:
              type: string
              example: "admin"
            id:
              type: string
              example: "uuid"
      400:
        description: Données requises manquantes
      401:
        description: Identifiants invalides ou inactifs
    """
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
