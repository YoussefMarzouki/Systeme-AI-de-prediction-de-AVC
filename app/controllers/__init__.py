from .patient_controller import patient_bp
from .dossier_controller import dossier_bp
from .image_irm_controller import image_irm_bp
from .mri_controller import mri_bp
from .prediction_controller import prediction_bp

def register_controllers(app):
    app.register_blueprint(patient_bp)
    app.register_blueprint(dossier_bp)
    app.register_blueprint(image_irm_bp)
    app.register_blueprint(mri_bp)
    app.register_blueprint(prediction_bp)
