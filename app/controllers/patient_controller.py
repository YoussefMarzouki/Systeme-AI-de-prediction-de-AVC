from flask import Blueprint, request, jsonify
import uuid
from app.services.patient_service import PatientService
from app.repositories.patient_repository import PatientRepository
from app.core.db import db

# We will support both the clean /patients endpoint and legacy /api/v1/patients
patient_bp = Blueprint('patient', __name__)
patient_repo = PatientRepository()
patient_service = PatientService(patient_repo)

@patient_bp.route('/patients', methods=['POST'])
@patient_bp.route('/api/v1/patients', methods=['POST'])
def create_patient():
    data = request.json
    current_user_id = request.headers.get('User-ID', str(uuid.uuid4()))
    
    try:
        patient_id = patient_service.create_patient(data, current_user_id)
        db.session.commit()
        return jsonify({"status": "success", "patient_id": patient_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@patient_bp.route('/patients/<string:patient_id>', methods=['GET'])
def get_patient(patient_id):
    try:
        patient_data = patient_service.get_patient(patient_id)
        return jsonify({"status": "success", "patient": patient_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@patient_bp.route('/patients/<string:patient_id>/info', methods=['POST'])
def add_patient_info(patient_id):
    data = request.json
    try:
        donnees_id = patient_service.add_clinical_info(patient_id, data)
        db.session.commit()
        return jsonify({"status": "success", "donnees_cliniques_id": donnees_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@patient_bp.route('/patients/<string:patient_id>/symptoms', methods=['POST'])
def add_patient_symptoms(patient_id):
    data = request.json
    try:
        donnees_id = patient_service.add_symptoms(patient_id, data)
        db.session.commit()
        return jsonify({"status": "success", "donnees_cliniques_id": donnees_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@patient_bp.route('/patients/search', methods=['GET'])
@patient_bp.route('/api/v1/patients/search', methods=['GET'])
def search_patients():
    query = request.args.get('q', '')
    try:
        patients = patient_service.search_patients(query)
        return jsonify({"status": "success", "patients": patients}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
