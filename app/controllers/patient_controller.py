from flask import Blueprint, request, jsonify
import uuid
from app.services.patient_service import PatientService
from app.repositories.patient_repository import PatientRepository
from app.core.db import db

patient_bp = Blueprint('patient', __name__)
patient_repo = PatientRepository()
patient_service = PatientService(patient_repo)


@patient_bp.route('/api/v1/patients', methods=['GET'])
def list_patients():
    try:
        patients = patient_service.list_patients()
        return jsonify({"status": "success", "patients": patients}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@patient_bp.route('/api/v1/patients', methods=['POST'])
def create_patient():
    """Créer un nouveau patient
    ---
    tags:
      - Patients
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nom
            - prenom
            - dateNaissance
            - sexe
          properties:
            nom:
              type: string
              example: "Doe"
            prenom:
              type: string
              example: "John"
            cin:
              type: string
              example: "AB123456"
            dateNaissance:
              type: string
              format: date
              example: "1990-05-15"
            sexe:
              type: string
              example: "M"
    responses:
      201:
        description: Patient créé avec succès
        schema:
          type: object
          properties:
            status:
              type: string
            patient_id:
              type: string
      400:
        description: Erreur de validation
    """
    data = request.json
    current_user_id = request.headers.get('User-ID', str(uuid.uuid4()))
    try:
        patient_id = patient_service.create_patient(data, current_user_id)
        db.session.commit()
        return jsonify({"status": "success", "patient_id": patient_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@patient_bp.route('/api/v1/patients/<string:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Récupérer un patient par son ID
    ---
    tags:
      - Patients
    parameters:
      - name: patient_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Patient trouvé
      404:
        description: Patient introuvable
    """
    try:
        patient_data = patient_service.get_patient(patient_id)
        return jsonify({"status": "success", "patient": patient_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@patient_bp.route('/api/v1/patients/<string:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json or {}
    try:
        patient = patient_service.update_patient(patient_id, data)
        return jsonify({"status": "success", "patient": patient}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@patient_bp.route('/api/v1/patients/<string:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        patient_service.delete_patient(patient_id)
        return jsonify({"status": "success", "message": "Patient supprime"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@patient_bp.route('/api/v1/patients/search', methods=['GET'])

def search_patients():
    """Rechercher des patients par nom ou CIN
    ---
    tags:
      - Patients
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Terme de recherche
    responses:
      200:
        description: Liste des patients correspondants
      400:
        description: Erreur
    """
    query = request.args.get('q', '')
    try:
        patients = patient_service.search_patients(query)
        return jsonify({"status": "success", "patients": patients}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@patient_bp.route('/api/v1/patients/check-cin', methods=['GET'])
def check_cin():
    """Vérifier si un CIN existe déjà
    ---
    tags:
      - Patients
    parameters:
      - name: cin
        in: query
        type: string
        required: true
        description: Numéro CIN à vérifier
    responses:
      200:
        description: Résultat de la vérification
        schema:
          type: object
          properties:
            status:
              type: string
            exists:
              type: boolean
      400:
        description: CIN non fourni
    """
    cin = request.args.get('cin', '')
    if not cin:
        return jsonify({"error": "CIN parameter is required"}), 400
    try:
        exists = patient_service.check_cin(cin)
        return jsonify({"status": "success", "exists": exists}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
