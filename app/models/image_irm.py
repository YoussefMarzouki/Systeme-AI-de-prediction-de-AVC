import uuid
from datetime import datetime
from app.core.db import db

class ImageIRM(db.Model):
    __tablename__ = 'images_irm'
    idImage = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    format = db.Column(db.String(50), nullable=False, default='DICOM')
    cheminStockage = db.Column(db.String(500), nullable=False)
    dateAcquisition = db.Column(db.DateTime, default=datetime.utcnow)
    qualiteOK = db.Column(db.Boolean, default=True)
    
    dossier_id = db.Column(db.String(36), db.ForeignKey('dossiers_patients.idDossier'), nullable=False)
    
    analyse_ia = db.relationship('AnalyseIA', backref='image_irm', uselist=False, lazy=True) # 1 to 1 per diagram "produit"
