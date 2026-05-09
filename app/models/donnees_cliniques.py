import uuid
from datetime import datetime
from app.core.db import db

class DonneesCliniques(db.Model):
    __tablename__ = 'symptomes'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dateSaisie = db.Column(db.DateTime, default=datetime.utcnow)
    fast = db.Column(db.String(100), nullable=True)
    tension = db.Column(db.String(50), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    dossier_id = db.Column(db.String(36), db.ForeignKey('dossiers_patients.idDossier'), nullable=False)
    
    # Relationships for Analyses depending on this data
    analyse_symptomes = db.relationship('AnalyseSymptomes', backref='donnees_cliniques', uselist=False, lazy=True)
