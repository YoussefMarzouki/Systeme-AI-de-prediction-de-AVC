from app.core.db import db
from app.models.image_irm import ImageIRM

class ImageIRMRepository:
    def create(self, image: ImageIRM) -> ImageIRM:
        db.session.add(image)
        db.session.commit()
        return image

    def get_by_id(self, image_id: str) -> ImageIRM:
        return ImageIRM.query.get(image_id)

    def update(self) -> None:
        db.session.commit()
