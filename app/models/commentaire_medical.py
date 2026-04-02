import uuid
from datetime import datetime
from app.core.db import db

class CommentaireMedical(db.Model):
    __tablename__ = 'commentaires_medicaux'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    texte = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 0..* from DossierPatient contains CommentaireMedical
    dossier_id = db.Column(db.String(36), db.ForeignKey('dossiers_patients.idDossier'), nullable=False)
    
    # Medecin effectue 0..* CommentaireMedical
    medecin_id = db.Column(db.String(36), db.ForeignKey('utilisateurs.id'), nullable=False)
