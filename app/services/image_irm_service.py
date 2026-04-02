from app.models.image_irm import ImageIRM
from app.repositories.image_irm_repository import ImageIRMRepository

class ImageIRMService:
    def __init__(self, irm_repo: ImageIRMRepository):
        self.irm_repo = irm_repo

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
