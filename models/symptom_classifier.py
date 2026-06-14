"""
symptom_classifier.py
=====================
Two classifiers are provided:

* ``SymptomClassifier``    – legacy sklearn RandomForest kept for backward
                             compatibility and optional fusion pipeline.
* ``GroqSymptomClassifier``– RAG-powered classifier that wraps SymptomRAG
                             and returns both a structured French evaluation and
                             a numeric risk probability extracted from the
                             urgency level (URGENCE IMMÉDIATE → 0.90, etc.).
"""

from __future__ import annotations

from typing import Optional, Union
import joblib
from sklearn.ensemble import RandomForestClassifier


def _normalize_urgency_label(value: str) -> str:
    text = " ".join(str(value or "").strip().upper().split())
    if "FAIBLE" in text and "SURVEILLANCE" in text:
        return "FAIBLE PROBABILITE MAIS SURVEILLANCE"
    if "RAPIDEMENT" in text or ("EVALUER" in text and "URGENCE" in text):
        return "URGENCE A EVALUER RAPIDEMENT"
    if "IMMEDIATE" in text or "IMM" in text:
        return "URGENCE IMMEDIATE"
    return "UNKNOWN"


def _urgency_probability(value: str) -> float:
    normalized = _normalize_urgency_label(value)
    if normalized == "URGENCE IMMEDIATE":
        return 0.92
    if normalized == "URGENCE A EVALUER RAPIDEMENT":
        return 0.65
    if normalized == "FAIBLE PROBABILITE MAIS SURVEILLANCE":
        return 0.20
    return 0.50


# ---------------------------------------------------------------------------
# LLM / RAG-based classifier
# ---------------------------------------------------------------------------

class GroqSymptomClassifier:
    """
    RAG-powered classifier that uses the SymptomRAG engine with Gemini/Groq failover.

    Parameters
    ----------
    api_key : str, optional
        LLM API key. Accepts Gemini or Groq keys.
    model : str
        Preferred model identifier for the selected provider.
    """

    # Urgency → approximate risk probability mapping
    _URGENCY_PROBABILITY = {
        "URGENCE IMMÉDIATE":                  0.92,
        "URGENCE À ÉVALUER RAPIDEMENT":       0.65,
        "FAIBLE PROBABILITÉ MAIS SURVEILLANCE": 0.20,
        "UNKNOWN":                            0.50,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash",
    ):
        # Lazy import to avoid hard dependency when only the legacy model is used
        from rag.symptom_rag import SymptomRAG
        from preprocessing.symptom_processor import RAGSymptomProcessor

        self.rag = SymptomRAG(api_key=api_key, model=model)
        self.processor = RAGSymptomProcessor()
        self._conversation_history: list[dict] = []

    # ------------------------------------------------------------------
    def evaluate(self, symptoms: "dict | str") -> dict:
        """
        Evaluate symptoms and return a rich result dict.

        Parameters
        ----------
        symptoms : dict | str
            Structured symptom dict or free-text description.

        Returns
        -------
        dict:
            ``response``    – full structured French evaluation (str)
            ``urgency``     – urgency level string
            ``probability`` – numeric risk score in [0, 1]
            ``model``       – Gemini model used
            ``usage``       – token usage dict
        """
        text = self.processor.to_text(symptoms)
        result = self.rag.evaluate(text, conversation_history=self._conversation_history)

        # Maintain conversation state for follow-up questions
        self._conversation_history.append({"role": "user",      "content": text})
        self._conversation_history.append({"role": "assistant", "content": result["response"]})

        result["urgency"] = _normalize_urgency_label(result.get("urgency", "UNKNOWN"))
        probability = _urgency_probability(result["urgency"])
        result["probability"] = probability
        return result

    def predict_proba(self, symptoms: "dict | str") -> float:
        """Return numeric risk probability only (for fusion pipeline compat)."""
        return self.evaluate(symptoms)["probability"]

    def reset_conversation(self) -> None:
        """Clear multi-turn history to start a fresh session."""
        self._conversation_history.clear()

    # ------------------------------------------------------------------
    # Stateful chat convenience wrapper
    # ------------------------------------------------------------------

    def chat(self, message: str) -> str:
        """
        Send a follow-up message in an ongoing conversation about symptoms.
        Returns the assistant's reply text.
        """
        reply, self._conversation_history = self.rag.chat(
            self._conversation_history, message
        )
        return reply


# ---------------------------------------------------------------------------
# Legacy: sklearn RandomForest classifier (unchanged, kept for compat)
# ---------------------------------------------------------------------------

class SymptomClassifier:
    """Legacy RandomForest-based symptom classifier (kept for backward compat)."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.feature_importance_ = None

    def fit(self, X, y):
        self.model.fit(X, y)
        self.feature_importance_ = self.model.feature_importances_

    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]

    def save(self, path):
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        return joblib.load(path)
