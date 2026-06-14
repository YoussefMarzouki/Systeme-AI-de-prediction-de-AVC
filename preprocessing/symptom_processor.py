"""
symptom_processor.py
====================
Two processors are provided:

* ``SymptomProcessor``    – legacy sklearn pipeline (kept for backward compat /
                            image-fusion workflow).
* ``RAGSymptomProcessor`` – new processor that converts a structured symptom
                            dict or free text into a natural-language French
                            description ready to be sent to the Groq RAG engine.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer


# ---------------------------------------------------------------------------
# New: RAG-aware processor
# ---------------------------------------------------------------------------

class RAGSymptomProcessor:
    """
    Convert a symptom dictionary (or plain string) into a natural-language
    French description that the SymptomRAG engine can evaluate.

    Accepted symptom keys (all optional):
        age, gender/sexe, onset/debut (when symptoms started),
        face/visage, arm/bras, speech/parole, vision, balance/equilibre,
        headache/cephalee, hypertension, heart_disease/cardiopathie,
        diabetes/diabete, smoking/tabac, other/autre, free_text

    If ``free_text`` is supplied, it is appended verbatim after the structured
    description.
    """

    # Mapping of English/mixed keys → French label used in the description
    _LABELS = {
        "age":           "Âge",
        "gender":        "Sexe",
        "sexe":          "Sexe",
        "onset":         "Début des symptômes",
        "debut":         "Début des symptômes",
        "face":          "Visage (déviation/asymétrie)",
        "visage":        "Visage (déviation/asymétrie)",
        "arm":           "Bras/jambe (faiblesse)",
        "bras":          "Bras/jambe (faiblesse)",
        "speech":        "Parole (difficulté à parler/comprendre)",
        "parole":        "Parole (difficulté à parler/comprendre)",
        "vision":        "Vision",
        "balance":       "Équilibre/vertiges",
        "equilibre":     "Équilibre/vertiges",
        "headache":      "Céphalée brutale inhabituelle",
        "cephalee":      "Céphalée brutale inhabituelle",
        "hypertension":  "Hypertension (HTA)",
        "heart_disease": "Cardiopathie",
        "cardiopathie":  "Cardiopathie",
        "diabetes":      "Diabète",
        "diabete":       "Diabète",
        "smoking":       "Tabac",
        "tabac":         "Tabac",
        "cholesterol":   "Cholestérol",
        "avg_glucose_level": "Glycémie moyenne",
        "bmi":           "IMC",
        "other":         "Autres symptômes",
        "autre":         "Autres symptômes",
    }

    def to_text(self, symptoms: "dict | str") -> str:
        """
        Convert *symptoms* to a natural-language description.

        Parameters
        ----------
        symptoms : dict | str
            Structured dict or already-formatted free text.

        Returns
        -------
        str
            French natural-language description.
        """
        if isinstance(symptoms, str):
            return symptoms.strip()

        lines: list[str] = ["Description des symptômes du patient :"]

        free_text = symptoms.pop("free_text", None) if isinstance(symptoms, dict) else None

        for key, value in symptoms.items():
            if value is None or str(value).strip() == "":
                continue
            label = self._LABELS.get(key.lower(), key)
            lines.append(f"  - {label} : {value}")

        if free_text:
            lines.append(f"\nInformation complémentaire : {free_text.strip()}")

        return "\n".join(lines)



