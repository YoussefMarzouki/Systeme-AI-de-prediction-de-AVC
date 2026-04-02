import uuid
from datetime import datetime
from app.core.db import db

class Rapport(db.Model):
    __tablename__ = 'rapports'
    idRapport = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dateGeneration = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(50), default='GENERATED')
    
    # Medecin "valide" Rapport (1 to 0..*)
    medecin_id = db.Column(db.String(36), db.ForeignKey('utilisateurs.id'), nullable=False)
    
    # DossierPatient "génère" Rapport (1 to 0..*)
    dossier_id = db.Column(db.String(36), db.ForeignKey('dossiers_patients.idDossier'), nullable=False)
