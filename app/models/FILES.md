# Model Files

SQLAlchemy models map Python classes to PostgreSQL tables.

## Files

- `__init__.py` - Imports all model classes so SQLAlchemy can register them.
- `user.py` - Defines `Utilisateur`, `Medecin`, `AgentAccueil`, and `Admin` with single-table inheritance.
- `patient.py` - Defines the patient table and patient identity/medical fields.
- `dossier_patient.py` - Defines medical dossiers linked to patients and creators.
- `donnees_cliniques.py` - Defines symptom/clinical data stored in the `symptomes` table.
- `image_irm.py` - Defines MRI image metadata and storage path records.
- `analyses.py` - Defines AI image analysis, symptom analysis, and global risk evaluation tables.
- `rapport.py` - Defines generated, validated, rejected, and versioned medical reports.
- `commentaire_medical.py` - Defines specialist/general doctor comments linked to a dossier.
