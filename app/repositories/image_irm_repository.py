from app.core.db import db
from app.models.image_irm import ImageIRM

class ImageIRMRepository:
    def list_all(self) -> list[ImageIRM]:
        return ImageIRM.query.order_by(ImageIRM.dateAcquisition.desc()).all()

    def create(self, image: ImageIRM) -> ImageIRM:
        db.session.add(image)
        db.session.commit()
        return image

    def get_by_id(self, image_id: str) -> ImageIRM:
        return ImageIRM.query.get(image_id)

    def update(self) -> None:
        db.session.commit()

    def delete(self, image: ImageIRM) -> None:
        db.session.delete(image)
        db.session.commit()
