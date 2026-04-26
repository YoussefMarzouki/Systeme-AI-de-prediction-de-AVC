import uuid
from datetime import datetime
from app.core.db import db
from sqlalchemy.dialects.postgresql import JSONB

class Rapport(db.Model):
    __tablename__ = 'rapports'
    idRapport = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dateGeneration = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Traceability for modifications
    dateModification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    statut = db.Column(db.String(50), default='GENERATED') # GENERATED, ARCHIVED, etc.
    
    # Optional fields to store the actual report data and file
    cheminFichier = db.Column(db.String(500), nullable=True) # Path to the saved PDF
    contenu = db.Column(db.JSON, nullable=True) # Store structured report data if needed
    
    # Medecin généraliste "crée" Rapport (1 to 0..*)
    medecin_id = db.Column(db.String(36), db.ForeignKey('utilisateurs.id'), nullable=False)
    
    # Medecin spécialiste "modifie/valider" Rapport 
    modifie_par_id = db.Column(db.String(36), db.ForeignKey('utilisateurs.id'), nullable=True)
    
    # DossierPatient "génère" Rapport (1 to 0..*)
    dossier_id = db.Column(db.String(36), db.ForeignKey('dossiers_patients.idDossier'), nullable=False)
