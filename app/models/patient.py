import uuid
from app.core.db import db

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    dateNaissance = db.Column(db.Date, nullable=False)
    sexe = db.Column(db.String(20), nullable=False)
    
    dossiers = db.relationship('DossierPatient', backref='patient', lazy=True)
