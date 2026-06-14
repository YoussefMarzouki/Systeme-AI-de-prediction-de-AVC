#!/usr/bin/env python3
"""
symptom_chat.py
===============
Interactive command-line chatbot for stroke symptom evaluation powered by
LM Studio / Gemini / Groq and the AVC knowledge base (RAG).

Usage
-----
    python symptom_chat.py
    python symptom_chat.py --query "Homme 65 ans..."

Environment
-----------
Can use a local LM Studio server or Gemini / Groq credentials.
The RAG layer can fail over between providers automatically.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Optional explicit LLM API key override.
_DEFAULT_API_KEY = None

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from rag.symptom_rag import SymptomRAG


try:
    import colorama

    colorama.init(autoreset=True)
    _GREEN = colorama.Fore.GREEN
    _CYAN = colorama.Fore.CYAN
    _YELLOW = colorama.Fore.YELLOW
    _RED = colorama.Fore.RED
    _BOLD = colorama.Style.BRIGHT
    _RESET = colorama.Style.RESET_ALL
except ImportError:
    _GREEN = _CYAN = _YELLOW = _RED = _BOLD = _RESET = ""


def _normalize_urgency_label(value: str) -> str:
    text = " ".join(str(value or "").strip().upper().split())
    if "FAIBLE" in text and "SURVEILLANCE" in text:
        return "FAIBLE PROBABILITE MAIS SURVEILLANCE"
    if "RAPIDEMENT" in text or ("EVALUER" in text and "URGENCE" in text):
        return "URGENCE A EVALUER RAPIDEMENT"
    if "IMMEDIATE" in text or "IMM" in text:
        return "URGENCE IMMEDIATE"
    return text or "UNKNOWN"


def _print_banner() -> None:
    print(f"\n{_BOLD}{_CYAN}{'=' * 65}")
    print("   Evaluation des symptomes d'AVC - LM Studio / Cloud RAG")
    print(f"{'=' * 65}{_RESET}")
    print(f"{_YELLOW}Attention: cet outil est educatif uniquement.{_RESET}")
    print(f"{_YELLOW}En cas de doute, appelez le 15 (SAMU) / 112 immediatement.{_RESET}\n")


def _print_urgency_badge(urgency: str) -> None:
    urgency = _normalize_urgency_label(urgency)
    colors = {
        "URGENCE IMMEDIATE": _RED + _BOLD,
        "URGENCE A EVALUER RAPIDEMENT": _YELLOW + _BOLD,
        "FAIBLE PROBABILITE MAIS SURVEILLANCE": _GREEN + _BOLD,
    }
    color = colors.get(urgency, _CYAN + _BOLD)
    print(f"\n{color}[ {urgency} ]{_RESET}\n")


def _print_separator() -> None:
    print(f"{_CYAN}{'-' * 65}{_RESET}")


def run_interactive(rag: SymptomRAG) -> None:
    """Full interactive multi-turn chat loop."""
    _print_banner()
    print(f"{_GREEN}Decrivez les symptomes observes en langage libre.{_RESET}")
    print("Tapez 'reset' pour effacer l'historique de conversation.")
    print("Tapez 'quit' ou 'exit' pour quitter.\n")

    history: list[dict] = []

    while True:
        try:
            user_input = input(f"{_BOLD}Vous > {_RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAu revoir !")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "quitter"):
            print("Au revoir !")
            break

        if user_input.lower() == "reset":
            history = []
            print(f"{_YELLOW}Historique efface. Nouvelle session demarree.{_RESET}\n")
            continue

        try:
            result = rag.evaluate(user_input, conversation_history=history)
        except Exception as exc:
            print(f"{_RED}Erreur lors de la communication avec le modele : {exc}{_RESET}\n")
            continue

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": result["response"]})

        _print_separator()
        _print_urgency_badge(result["urgency"])
        print(result["response"])
        _print_separator()
        tokens = result["usage"].get("total_tokens", "n/a")
        provider = result.get("provider", "unknown")
        model = result.get("model", "unknown")
        print(f"{_CYAN}[provider: {provider} | model: {model} | tokens: {tokens}]{_RESET}\n")


def run_single_query(rag: SymptomRAG, query: str) -> None:
    """Single-shot evaluation."""
    _print_banner()
    print(f"{_BOLD}Requete :{_RESET} {query}\n")

    result = rag.evaluate(query)

    _print_separator()
    _print_urgency_badge(result["urgency"])
    print(result["response"])
    _print_separator()
    tokens = result["usage"].get("total_tokens", "n/a")
    provider = result.get("provider", "unknown")
    model = result.get("model", "unknown")
    print(f"\n{_CYAN}[provider: {provider} | model: {model} | tokens: {tokens}]{_RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluation des symptomes d'AVC via LM Studio / Gemini / Groq (RAG)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-key",
        default=_DEFAULT_API_KEY,
        help="Optional Gemini or Groq API key override",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override for LM Studio, Gemini, or Groq",
    )
    parser.add_argument(
        "--query",
        "-q",
        default=None,
        help="Single symptom description (non-interactive mode)",
    )
    args = parser.parse_args()

    try:
        rag = SymptomRAG(api_key=args.api_key, model=args.model)
    except ValueError as exc:
        print(f"{_RED}Erreur d'initialisation : {exc}{_RESET}", file=sys.stderr)
        sys.exit(1)

    if args.query:
        run_single_query(rag, args.query)
    else:
        run_interactive(rag)


if __name__ == "__main__":
    main()
