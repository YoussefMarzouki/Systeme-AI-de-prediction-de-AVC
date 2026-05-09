import uuid
from datetime import datetime
from app.core.db import db

class AnalyseIA(db.Model):
    __tablename__ = 'analyses_ia'
    idAnalyse = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dateAnalyse = db.Column(db.DateTime, default=datetime.utcnow)
    probabiliteAVC = db.Column(db.Float, nullable=False)
    scoreConfiance = db.Column(db.Float, nullable=False)
    modeleVersion = db.Column(db.String(100), nullable=False)
    
    # 1 to 1 association with ImageIRM (ImageIRM "produit" AnalyseIA)
    image_id = db.Column(db.String(36), db.ForeignKey('images_irm.idImage'), nullable=False, unique=True)
    
    # Evaluated by (1 -> 1)
    evaluation_risque = db.relationship('EvaluationRisque', backref='analyse_ia', uselist=False, lazy=True)

class AnalyseSymptomes(db.Model):
    __tablename__ = 'analyses_symptomes'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    valeur = db.Column(db.Float, nullable=False)
    methode = db.Column(db.String(100), nullable=False)
    
    # 1 to 1 association with DonneesCliniques ("produit")
    donnees_cliniques_id = db.Column(db.String(36), db.ForeignKey('symptomes.id'), nullable=False, unique=True)
    
    # Evaluated by (1 -> 1)
    evaluation_risque = db.relationship('EvaluationRisque', backref='analyse_symptomes', uselist=False, lazy=True)

class EvaluationRisque(db.Model):
    __tablename__ = 'evaluations_risque'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scoreGlobal = db.Column(db.Float, nullable=False)
    niveau = db.Column(db.String(50), nullable=False)
    
    # Relationships 1 to 1 "regroupe" as per diagram
    analyse_ia_id = db.Column(db.String(36), db.ForeignKey('analyses_ia.idAnalyse'), nullable=False, unique=True)
    analyse_symptomes_id = db.Column(db.String(36), db.ForeignKey('analyses_symptomes.id'), nullable=False, unique=True)
    
    # Relationship to dossier (implicit as 0..*)
    dossier_id = db.Column(db.String(36), db.ForeignKey('dossiers_patients.idDossier'), nullable=False)
