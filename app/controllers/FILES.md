# Controller Files

Controllers define HTTP API routes. They receive requests, call services, and return JSON responses.

## Files

- `__init__.py` - Registers all controller blueprints on the Flask app.
- `patient_controller.py` - Patient CRUD, CIN checks, and patient search endpoints.
- `dossier_controller.py` - Dossier creation, update, delete, evaluated dashboard data, and patient history endpoints.
- `donnees_cliniques_controller.py` - Clinical/symptom data endpoints for dossiers.
- `image_irm_controller.py` - MRI upload, metadata, and patient MRI endpoints.
- `prediction_controller.py` - Prediction endpoints that call image/symptom/fused AI analysis and create report data.
- `rapport_controller.py` - Report CRUD, validation queue, case detail, validate, and reject endpoints.
