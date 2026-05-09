# Service Files

Services contain backend business logic. Controllers should stay thin and call these classes.

## Files

- `__init__.py` - Service package marker.
- `patient_service.py` - Validates and serializes patients, handles create/update/delete/search logic.
- `dossier_service.py` - Handles dossiers, dashboard evaluated records, patient history, and report-version history.
- `donnees_cliniques_service.py` - Handles clinical/symptom entries for dossiers.
- `image_irm_service.py` - Handles MRI upload, metadata, patient MRI lookup, and upload storage paths.
- `prediction_service.py` - Calls the external AI model API for image, symptom, and fused predictions.
- `rapport_service.py` - Handles report creation, queue display, case detail, validation/rejection, comments, scores, and report versions.
