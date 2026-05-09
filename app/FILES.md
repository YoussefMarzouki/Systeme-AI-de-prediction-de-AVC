# Backend App Files

Main Flask application package.

## Files

- `__init__.py` - Creates the Flask app, configures PostgreSQL, registers controllers, initializes Swagger, and calls `db.create_all()`.

## Folders

- `controllers/` - HTTP route handlers.
- `core/` - Shared infrastructure such as the database object.
- `models/` - SQLAlchemy database models.
- `repositories/` - Database access helpers.
- `services/` - Business logic used by controllers.
