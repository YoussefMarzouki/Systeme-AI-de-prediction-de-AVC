from flask import Blueprint, request, jsonify
from app.services.image_irm_service import ImageIRMService
from app.repositories.image_irm_repository import ImageIRMRepository
from app.core.db import db

image_irm_bp = Blueprint('image_irm', __name__)
irm_repo = ImageIRMRepository()
irm_service = ImageIRMService(irm_repo)

@image_irm_bp.route('/api/v1/dossiers/<string:dossier_id>/image-irm', methods=['POST'])
def upload_image_irm(dossier_id):
    file = request.files.get('file')
    
    try:
        res = irm_service.upload_image(dossier_id, file)
        
        if "error" in res:
            db.session.rollback()
            return jsonify({"error": res["error"]}), res.get("code", 400)
            
        db.session.commit()
        return jsonify({"status": "success", "idImage": res["image_id"]}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@image_irm_bp.route('/api/v1/dossiers/<string:dossier_id>/image-metadata', methods=['POST'])
def add_image_metadata(dossier_id):
    data = request.json
    try:
        image_id = irm_service.add_image_metadata(dossier_id, data)
        db.session.commit()
        return jsonify({"status": "success", "idImage": image_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
