import os
from werkzeug.utils import secure_filename
from app.models.image_irm import ImageIRM
from app.models.dossier_patient import DossierPatient
from app.repositories.image_irm_repository import ImageIRMRepository
from app.core.db import db
from datetime import datetime

class ImageIRMService:
    def __init__(self, irm_repo: ImageIRMRepository, upload_folder='uploads/mri'):
        self.irm_repo = irm_repo
        self.upload_folder = upload_folder
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def _get_or_create_dossier(self, patient_id: str):
        dossier = db.session.query(DossierPatient).filter_by(patient_id=patient_id).order_by(DossierPatient.dateCreation.desc()).first()
        if not dossier:
            dossier = DossierPatient(patient_id=patient_id)
            db.session.add(dossier)
            db.session.flush()
        return dossier

    def upload_image(self, dossier_id: str, file) -> dict:
        if not file or not file.filename.endswith('.zip'):
            return {"error": "Invalid file format. ZIP required.", "code": 400}

        # create image record
        new_irm = ImageIRM(
            dossier_id=dossier_id,
            format='DICOM',
            cheminStockage=f"/storage/irm/placeholder_{dossier_id}.zip",
            qualiteOK=True
        )
        irm = self.irm_repo.create(new_irm)
        
        return {"status": "success", "image_id": str(irm.idImage)}

    def add_image_metadata(self, dossier_id: str, data: dict) -> str:
        new_irm = ImageIRM(
            dossier_id=dossier_id,
            format=data.get('format', 'MRI'),
            cheminStockage=data.get('url'),
            qualiteOK=True
        )
        irm = self.irm_repo.create(new_irm)
        return str(irm.idImage)

    def request_mri(self, data: dict) -> dict:
        # Simulate an MRI request
        patient_id = data.get('patientId')
        priority = data.get('priority', 'NORMAL')
        notes = data.get('notes', '')
        
        return {
            "status": "pending",
            "patientId": patient_id,
            "requestId": f"REQ-{int(datetime.utcnow().timestamp())}",
            "message": "MRI request successfully simulated."
        }

    def upload_mri(self, patient_id: str, file) -> str:
        dossier = self._get_or_create_dossier(patient_id)
        
        filename = secure_filename(file.filename)
        timestamp = int(datetime.utcnow().timestamp())
        unique_filename = f"{patient_id}_{timestamp}_{filename}"
        
        file_path = os.path.join(self.upload_folder, unique_filename)
        file.save(file_path)

        new_irm = ImageIRM(
            dossier_id=dossier.idDossier,
            format='FILE',
            cheminStockage=file_path,
            qualiteOK=True
        )
        irm = self.irm_repo.create(new_irm)
        return str(irm.idImage)

    def get_patient_mri(self, patient_id: str) -> list:
        # Get dossiers for patient
        dossiers = db.session.query(DossierPatient).filter_by(patient_id=patient_id).all()
        dossier_ids = [d.idDossier for d in dossiers]
        
        images = db.session.query(ImageIRM).filter(ImageIRM.dossier_id.in_(dossier_ids)).all()
        
        return [{
            "id": img.idImage,
            "format": img.format,
            "path": img.cheminStockage,
            "date": str(img.dateAcquisition),
            "quality_ok": img.qualiteOK
        } for img in images]
