from flask import Blueprint, request, jsonify
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.utilisateur_service import UtilisateurService
from app.core.db import db

utilisateur_bp = Blueprint("utilisateur", __name__)

utilisateur_repo = UtilisateurRepository()
utilisateur_service = UtilisateurService(utilisateur_repo)


@utilisateur_bp.route("/api/v1/utilisateurs", methods=["GET"])
def list_utilisateurs():
    try:
        users = utilisateur_service.list_utilisateurs()
        return jsonify({"status": "success", "utilisateurs": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utilisateur_bp.route("/api/v1/utilisateurs", methods=["POST"])
def create_utilisateur():
    data = request.json or {}
    try:
        user_id = utilisateur_service.create_utilisateur(data)
        return jsonify({"status": "success", "id": user_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@utilisateur_bp.route("/api/v1/utilisateurs/<string:user_id>", methods=["GET"])
def get_utilisateur(user_id):
    try:
        user = utilisateur_service.get_utilisateur(user_id)
        return jsonify({"status": "success", "utilisateur": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@utilisateur_bp.route("/api/v1/utilisateurs/<string:user_id>", methods=["PUT"])
def update_utilisateur(user_id):
    data = request.json or {}
    try:
        user = utilisateur_service.update_utilisateur(user_id, data)
        return jsonify({"status": "success", "utilisateur": user}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@utilisateur_bp.route("/api/v1/utilisateurs/<string:user_id>", methods=["DELETE"])
def delete_utilisateur(user_id):
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
    query = request.args.get("q", "")
    try:
        users = utilisateur_service.search_utilisateurs(query)
        return jsonify({"status": "success", "utilisateurs": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
