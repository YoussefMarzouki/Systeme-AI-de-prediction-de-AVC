from flask import Blueprint, request, jsonify
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.utilisateur_service import UtilisateurService
from app.core.db import db

utilisateur_bp = Blueprint("utilisateur", __name__)

utilisateur_repo = UtilisateurRepository()
utilisateur_service = UtilisateurService(utilisateur_repo)


@utilisateur_bp.route("/api/v1/utilisateurs", methods=["GET"])
def list_utilisateurs():
    """Récupérer la liste de tous les utilisateurs
    ---
    tags:
      - Utilisateurs
    responses:
      200:
        description: Liste des utilisateurs récupérée avec succès
      500:
        description: Erreur serveur
    """
    try:
        users = utilisateur_service.list_utilisateurs()
        return jsonify({"status": "success", "utilisateurs": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utilisateur_bp.route("/api/v1/utilisateurs", methods=["POST"])
def create_utilisateur():
    """Créer un nouvel utilisateur (Médecin, Expert ou Admin)
    ---
    tags:
      - Utilisateurs
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - nom
            - motDePasse
            - role
          properties:
            email:
              type: string
              example: "doctor@hopital.tn"
            nom:
              type: string
              example: "Dr. House"
            motDePasse:
              type: string
              example: "securepassword"
            role:
              type: string
              enum: ["medecin", "expert", "admin"]
              example: "medecin"
            specialite:
              type: string
              example: "Neurologue"
    responses:
      201:
        description: Utilisateur créé avec succès
      400:
        description: Erreur de validation ou email déjà utilisé
    """
    data = request.json or {}
    try:
        user_id = utilisateur_service.create_utilisateur(data)
        return jsonify({"status": "success", "id": user_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@utilisateur_bp.route("/api/v1/utilisateurs/<string:user_id>", methods=["GET"])
def get_utilisateur(user_id):
    """Récupérer les détails d'un utilisateur par son ID
    ---
    tags:
      - Utilisateurs
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Utilisateur trouvé
      404:
        description: Utilisateur introuvable
    """
    try:
        user = utilisateur_service.get_utilisateur(user_id)
        return jsonify({"status": "success", "utilisateur": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@utilisateur_bp.route("/api/v1/utilisateurs/<string:user_id>", methods=["PUT"])
def update_utilisateur(user_id):
    """Mettre à jour les informations d'un utilisateur
    ---
    tags:
      - Utilisateurs
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Dr. Gregory House"
            email:
              type: string
              example: "g.house@hopital.tn"
            specialite:
              type: string
              example: "Neurologie cognitive"
            etat:
              type: string
              enum: ["actif", "inactif"]
              example: "actif"
    responses:
      200:
        description: Utilisateur mis à jour avec succès
      400:
        description: Erreur lors de la mise à jour
    """
    data = request.json or {}
    try:
        user = utilisateur_service.update_utilisateur(user_id, data)
        return jsonify({"status": "success", "utilisateur": user}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@utilisateur_bp.route("/api/v1/utilisateurs/<string:user_id>", methods=["DELETE"])
def delete_utilisateur(user_id):
    """Supprimer un utilisateur
    ---
    tags:
      - Utilisateurs
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - name: User-ID
        in: header
        type: string
        required: true
        description: ID de l'utilisateur effectuant la suppression
    responses:
      200:
        description: Utilisateur supprimé avec succès
      403:
        description: Auto-suppression interdite
      400:
        description: Erreur lors de la suppression
    """
    current_user_id = request.headers.get("User-ID")
    if current_user_id and current_user_id == user_id:
        return jsonify({"error": "You cannot delete your own account."}), 403

    try:
        utilisateur_service.delete_utilisateur(user_id)
        return jsonify({"status": "success", "message": "User deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@utilisateur_bp.route("/api/v1/utilisateurs/search", methods=["GET"])
def search_utilisateurs():
    """Rechercher des utilisateurs par nom ou email
    ---
    tags:
      - Utilisateurs
    parameters:
      - name: q
        in: query
        type: string
        required: true
    responses:
      200:
        description: Liste des utilisateurs correspondants
      400:
        description: Erreur
    """
    query = request.args.get("q", "")
    try:
        users = utilisateur_service.search_utilisateurs(query)
        return jsonify({"status": "success", "utilisateurs": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
