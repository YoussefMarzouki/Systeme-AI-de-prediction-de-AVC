import os
from flask import Flask
from app.core.db import db

# Import all models to ensure they are registered with SQLAlchemy
import app.models 
from app.controllers import register_controllers

def create_app():
    app = Flask(__name__)
    
    # Configuration PostgreSQL au lieu de SQLite
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/postgres')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Enregistrement des Blueprints via Controllers
    register_controllers(app)
    
    # Création automatique des tables
    with app.app_context():
        try:
            db.create_all()
            print("[+] Tables PostgreSQL créées avec succès ! (models: Patient, Dossier, ExamenIRM, etc.)")
        except Exception as e:
            print(f"[!] Erreur de connexion à PostgreSQL: {e}")
            print(f"[!] L'URL utilisée était: {db_url}")
            print("[!] Vérifiez que le mot de passe est 'postgres' ou définissez la variable d'environnement DATABASE_URL")
        
    return app
