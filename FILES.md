# Backend Files

Flask backend for the StrokeAI API. It exposes REST endpoints, stores data with SQLAlchemy, and connects the frontend to the AI prediction service.

## Files

- `Dockerfile` - Builds the backend container when using Docker.
- `requirements.txt` - Python dependencies for Flask, SQLAlchemy, PostgreSQL, Swagger, and HTTP requests.
- `run.py` - Starts the Flask app locally.
- `seed.py` - Recreates and fills the database with test users, patients, dossiers, analyses, and rapports.

## Folders

- `app/` - Main Flask application package.
- `uploads/` - Uploaded MRI files saved by the backend.
