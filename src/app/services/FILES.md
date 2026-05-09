# Service Files

Angular services call the backend API and store lightweight client state.

## Files

- `state.service.ts` - Stores selected patient/dossier IDs and mock role/user headers.
- `patient.service.ts` - Calls patient create/search/check/history API endpoints.
- `dossier.service.ts` - Calls dossier create and evaluated-dashboard endpoints.
- `donnees-cliniques.service.ts` - Calls clinical/symptom data endpoints.
- `image-irm.service.ts` - Calls MRI upload and patient MRI endpoints.
- `prediction.service.ts` - Calls image, symptom, and fused prediction endpoints.
- `rapport.service.ts` - Calls report validation queue, case detail, validate, and reject endpoints.
