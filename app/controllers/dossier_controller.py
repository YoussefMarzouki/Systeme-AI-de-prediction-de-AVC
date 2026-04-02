from flask import Blueprint, request, jsonify
import uuid
from app.services.dossier_service import DossierService
from app.repositories.dossier_repository import DossierRepository
from app.repositories.donnees_cliniques_repository import DonneesCliniquesRepository
from app.core.db import db

dossier_bp = Blueprint('dossier', __name__)

dossier_repo = DossierRepository()
donnees_repo = DonneesCliniquesRepository()
dossier_service = DossierService(dossier_repo, donnees_repo)

@dossier_bp.route('/api/v1/dossiers', methods=['POST'])
def create_dossier():
    data = request.json
    current_user_id = request.headers.get('User-ID')
    
    # Normally check roles, here mock 'is_medecin' to False by default
    is_medecin = data.get('is_medecin', False)
    
    try:
        id_dossier = dossier_service.create_dossier(data['patient_id'], current_user_id, is_medecin)
        db.session.commit()
        return jsonify({"status": "success", "idDossier": id_dossier}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@dossier_bp.route('/api/v1/dossiers/<string:dossier_id>/donnees-cliniques', methods=['POST'])
def add_donnees_cliniques(dossier_id):
    data = request.json
    
    try:
        donnees_id = dossier_service.add_donnees_cliniques(dossier_id, data)
        db.session.commit()
        return jsonify({"status": "success", "donnees_cliniques_id": donnees_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
