import os
from datetime import timedelta
import bcrypt
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from sqlalchemy import text
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

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'strokeai-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
    
    db.init_app(app)
    JWTManager(app)
    CORS(app)
    
    # Enregistrement des Blueprints via Controllers
    register_controllers(app)
    
    # Initialisation de Swagger
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Création automatique des tables
    with app.app_context():
        try:
            db.create_all()
            ensure_patient_contact_columns()
            ensure_default_admin()
            print("[+] Swagger UI disponible sur http://localhost:5000/apidocs/")
        except Exception as e:
            print(f"[!] Erreur de connexion à PostgreSQL: {e}")
            print(f"[!] L'URL utilisée était: {db_url}")

        
    return app


def ensure_patient_contact_columns():
    columns = {
        "email": "VARCHAR(120)",
        "telephone": "VARCHAR(30)",
        "adresse": "VARCHAR(255)",
    }
    for column, column_type in columns.items():
        db.session.execute(text(
            f"ALTER TABLE patients ADD COLUMN IF NOT EXISTS {column} {column_type}"
        ))
    db.session.commit()


def ensure_default_admin():
    from app.models.user import Admin

    admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@hopital.tn')
    admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'password123')
    existing_admin = Admin.query.filter_by(email=admin_email).first()

    if existing_admin:
        return

    hashed_password = bcrypt.hashpw(
        admin_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    db.session.add(Admin(
        id='55555555-5555-5555-5555-555555555555',
        nom='Administrateur Systeme',
        email=admin_email,
        motDePasse=hashed_password,
        etat='actif'
    ))
    db.session.commit()
