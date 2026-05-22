from flask import Blueprint, jsonify
from sqlalchemy import text

from app.core.db import db

system_bp = Blueprint("system", __name__)


@system_bp.route("/api/v1/system/health", methods=["GET"])
def get_system_health():
    """Vérifier le statut de santé du système et de la base de données
    ---
    tags:
      - System
    responses:
      200:
        description: Statut de santé récupéré avec succès
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            health:
              type: object
              properties:
                backend:
                  type: object
                  properties:
                    ok:
                      type: boolean
                    label:
                      type: string
                    state:
                      type: string
                database:
                  type: object
                  properties:
                    ok:
                      type: boolean
                    label:
                      type: string
                    state:
                      type: string
    """
    backend_ok = True
    database_ok = False

    try:
        db.session.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    return jsonify({
        "status": "success",
        "health": {
            "backend": {
                "ok": backend_ok,
                "label": "Online" if backend_ok else "Offline",
                "state": "online" if backend_ok else "offline",
            },
            "database": {
                "ok": database_ok,
                "label": "Connected" if database_ok else "Unavailable",
                "state": "online" if database_ok else "offline",
            },
        }
    }), 200
