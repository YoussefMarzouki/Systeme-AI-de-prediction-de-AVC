from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.db import db

class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    motDePasse = db.Column(db.String(256), nullable=False)
    etat = db.Column(db.String(50), nullable=False, default='actif')
    type = db.Column(db.String(50))  # For STI (Single Table Inheritance)

    __mapper_args__ = {
        'polymorphic_identity': 'utilisateur',
        'polymorphic_on': type
    }

class Medecin(Utilisateur):
    specialite = db.Column(db.Boolean, nullable=True) # Assuming True=Specialist, False=Generalist as per diagram
    
    __mapper_args__ = {
        'polymorphic_identity': 'medecin',
    }

class AgentAccueil(Utilisateur):
    __mapper_args__ = {
        'polymorphic_identity': 'agent_accueil',
    }

class Admin(Utilisateur):
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }
