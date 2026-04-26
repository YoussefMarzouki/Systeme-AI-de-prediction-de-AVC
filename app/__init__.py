import os
from flask import Flask
from flasgger import Swagger
from app.core.db import db

# Import all models to ensure they are registered with SQLAlchemy
import app.models 
from app.controllers import register_controllers

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "info": {
        "title": "StrokeAI - API Documentation",
        "description": "API REST du système d'information clinique StrokeAI pour la détection d'AVC.",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http"],
    "tags": [
        {"name": "Patients", "description": "Gestion des patients"},
        {"name": "Dossiers", "description": "Gestion des dossiers médicaux"},
        {"name": "Données Cliniques", "description": "Gestion des données cliniques et symptômes"},
        {"name": "Images IRM", "description": "Gestion des images IRM"},
        {"name": "Prédictions", "description": "Module IA de prédiction"}
    ]
}

def create_app():
    app = Flask(__name__)
    
    # Configuration PostgreSQL au lieu de SQLite
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/postgres')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Enregistrement des Blueprints via Controllers
    register_controllers(app)
    
    # Initialisation de Swagger
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Création automatique des tables
    with app.app_context():
        try:
            db.create_all()
            print("[+] Tables PostgreSQL créées avec succès ! (models: Patient, Dossier, ExamenIRM, etc.)")
            print("[+] Swagger UI disponible sur http://localhost:5000/apidocs/")
        except Exception as e:
            print(f"[!] Erreur de connexion à PostgreSQL: {e}")
            print(f"[!] L'URL utilisée était: {db_url}")
            print("[!] Vérifiez que le mot de passe est 'postgres' ou définissez la variable d'environnement DATABASE_URL")
        
    return app
