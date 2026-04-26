from flask import Blueprint, request, jsonify
from app.services.donnees_cliniques_service import DonneesCliniquesService
from app.repositories.donnees_cliniques_repository import DonneesCliniquesRepository
from app.repositories.dossier_repository import DossierRepository
from app.core.db import db

donnees_cliniques_bp = Blueprint('donnees_cliniques', __name__)

donnees_repo = DonneesCliniquesRepository()
dossier_repo = DossierRepository()
donnees_service = DonneesCliniquesService(donnees_repo, dossier_repo)


@donnees_cliniques_bp.route('/api/v1/dossiers/<string:dossier_id>/donnees-cliniques', methods=['POST'])
def add_donnees_cliniques(dossier_id):
    """Ajouter des données cliniques à un dossier
    ---
    tags:
      - Données Cliniques
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
            fast:
              type: string
              description: "Symptômes FAST séparés par virgules"
              example: "Paralysie faciale, Faiblesse du bras"
            tension:
              type: string
              example: "120/80"
            age:
              type: integer
              example: 65
            notes:
              type: string
              example: "Patient conscient, douleurs thoraciques"
    responses:
      201:
        description: Données cliniques ajoutées
        schema:
          type: object
          properties:
            status:
              type: string
            donnees_cliniques_id:
              type: string
      400:
        description: Erreur de validation
    """
    data = request.json
    try:
        donnees_id = donnees_service.add_donnees_cliniques(dossier_id, data)
        db.session.commit()
        return jsonify({"status": "success", "donnees_cliniques_id": donnees_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@donnees_cliniques_bp.route('/api/v1/dossiers/<string:dossier_id>/donnees-cliniques', methods=['GET'])
def get_donnees_cliniques(dossier_id):
    """Récupérer toutes les données cliniques d'un dossier
    ---
    tags:
      - Données Cliniques
    parameters:
      - name: dossier_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Liste des données cliniques
      400:
        description: Erreur
    """
    try:
        entries = donnees_service.get_by_dossier(dossier_id)
        return jsonify({"status": "success", "donnees_cliniques": entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
