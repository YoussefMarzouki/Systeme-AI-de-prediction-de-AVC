from flask import Blueprint, request, jsonify
from app.services.mri_service import MRIService
from app.core.db import db

mri_bp = Blueprint('mri', __name__)
mri_service = MRIService()

@mri_bp.route('/mri/request', methods=['POST'])
def request_mri():
    data = request.json
    try:
        result = mri_service.request_mri(data)
        # Assuming simulation means we just return success mock Data.
        # But we don't need to persist simulation if it's meant to be simple.
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@mri_bp.route('/mri/upload', methods=['POST'])
def upload_mri():
    # Require multipart form with 'file' and 'patientId'
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
        
    file = request.files['file']
    patient_id = request.form.get('patientId')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not patient_id:
        return jsonify({"error": "patientId is required form data"}), 400

    try:
        image_id = mri_service.upload_mri(patient_id, file)
        db.session.commit()
        return jsonify({"status": "success", "image_id": image_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@mri_bp.route('/mri/<string:patient_id>', methods=['GET'])
def get_mri_list(patient_id):
    try:
        images = mri_service.get_patient_mri(patient_id)
        return jsonify({"status": "success", "images": images}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
