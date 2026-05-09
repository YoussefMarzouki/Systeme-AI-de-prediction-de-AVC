from .patient_controller import patient_bp
from .dossier_controller import dossier_bp
from .donnees_cliniques_controller import donnees_cliniques_bp
from .image_irm_controller import image_irm_bp
from .prediction_controller import prediction_bp
from .rapport_controller import rapport_bp
from .auth_controller import auth_bp
from .utilisateur_controller import utilisateur_bp
from .system_controller import system_bp

def register_controllers(app):
    app.register_blueprint(patient_bp)
    app.register_blueprint(dossier_bp)
    app.register_blueprint(donnees_cliniques_bp)
    app.register_blueprint(image_irm_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(rapport_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(utilisateur_bp)
    app.register_blueprint(system_bp)
