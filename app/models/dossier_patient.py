import uuid
from datetime import datetime
from app.core.db import db

class DossierPatient(db.Model):
    __tablename__ = 'dossiers_patients'
    idDossier = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dateCreation = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(50), default='OUVERT')
    
    # Relations defined in UML
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    agent_id = db.Column(db.String(36), db.ForeignKey('utilisateurs.id'), nullable=True) # AgentAccueil cree
    medecin_id = db.Column(db.String(36), db.ForeignKey('utilisateurs.id'), nullable=True) # Medecin cree ou suit
    
    # 0..* relationships to this dossier
    donnees_cliniques = db.relationship('DonneesCliniques', backref='dossier', lazy=True)
    images_irm = db.relationship('ImageIRM', backref='dossier', lazy=True)
    rapports = db.relationship('Rapport', backref='dossier', lazy=True)
    evaluations = db.relationship('EvaluationRisque', backref='dossier', lazy=True)
