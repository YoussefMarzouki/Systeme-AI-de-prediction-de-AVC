from flask import Blueprint, jsonify, request

from app.core.db import db
from app.repositories.rapport_repository import RapportRepository
from app.services.rapport_service import RapportService

rapport_bp = Blueprint("rapport", __name__)

rapport_repo = RapportRepository()
rapport_service = RapportService(rapport_repo)


@rapport_bp.route("/api/v1/rapports", methods=["GET"])
def list_rapports():
    """Récupérer tous les rapports médicaux
    ---
    tags:
      - Rapports
    responses:
      200:
        description: Liste de tous les rapports
      500:
        description: Erreur serveur
    """
    try:
        rapports = rapport_service.list_rapports()
        return jsonify({"status": "success", "rapports": rapports}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rapport_bp.route("/api/v1/rapports", methods=["POST"])
def create_rapport():
    """Créer un nouveau rapport médical manuellement
    ---
    tags:
      - Rapports
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - medecin_id
            - dossier_id
            - contenu
          properties:
            medecin_id:
              type: string
              example: "uuid-du-medecin"
            dossier_id:
              type: string
              example: "uuid-du-dossier"
            contenu:
              type: object
              description: Contenu JSON du rapport
            statut:
              type: string
              example: "DRAFT"
    responses:
      201:
        description: Rapport créé avec succès
      400:
        description: Erreur de validation
    """
    payload = request.json or {}
    try:
        rapport_id = rapport_service.create_rapport(payload)
        return jsonify({"status": "success", "rapport_id": rapport_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/validation-queue", methods=["GET"])
def get_validation_queue():
    """Récupérer la file d'attente des rapports pour validation spécialisée
    ---
    tags:
      - Rapports
    parameters:
      - name: status
        in: query
        type: string
        required: false
        default: "PENDING_VALIDATION"
        description: Statut des rapports à filtrer
    responses:
      200:
        description: File d'attente récupérée avec succès
      500:
        description: Erreur serveur
    """
    status = request.args.get("status", "PENDING_VALIDATION")
    try:
        queue = rapport_service.get_validation_queue(status)
        return jsonify({"status": "success", "queue": queue}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rapport_bp.route("/api/v1/rapports/dossier/<string:dossier_id>", methods=["GET"])
def get_case_detail(dossier_id):
    """Récupérer les détails complets d'un dossier pour examen spécialisé
    ---
    tags:
      - Rapports
    parameters:
      - name: dossier_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Détails du dossier trouvés
      404:
        description: Dossier ou rapport introuvable
    """
    try:
        case = rapport_service.get_case_detail(dossier_id)
        return jsonify({"status": "success", "case": case}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@rapport_bp.route("/api/v1/rapports/patient/<string:patient_id>", methods=["GET"])
def get_rapports_by_patient(patient_id):
    """Récupérer les rapports d'un patient spécifique
    ---
    tags:
      - Rapports
    parameters:
      - name: patient_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Liste des rapports du patient
      404:
        description: Patient introuvable
    """
    try:
        rapports = rapport_service.get_rapports_by_patient(patient_id)
        return jsonify({"status": "success", "rapports": rapports}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>", methods=["GET"])
def get_rapport(rapport_id):
    """Récupérer un rapport spécifique par son ID
    ---
    tags:
      - Rapports
    parameters:
      - name: rapport_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Rapport trouvé
      404:
        description: Rapport introuvable
    """
    try:
        rapport = rapport_service.get_rapport(rapport_id)
        return jsonify({"status": "success", "rapport": rapport}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>", methods=["PUT"])
def update_rapport(rapport_id):
    """Mettre à jour le contenu d'un rapport médical
    ---
    tags:
      - Rapports
    parameters:
      - name: rapport_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            contenu:
              type: object
              description: Nouveau contenu du rapport
            statut:
              type: string
              example: "VALIDATED"
    responses:
      200:
        description: Rapport mis à jour avec succès
      400:
        description: Erreur lors de la mise à jour
    """
    payload = request.json or {}
    try:
        rapport = rapport_service.update_rapport(rapport_id, payload)
        return jsonify({"status": "success", "rapport": rapport}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>", methods=["DELETE"])
def delete_rapport(rapport_id):
    """Supprimer un rapport médical
    ---
    tags:
      - Rapports
    parameters:
      - name: rapport_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Rapport supprimé avec succès
      400:
        description: Erreur lors de la suppression
    """
    try:
        rapport_service.delete_rapport(rapport_id)
        return jsonify({"status": "success", "message": "Rapport supprime"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>/validate", methods=["PATCH"])
def validate_rapport(rapport_id):
    """Valider un rapport en tant qu'expert/spécialiste
    ---
    tags:
      - Rapports
    parameters:
      - name: rapport_id
        in: path
        type: string
        required: true
      - name: User-ID
        in: header
        type: string
        required: true
        description: ID unique du spécialiste
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            notes:
              type: string
              example: "Confirmation du diagnostic d'AVC ischémique."
    responses:
      200:
        description: Rapport validé avec succès
      400:
        description: En-tête User-ID manquant ou erreur
    """
    specialist_id = request.headers.get("User-ID")
    if not specialist_id:
        return jsonify({"error": "User-ID header is required"}), 400

    payload = request.json or {}
    try:
        result = rapport_service.validate_rapport(rapport_id, specialist_id, payload)
        return jsonify({"status": "success", "rapport": result}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>/reject", methods=["PATCH"])
def reject_rapport(rapport_id):
    """Rejeter un rapport en tant qu'expert/spécialiste
    ---
    tags:
      - Rapports
    parameters:
      - name: rapport_id
        in: path
        type: string
        required: true
      - name: User-ID
        in: header
        type: string
        required: true
        description: ID unique du spécialiste
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            raison:
              type: string
              example: "Qualité d'image insuffisante."
    responses:
      200:
        description: Rapport rejeté avec succès
      400:
        description: En-tête User-ID manquant ou erreur
    """
    specialist_id = request.headers.get("User-ID")
    if not specialist_id:
        return jsonify({"error": "User-ID header is required"}), 400

    payload = request.json or {}
    try:
        result = rapport_service.reject_rapport(rapport_id, specialist_id, payload)
        return jsonify({"status": "success", "rapport": result}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
