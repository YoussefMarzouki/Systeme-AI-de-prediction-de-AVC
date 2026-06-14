from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.db import db
from app.models.analyses import AnalyseIA, AnalyseSymptomes, EvaluationRisque
from app.models.donnees_cliniques import DonneesCliniques
from app.models.dossier_patient import DossierPatient
from app.models.image_irm import ImageIRM
from app.models.patient import Patient
from app.models.rapport import Rapport
from app.models.user import Medecin
from app.repositories.rapport_repository import RapportRepository


class RapportService:
    PENDING_STATUSES = ["GENERATED", "UPDATED", "PENDING_VALIDATION"]
    STATUS_MAP = {
        "PENDING_VALIDATION": PENDING_STATUSES,
        "VALIDATED": ["VALIDATED"],
        "REJECTED": ["REJECTED"],
    }

    def __init__(self, rapport_repo: RapportRepository):
        self.rapport_repo = rapport_repo

    def _serialize_rapport(self, rapport: Rapport) -> dict[str, Any]:
        content = self._content_dict(rapport)
        return {
            "idRapport": rapport.idRapport,
            "dateGeneration": str(rapport.dateGeneration) if rapport.dateGeneration else None,
            "dateModification": str(rapport.dateModification) if rapport.dateModification else None,
            "statut": rapport.statut,
            "cheminFichier": rapport.cheminFichier,
            "contenu": rapport.contenu,
            "medecin_id": rapport.medecin_id,
            "modifie_par_id": rapport.modifie_par_id,
            "dossier_id": rapport.dossier_id,
            "version_type": content.get("version_type"),
            "version_number": content.get("version_number"),
            "previous_rapport_id": content.get("previous_rapport_id"),
        }

    def list_rapports(self) -> list[dict[str, Any]]:
        return [self._serialize_rapport(rapport) for rapport in self.rapport_repo.list_all()]

    def create_rapport(self, data: dict[str, Any]) -> str:
        content = data.get("contenu")
        if isinstance(content, dict):
            content = dict(content)
        else:
            content = {}
        content.setdefault("version_type", "ORIGINAL_AI")
        content.setdefault("version_number", 1)
        content.setdefault("validation_status", "UNVALIDATED")

        rapport = Rapport(
            statut=data.get("statut", "GENERATED"),
            cheminFichier=data.get("cheminFichier"),
            contenu=content,
            medecin_id=data["medecin_id"],
            modifie_par_id=data.get("modifie_par_id"),
            dossier_id=data["dossier_id"],
        )
        saved = self.rapport_repo.create(rapport)
        return saved.idRapport

    def get_rapport(self, rapport_id: str) -> dict[str, Any]:
        rapport = self.rapport_repo.get_by_id(rapport_id)
        if not rapport:
            raise Exception("Rapport introuvable")
        return self._serialize_rapport(rapport)

    def get_rapports_by_patient(self, patient_id: str) -> list[dict[str, Any]]:
        patient = Patient.query.get(patient_id)
        if not patient:
            raise Exception("Patient introuvable")

        dossiers = DossierPatient.query.filter_by(patient_id=patient_id).all()
        dossier_ids = [dossier.idDossier for dossier in dossiers]
        rapports = self.rapport_repo.list_by_dossier_ids(dossier_ids)
        return [self._serialize_rapport(rapport) for rapport in rapports]

    def update_rapport(self, rapport_id: str, data: dict[str, Any]) -> dict[str, Any]:
        rapport = self.rapport_repo.get_by_id(rapport_id)
        if not rapport:
            raise Exception("Rapport introuvable")

        if "statut" in data:
            rapport.statut = data["statut"]
        if "cheminFichier" in data:
            rapport.cheminFichier = data["cheminFichier"]
        if "contenu" in data:
            rapport.contenu = data["contenu"]
        if "medecin_id" in data:
            rapport.medecin_id = data["medecin_id"]
        if "modifie_par_id" in data:
            rapport.modifie_par_id = data["modifie_par_id"]
        if "dossier_id" in data:
            rapport.dossier_id = data["dossier_id"]

        self.rapport_repo.update()
        return self._serialize_rapport(rapport)

    def delete_rapport(self, rapport_id: str) -> None:
        rapport = self.rapport_repo.get_by_id(rapport_id)
        if not rapport:
            raise Exception("Rapport introuvable")
        self.rapport_repo.delete(rapport)

    def get_validation_queue(self, status: str = "PENDING_VALIDATION") -> list[dict[str, Any]]:
        statuses = self.STATUS_MAP.get(status, self.PENDING_STATUSES)
        rapports = self.rapport_repo.list_by_statuses(statuses)
        return [self._build_queue_case(rapport) for rapport in rapports]

    def get_case_detail(self, dossier_id: str) -> dict[str, Any]:
        rapport = self.rapport_repo.get_pending_by_dossier(dossier_id, self.PENDING_STATUSES)
        if not rapport:
            rapport = self.rapport_repo.get_by_dossier(dossier_id)
        if not rapport:
            raise Exception("Rapport introuvable pour ce dossier")

        dossier = DossierPatient.query.get(dossier_id)
        if not dossier:
            raise Exception("Dossier introuvable")

        patient = Patient.query.get(dossier.patient_id)
        if not patient:
            raise Exception("Patient introuvable")

        image_urls = [
            img.cheminStockage
            for img in ImageIRM.query.filter_by(dossier_id=dossier_id)
            .order_by(ImageIRM.dateAcquisition.desc())
            .all()
            if img.cheminStockage
        ]
        donnees = (
            DonneesCliniques.query.filter_by(dossier_id=dossier_id)
            .order_by(DonneesCliniques.dateSaisie.desc())
            .first()
        )
        scores = self._get_scores(dossier_id, rapport)
        comments = self._get_comments(dossier_id)
        content = self._content_dict(rapport)

        ai_assessment = (
            content.get("ai_assessment")
            or content.get("symptom_response")
            or content.get("response")
            or self._clinical_fallback_assessment(donnees, scores["symptom_probability"])
        )

        return {
            "rapport_id": rapport.idRapport,
            "dossier_id": dossier.idDossier,
            "rapport_status": rapport.statut,
            "patient_id": patient.id,
            "patient_name": f"{patient.prenom} {patient.nom}",
            "patient_cin": patient.cin,
            "patient_gender": patient.sexe,
            "patient_age": patient.age,
            "risk_level": scores["risk_level"],
            "predicted_class": scores["predicted_class"],
            "confidence_score": self._as_percent(scores["confidence"]),
            "ai_irm_score": self._as_percent(scores["image_probability"]),
            "ai_symptom_score": self._as_percent(scores["symptom_probability"]),
            "ai_probability_score": scores["fused_probability"],
            "fused_score": self._as_percent(scores["fused_probability"]),
            "ai_assessment": ai_assessment,
            "clinical_data": {
                "fast": donnees.fast if donnees else None,
                "tension": donnees.tension if donnees else None,
                "notes": donnees.notes if donnees else None,
                "age": donnees.age if donnees else None,
            },
            "image_urls": image_urls,
            "total_slices": len(image_urls),
            "comments": comments,
            "contenu": rapport.contenu,
            "date_generation": str(rapport.dateGeneration) if rapport.dateGeneration else None,
            "date_modification": str(rapport.dateModification) if rapport.dateModification else None,
            "modifie_par_id": rapport.modifie_par_id,
            "version_type": content.get("version_type"),
            "version_number": content.get("version_number"),
            "previous_rapport_id": content.get("previous_rapport_id"),
        }

    def validate_rapport(self, rapport_id: str, specialist_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        rapport = self.rapport_repo.get_by_id(rapport_id)
        if not rapport:
            raise Exception("Rapport introuvable")

        content = self._content_dict(rapport)
        original_content = dict(content)
        original_content.setdefault("version_type", "ORIGINAL_AI")
        original_content.setdefault("version_number", 1)
        original_content.setdefault("validation_status", "UNVALIDATED")

        if payload.get("predicted_class"):
            content["predicted_class"] = payload.get("predicted_class")
        if payload.get("ai_assessment") is not None:
            content["ai_assessment"] = payload.get("ai_assessment")
        if payload.get("notes"):
            content["specialist_notes"] = payload.get("notes")

        content["validation_status"] = "VALIDATED"
        content["validated_at"] = datetime.utcnow().isoformat()
        content["validated_by"] = specialist_id
        content["version_type"] = "SPECIALIST_REVIEW"
        content["version_number"] = 2
        content["previous_rapport_id"] = rapport.idRapport

        rapport.contenu = original_content
        rapport.statut = "UNVALIDATED"

        reviewed = Rapport(
            statut="VALIDATED",
            cheminFichier=rapport.cheminFichier,
            contenu=content,
            commentaire=payload.get("notes"),
            medecin_id=rapport.medecin_id,
            modifie_par_id=specialist_id,
            dossier_id=rapport.dossier_id,
        )
        db.session.add(reviewed)

        # Update dossier status as well
        dossier = DossierPatient.query.get(rapport.dossier_id)
        if dossier:
            dossier.statut = "VALIDATED"

        db.session.commit()
        return {
            "original_rapport_id": rapport.idRapport,
            "rapport_id": reviewed.idRapport,
            "statut": reviewed.statut,
            "previous_statut": rapport.statut,
        }

    def reject_rapport(self, rapport_id: str, specialist_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        rapport = self.rapport_repo.get_by_id(rapport_id)
        if not rapport:
            raise Exception("Rapport introuvable")

        content = self._content_dict(rapport)
        original_content = dict(content)
        original_content.setdefault("version_type", "ORIGINAL_AI")
        original_content.setdefault("version_number", 1)
        original_content.setdefault("validation_status", "UNVALIDATED")

        if payload.get("notes"):
            content["rejection_notes"] = payload.get("notes")
        content["validation_status"] = "REJECTED"
        content["rejected_at"] = datetime.utcnow().isoformat()
        content["rejected_by"] = specialist_id
        content["version_type"] = "SPECIALIST_REVIEW"
        content["version_number"] = 2
        content["previous_rapport_id"] = rapport.idRapport

        rapport.contenu = original_content
        rapport.statut = "UNVALIDATED"

        reviewed = Rapport(
            statut="REJECTED",
            cheminFichier=rapport.cheminFichier,
            contenu=content,
            commentaire=payload.get("notes"),
            medecin_id=rapport.medecin_id,
            modifie_par_id=specialist_id,
            dossier_id=rapport.dossier_id,
        )
        db.session.add(reviewed)

        # Update dossier status as well
        dossier = DossierPatient.query.get(rapport.dossier_id)
        if dossier:
            dossier.statut = "REJECTED"

        db.session.commit()
        return {
            "original_rapport_id": rapport.idRapport,
            "rapport_id": reviewed.idRapport,
            "statut": reviewed.statut,
            "previous_statut": rapport.statut,
        }

    def _build_queue_case(self, rapport: Rapport) -> dict[str, Any]:
        dossier = DossierPatient.query.get(rapport.dossier_id)
        patient = Patient.query.get(dossier.patient_id) if dossier else None
        donnees = (
            DonneesCliniques.query.filter_by(dossier_id=rapport.dossier_id)
            .order_by(DonneesCliniques.dateSaisie.desc())
            .first()
        )
        image_count = ImageIRM.query.filter_by(dossier_id=rapport.dossier_id).count()
        scores = self._get_scores(rapport.dossier_id, rapport)

        patient_name = f"{patient.prenom} {patient.nom}" if patient else "Patient inconnu"
        return {
            "rapport_id": rapport.idRapport,
            "dossier_id": rapport.dossier_id,
            "patient_id": patient.id if patient else None,
            "patient_name": patient_name,
            "patient_initials": self._initials(patient_name),
            "patient_gender": patient.sexe if patient else "N/A",
            "patient_age": patient.age if patient else None,
            "modality": "IRM + Symptomes" if image_count and donnees else ("IRM" if image_count else "Symptomes"),
            "ai_irm_score": self._as_percent(scores["image_probability"]),
            "ai_symptom_score": self._as_percent(scores["symptom_probability"]),
            "ai_probability_score": scores["fused_probability"],
            "fused_score": self._as_percent(scores["fused_probability"]),
            "time_since_onset": self._extract_onset(donnees.notes if donnees else None),
            "risk_level": scores["risk_level"],
            "status": self._ui_status(scores["risk_level"]),
            "rapport_status": rapport.statut,

            "date_generation": str(rapport.dateGeneration) if rapport.dateGeneration else None,
        }

    def _get_scores(self, dossier_id: str, rapport: Rapport) -> dict[str, Any]:
        content = self._content_dict(rapport)
        eval_risque = EvaluationRisque.query.filter_by(dossier_id=dossier_id).first()

        image = (
            ImageIRM.query.filter_by(dossier_id=dossier_id)
            .order_by(ImageIRM.dateAcquisition.desc())
            .first()
        )
        analyse_ia = AnalyseIA.query.filter_by(image_id=image.idImage).first() if image else None

        donnees = (
            DonneesCliniques.query.filter_by(dossier_id=dossier_id)
            .order_by(DonneesCliniques.dateSaisie.desc())
            .first()
        )
        analyse_symptomes = (
            AnalyseSymptomes.query.filter_by(donnees_cliniques_id=donnees.id).first()
            if donnees
            else None
        )

        image_probability = self._first_number(
            content.get("image_probability"),
            content.get("probability") if content.get("predicted_class") else None,
            analyse_ia.probabiliteAVC if analyse_ia else None,
        )
        symptom_probability = self._first_number(
            content.get("symptom_probability"),
            analyse_symptomes.valeur if analyse_symptomes else None,
        )
        fused_probability = self._first_number(
            content.get("fused_probability"),
            eval_risque.scoreGlobal if eval_risque else None,
            self._weighted_score(image_probability, symptom_probability),
        )
        confidence = self._first_number(
            content.get("confidence"),
            analyse_ia.scoreConfiance if analyse_ia else None,
            0.0,
        )

        return {
            "image_probability": image_probability,
            "symptom_probability": symptom_probability,
            "fused_probability": fused_probability,
            "confidence": confidence,
            "risk_level": content.get("risk_level") or (eval_risque.niveau if eval_risque else "UNKNOWN"),
            "predicted_class": content.get("predicted_class") or "N/A",
        }

    def _get_comments(self, dossier_id: str) -> list[dict[str, Any]]:
        rapports = (
            Rapport.query.filter(
                Rapport.dossier_id == dossier_id,
                Rapport.commentaire.isnot(None),
                Rapport.commentaire != "",
            )
            .order_by(Rapport.dateGeneration.desc())
            .all()
        )
        return [
            {
                "id": r.idRapport,
                "texte": r.commentaire,
                "date": str(r.dateGeneration) if r.dateGeneration else None,
                "medecin_id": r.modifie_par_id or r.medecin_id,
            }
            for r in rapports
        ]

    def _content_dict(self, rapport: Rapport) -> dict[str, Any]:
        if isinstance(rapport.contenu, dict):
            return dict(rapport.contenu)
        if isinstance(rapport.contenu, str):
            try:
                parsed = json.loads(rapport.contenu)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    def _first_number(self, *values: Any) -> float | None:
        for value in values:
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _weighted_score(self, image_probability: float | None, symptom_probability: float | None) -> float | None:
        if image_probability is not None and symptom_probability is not None:
            return (0.7 * image_probability) + (0.3 * symptom_probability)
        return image_probability if image_probability is not None else symptom_probability

    def _as_percent(self, value: float | None) -> int | None:
        if value is None:
            return None
        if value <= 1:
            value = value * 100
        return int(round(value))

    def _initials(self, name: str) -> str:
        parts = [part for part in name.split(" ") if part]
        return "".join(part[0] for part in parts[:2]).upper() or "NA"

    def _ui_status(self, risk_level: str | None) -> str:
        normalized = (risk_level or "UNKNOWN").upper()
        if normalized == "VERY_HIGH":
            return "very-high-risk"
        if normalized == "HIGH":
            return "high-risk"
        if normalized == "MEDIUM":
            return "medium"
        return "low"

    def _extract_onset(self, notes: str | None) -> str:
        if not notes:
            return "N/A"
        for marker in ("Début des symptômes :", "Symptom onset time:"):
            if marker in notes:
                part = notes.split(marker, 1)[1].strip()
                if " | " in part:
                    part = part.split(" | ", 1)[0].strip()
                return part
        return "N/A"


    def _clinical_fallback_assessment(
        self,
        donnees: DonneesCliniques | None,
        symptom_probability: float | None,
    ) -> str:
        if not donnees:
            return "Aucune evaluation textuelle disponible."

        parts = ["Analyse des symptomes enregistree dans les donnees cliniques."]
        if donnees.fast:
            parts.append(f"Symptomes rapportes: {donnees.fast}.")
        if donnees.tension:
            parts.append(f"Tension arterielle: {donnees.tension}.")
        if symptom_probability is not None:
            parts.append(f"Score symptomes: {self._as_percent(symptom_probability)}%.")
        if donnees.notes:
            parts.append(f"Notes cliniques: {donnees.notes}")
        return " ".join(parts)
