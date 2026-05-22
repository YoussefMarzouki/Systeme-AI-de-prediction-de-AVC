from flask import Blueprint, request, jsonify
from app.services.donnees_cliniques_service import DonneesCliniquesService
from app.repositories.donnees_cliniques_repository import DonneesCliniquesRepository
from app.repositories.dossier_repository import DossierRepository
from app.core.db import db

donnees_cliniques_bp = Blueprint('donnees_cliniques', __name__)

donnees_repo = DonneesCliniquesRepository()
dossier_repo = DossierRepository()
donnees_service = DonneesCliniquesService(donnees_repo, dossier_repo)


@donnees_cliniques_bp.route('/api/v1/donnees-cliniques', methods=['GET'])
def list_donnees_cliniques():
    """Récupérer toutes les entrées de données cliniques
    ---
    tags:
      - Données Cliniques
    responses:
      200:
        description: Liste des données cliniques
      500:
        description: Erreur serveur
    """
    try:
        entries = donnees_service.list_donnees_cliniques()
        return jsonify({"status": "success", "donnees_cliniques": entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


@donnees_cliniques_bp.route('/api/v1/donnees-cliniques/<string:donnees_id>', methods=['GET'])
def get_donnees_cliniques_by_id(donnees_id):
    """Récupérer une entrée spécifique de données cliniques par ID
    ---
    tags:
      - Données Cliniques
    parameters:
      - name: donnees_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Données cliniques trouvées
      404:
        description: Données cliniques introuvables
    """
    try:
        donnees = donnees_service.get_donnees_cliniques(donnees_id)
        return jsonify({"status": "success", "donnees_cliniques": donnees}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@donnees_cliniques_bp.route('/api/v1/donnees-cliniques/<string:donnees_id>', methods=['PUT'])
def update_donnees_cliniques(donnees_id):
    """Mettre à jour une entrée de données cliniques
    ---
    tags:
      - Données Cliniques
    parameters:
      - name: donnees_id
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
              example: "Paralysie faciale"
            tension:
              type: string
              example: "130/85"
            age:
              type: integer
              example: 66
            notes:
              type: string
              example: "Notes médicales mises à jour"
    responses:
      200:
        description: Données cliniques mises à jour avec succès
      400:
        description: Erreur lors de la mise à jour
    """
    data = request.json or {}
    try:
        donnees = donnees_service.update_donnees_cliniques(donnees_id, data)
        return jsonify({"status": "success", "donnees_cliniques": donnees}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@donnees_cliniques_bp.route('/api/v1/donnees-cliniques/<string:donnees_id>', methods=['DELETE'])
def delete_donnees_cliniques(donnees_id):
    """Supprimer une entrée de données cliniques
    ---
    tags:
      - Données Cliniques
    parameters:
      - name: donnees_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Données cliniques supprimées avec succès
      400:
        description: Erreur lors de la suppression
    """
    try:
        donnees_service.delete_donnees_cliniques(donnees_id)
        return jsonify({"status": "success", "message": "Donnees cliniques supprimees"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
