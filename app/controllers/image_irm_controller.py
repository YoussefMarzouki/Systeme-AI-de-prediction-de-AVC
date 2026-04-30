from flask import Blueprint, request, jsonify
from app.services.image_irm_service import ImageIRMService
from app.repositories.image_irm_repository import ImageIRMRepository
from app.core.db import db

image_irm_bp = Blueprint('image_irm', __name__)
irm_repo = ImageIRMRepository()
irm_service = ImageIRMService(irm_repo)


@image_irm_bp.route('/api/v1/images-irm', methods=['GET'])
def list_images_irm():
    try:
        images = irm_service.list_images()
        return jsonify({"status": "success", "images": images}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@image_irm_bp.route('/api/v1/dossiers/<string:dossier_id>/image-irm', methods=['POST'])
def upload_image_irm(dossier_id):
    """Uploader une image IRM DICOM pour un dossier
    ---
    tags:
      - Images IRM
    consumes:
      - multipart/form-data
    parameters:
      - name: dossier_id
        in: path
        type: string
        required: true
      - name: file
        in: formData
        type: file
        required: true
        description: Fichier ZIP contenant les images DICOM
    responses:
      200:
        description: Image uploadée avec succès
        schema:
          type: object
          properties:
            status:
              type: string
            idImage:
              type: string
      400:
        description: Format de fichier invalide
    """
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
    """Ajouter les métadonnées d'une image IRM hébergée en externe
    ---
    tags:
      - Images IRM
    parameters:
      - name: dossier_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              description: URL Cloudinary de l'image
              example: "https://res.cloudinary.com/xxx/image.jpg"
            format:
              type: string
              example: "MRI"
    responses:
      201:
        description: Métadonnées enregistrées
      400:
        description: Erreur
    """
    data = request.json
    try:
        image_id = irm_service.add_image_metadata(dossier_id, data)
        db.session.commit()
        return jsonify({"status": "success", "idImage": image_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@image_irm_bp.route('/api/v1/images-irm/<string:image_id>', methods=['GET'])
def get_image_irm(image_id):
    try:
        image = irm_service.get_image(image_id)
        return jsonify({"status": "success", "image": image}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@image_irm_bp.route('/api/v1/images-irm/<string:image_id>', methods=['PUT'])
def update_image_irm(image_id):
    data = request.json or {}
    try:
        image = irm_service.update_image(image_id, data)
        return jsonify({"status": "success", "image": image}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@image_irm_bp.route('/api/v1/images-irm/<string:image_id>', methods=['DELETE'])
def delete_image_irm(image_id):
    try:
        irm_service.delete_image(image_id)
        return jsonify({"status": "success", "message": "Image IRM supprimee"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@image_irm_bp.route('/mri/request', methods=['POST'])
def request_mri():
    """Simuler une demande d'examen IRM
    ---
    tags:
      - Images IRM
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            patientId:
              type: string
            priority:
              type: string
              example: "NORMAL"
            notes:
              type: string
    responses:
      200:
        description: Demande simulée avec succès
      400:
        description: Erreur
    """
    data = request.json
    try:
        result = irm_service.request_mri(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@image_irm_bp.route('/mri/upload', methods=['POST'])
def upload_mri():
    """Uploader un fichier IRM pour un patient
    ---
    tags:
      - Images IRM
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
      - name: patientId
        in: formData
        type: string
        required: true
    responses:
      201:
        description: Image uploadée avec succès
      400:
        description: Fichier manquant ou patientId requis
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
        
    file = request.files['file']
    patient_id = request.form.get('patientId')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not patient_id:
        return jsonify({"error": "patientId is required form data"}), 400

    try:
        image_id = irm_service.upload_mri(patient_id, file)
        db.session.commit()
        return jsonify({"status": "success", "image_id": image_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@image_irm_bp.route('/mri/<string:patient_id>', methods=['GET'])
def get_mri_list(patient_id):
    """Récupérer toutes les images IRM d'un patient
    ---
    tags:
      - Images IRM
    parameters:
      - name: patient_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Liste des images IRM
      400:
        description: Erreur
    """
    try:
        images = irm_service.get_patient_mri(patient_id)
        return jsonify({"status": "success", "images": images}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
