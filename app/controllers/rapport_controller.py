from flask import Blueprint, jsonify, request

from app.core.db import db
from app.repositories.rapport_repository import RapportRepository
from app.services.rapport_service import RapportService

rapport_bp = Blueprint("rapport", __name__)

rapport_repo = RapportRepository()
rapport_service = RapportService(rapport_repo)


@rapport_bp.route("/api/v1/rapports", methods=["GET"])
def list_rapports():
    try:
        rapports = rapport_service.list_rapports()
        return jsonify({"status": "success", "rapports": rapports}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rapport_bp.route("/api/v1/rapports", methods=["POST"])
def create_rapport():
    payload = request.json or {}
    try:
        rapport_id = rapport_service.create_rapport(payload)
        return jsonify({"status": "success", "rapport_id": rapport_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/validation-queue", methods=["GET"])
def get_validation_queue():
    """List reports for specialist validation."""
    status = request.args.get("status", "PENDING_VALIDATION")
    try:
        queue = rapport_service.get_validation_queue(status)
        return jsonify({"status": "success", "queue": queue}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rapport_bp.route("/api/v1/rapports/dossier/<string:dossier_id>", methods=["GET"])
def get_case_detail(dossier_id):
    """Get a full report/case detail for specialist review."""
    try:
        case = rapport_service.get_case_detail(dossier_id)
        return jsonify({"status": "success", "case": case}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@rapport_bp.route("/api/v1/rapports/patient/<string:patient_id>", methods=["GET"])
def get_rapports_by_patient(patient_id):
    try:
        rapports = rapport_service.get_rapports_by_patient(patient_id)
        return jsonify({"status": "success", "rapports": rapports}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>", methods=["GET"])
def get_rapport(rapport_id):
    try:
        rapport = rapport_service.get_rapport(rapport_id)
        return jsonify({"status": "success", "rapport": rapport}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>", methods=["PUT"])
def update_rapport(rapport_id):
    payload = request.json or {}
    try:
        rapport = rapport_service.update_rapport(rapport_id, payload)
        return jsonify({"status": "success", "rapport": rapport}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>", methods=["DELETE"])
def delete_rapport(rapport_id):
    try:
        rapport_service.delete_rapport(rapport_id)
        return jsonify({"status": "success", "message": "Rapport supprime"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@rapport_bp.route("/api/v1/rapports/<string:rapport_id>/validate", methods=["PATCH"])
def validate_rapport(rapport_id):
    """Validate a draft report after specialist review."""
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
    """Reject a draft report after specialist review."""
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
