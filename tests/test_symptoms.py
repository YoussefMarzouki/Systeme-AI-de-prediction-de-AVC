#!/usr/bin/env python3
"""
test_symptoms.py
================
Tests for the RAG-powered symptom evaluation system.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models.symptom_classifier import GroqSymptomClassifier
from preprocessing.symptom_processor import RAGSymptomProcessor


def _integration_api_key() -> str:
    return Config.GEMINI_API_KEY or Config.GROQ_API_KEY


# ---------------------------------------------------------------------------
# RAGSymptomProcessor unit tests (no network)
# ---------------------------------------------------------------------------

def test_processor_dict() -> None:
    proc = RAGSymptomProcessor()
    text = proc.to_text(
        {
            "age": 68,
            "gender": "homme",
            "face": "bouche deviee",
            "arm": "bras gauche faible",
        }
    )
    assert "68" in text
    assert "Visage" in text
    assert "Bras" in text
    print("PASS  test_processor_dict")


def test_processor_free_text() -> None:
    proc = RAGSymptomProcessor()
    raw = "Homme 50 ans, tete qui tourne, nausees."
    assert proc.to_text(raw) == raw
    print("PASS  test_processor_free_text")


def test_processor_free_text_key() -> None:
    proc = RAGSymptomProcessor()
    text = proc.to_text({"age": 40, "free_text": "Douleur soudaine dans le bras gauche."})
    assert "Douleur soudaine" in text
    print("PASS  test_processor_free_text_key")


# ---------------------------------------------------------------------------
# GroqSymptomClassifier integration tests (requires network + API key)
# ---------------------------------------------------------------------------

def test_evaluate_dict() -> None:
    clf = GroqSymptomClassifier(api_key=_integration_api_key())
    result = clf.evaluate(
        {
            "age": 68,
            "gender": "homme",
            "onset": "il y a 15 min (soudain)",
            "face": "bouche deviee",
            "arm": "bras gauche faible",
            "speech": "parole confuse",
        }
    )
    assert "response" in result
    assert "urgency" in result
    assert "probability" in result
    assert 0.0 <= result["probability"] <= 1.0
    assert result["urgency"] in (
        "URGENCE IMMEDIATE",
        "URGENCE A EVALUER RAPIDEMENT",
        "FAIBLE PROBABILITE MAIS SURVEILLANCE",
        "UNKNOWN",
    )
    print(f"PASS  test_evaluate_dict  [urgency={result['urgency']}]")


def test_evaluate_free_text() -> None:
    clf = GroqSymptomClassifier(api_key=_integration_api_key())
    result = clf.evaluate(
        "Femme 55 ans. Perte soudaine de vision d'un oeil, 45 minutes, antecedent tabac."
    )
    assert len(result["response"]) > 100
    print(f"PASS  test_evaluate_free_text  [urgency={result['urgency']}]")


def test_multi_turn_chat() -> None:
    clf = GroqSymptomClassifier(api_key=_integration_api_key())
    clf.evaluate("Homme 60 ans, vertiges soudains depuis 1 heure.")
    reply = clf.chat("Il a aussi des vomissements et ne tient pas debout.")
    assert len(reply) > 50
    print("PASS  test_multi_turn_chat")


def test_reset_conversation() -> None:
    clf = GroqSymptomClassifier(api_key=_integration_api_key())
    clf.evaluate("Test message.")
    assert len(clf._conversation_history) == 2
    clf.reset_conversation()
    assert clf._conversation_history == []
    print("PASS  test_reset_conversation")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== RAGSymptomProcessor (unit) ===")
    test_processor_dict()
    test_processor_free_text()
    test_processor_free_text_key()

    print("\n=== GroqSymptomClassifier (integration - requires Gemini or Groq API) ===")
    test_evaluate_dict()
    test_evaluate_free_text()
    test_multi_turn_chat()
    test_reset_conversation()

    print("\nAll symptom tests passed.")
