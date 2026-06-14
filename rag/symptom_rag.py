from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib import error, request

from loguru import logger

try:
    from config import Config
except Exception:  # pragma: no cover - import path fallback
    Config = None


URGENCY_IMMEDIATE = "URGENCE IMMEDIATE"
URGENCY_RAPID = "URGENCE A EVALUER RAPIDEMENT"
URGENCY_MONITOR = "FAIBLE PROBABILITE MAIS SURVEILLANCE"
URGENCY_UNKNOWN = "UNKNOWN"


class SymptomRAG:
    """Educational stroke triage assistant with LM Studio, Gemini, and Groq providers."""

    _LMSTUDIO_MODEL_PREFERENCES = (
        "microsoft/phi-4-mini-reasoning",
        "nvidia/nemotron-3-nano-4b",
        "deepseek/deepseek-r1-0528-qwen3-8b",
        "qwen/qwen3.5-9b",
        "essentialai/rnj-1",
    )

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._requested_api_key = (api_key or "").strip() or None
        self._requested_model = (model or "").strip() or None
        self.api_key: str | None = None
        self.model: str | None = None
        self.provider: str | None = None
        self._clients: dict[str, dict[str, Any]] = {}
        self._lmstudio_model_cache: str | None = None
        self._context_blob = self._build_context_blob()
        self._system_instruction = self._build_system_instruction()
        self._provider_order = self._build_provider_order()
        if not self._provider_order:
            raise ValueError("LM Studio, Gemini, or Groq must be configured.")

    def evaluate(self, text: str, conversation_history: list[dict] | None = None) -> dict[str, Any]:
        prompt = self._build_prompt(text=text, conversation_history=conversation_history or [])
        last_exc: Exception | None = None

        for index, provider_cfg in enumerate(self._provider_order):
            try:
                response = self._generate_with_provider(provider_cfg, prompt)
                response_text = self._sanitize_response_text(self._extract_text(response)).strip()
                if not response_text:
                    raise RuntimeError(f"{provider_cfg['name']} returned an empty response.")

                self.api_key = provider_cfg.get("api_key") or None
                self.model = provider_cfg["model"]
                self.provider = provider_cfg["name"]

                urgency = self._extract_urgency(response_text)
                return {
                    "response": response_text,
                    "urgency": urgency,
                    "model": self.model,
                    "provider": self.provider,
                    "usage": self._extract_usage(response),
                }
            except Exception as exc:
                last_exc = exc
                has_next = index < len(self._provider_order) - 1
                if has_next:
                    next_provider = self._provider_order[index + 1]["name"]
                    logger.warning(
                        f"{provider_cfg['name']} unavailable, trying {next_provider}: {exc}"
                    )
                else:
                    logger.warning(f"{provider_cfg['name']} unavailable, using local fallback: {exc}")

        return self._evaluate_locally(text, last_exc or RuntimeError("No LLM provider available."))

    def chat(self, history: list[dict], message: str) -> tuple[str, list[dict]]:
        result = self.evaluate(message, conversation_history=history)
        new_history = list(history)
        new_history.append({"role": "user", "content": message})
        new_history.append({"role": "assistant", "content": result["response"]})
        return result["response"], new_history

    def _build_provider_order(self) -> list[dict[str, str]]:
        order: list[dict[str, str]] = []
        explicit_provider = self._detect_provider(
            api_key=self._requested_api_key,
            model=self._requested_model,
        )

        if explicit_provider == "lmstudio":
            self._append_provider(order, "lmstudio", None, self._requested_model)
            self._append_provider(order, "gemini", self._gemini_api_key(), None)
            self._append_provider(order, "groq", self._groq_api_key(), None)
            return order

        if explicit_provider == "groq":
            self._append_provider(order, "groq", self._requested_api_key, self._requested_model)
            self._append_provider(order, "lmstudio", None, None)
            self._append_provider(order, "gemini", self._gemini_api_key(), None)
            return order

        if explicit_provider == "gemini":
            self._append_provider(order, "gemini", self._requested_api_key, self._requested_model)
            self._append_provider(order, "lmstudio", None, None)
            self._append_provider(order, "groq", self._groq_api_key(), None)
            return order

        self._append_provider(order, "lmstudio", None, self._requested_model)
        self._append_provider(order, "gemini", self._gemini_api_key(), None)
        self._append_provider(order, "groq", self._groq_api_key(), None)
        return order

    def _append_provider(
        self,
        order: list[dict[str, str]],
        name: str,
        api_key: str | None,
        model_hint: str | None,
    ) -> None:
        if name == "lmstudio":
            base_url = self._lmstudio_base_url()
            if not base_url:
                return

            model = self._resolve_model(name, model_hint)
            candidate = {
                "name": name,
                "api_key": "",
                "model": model,
                "base_url": base_url,
            }
            if candidate not in order:
                order.append(candidate)
            return

        key = (api_key or "").strip()
        if not key:
            return

        model = self._resolve_model(name, model_hint)
        candidate = {
            "name": name,
            "api_key": key,
            "model": model,
        }
        if candidate not in order:
            order.append(candidate)

    def _detect_provider(self, api_key: str | None, model: str | None) -> str | None:
        if api_key:
            return "groq" if api_key.startswith("gsk_") else "gemini"

        if model and self._is_gemini_model(model):
            return "gemini"

        if model and self._lmstudio_base_url():
            return "lmstudio"

        if model and self._is_groq_model(model):
            return "groq"

        return None

    def _resolve_model(self, provider: str, requested_model: str | None) -> str:
        if provider == "lmstudio":
            if requested_model:
                return requested_model
            configured = self._config_value("LM_STUDIO_MODEL")
            return configured or "auto"

        if provider == "groq":
            if requested_model:
                return requested_model
            configured = self._config_value("GROQ_MODEL")
            return configured or "llama-3.1-8b-instant"

        if requested_model:
            return requested_model
        configured = self._config_value("GEMINI_MODEL")
        return configured or "gemini-2.0-flash"

    def _is_gemini_model(self, model: str | None) -> bool:
        return bool(model and "gemini" in model.lower())

    def _is_groq_model(self, model: str | None) -> bool:
        if not model:
            return False
        normalized = model.lower()
        groq_prefixes = ("llama", "mixtral", "gemma", "deepseek", "qwen", "mistral")
        return normalized.startswith(groq_prefixes)

    def _gemini_api_key(self) -> str | None:
        return os.environ.get("GEMINI_API_KEY") or self._config_value("GEMINI_API_KEY")

    def _groq_api_key(self) -> str | None:
        return os.environ.get("GROQ_API_KEY") or self._config_value("GROQ_API_KEY")

    def _lmstudio_base_url(self) -> str | None:
        raw = os.environ.get("LM_STUDIO_BASE_URL") or self._config_value("LM_STUDIO_BASE_URL")
        if not raw:
            return None

        base = str(raw).strip().rstrip("/")
        for suffix in ("/models", "/chat/completions", "/completions"):
            if base.lower().endswith(suffix):
                base = base[: -len(suffix)]
                break

        if base.endswith("/v1") or base.endswith("/api/v1"):
            return base
        if base.endswith("/api"):
            return f"{base}/v1"
        return f"{base}/v1"

    def _lmstudio_timeout(self) -> int:
        configured = self._config_value("LM_STUDIO_TIMEOUT")
        try:
            return max(5, int(configured or 60))
        except ValueError:
            return 60

    def _config_value(self, attribute: str) -> str | None:
        if Config is None:
            return None
        value = getattr(Config, attribute, None)
        if value is None:
            return None
        return str(value).strip()

    def _get_or_create_client(self, provider_cfg: dict[str, str]) -> dict[str, Any]:
        cached = self._clients.get(provider_cfg["name"])
        if cached is not None:
            return cached

        if provider_cfg["name"] == "lmstudio":
            cached = {
                "backend": "lmstudio",
                "base_url": provider_cfg["base_url"],
                "timeout": self._lmstudio_timeout(),
            }
            self._clients[provider_cfg["name"]] = cached
            return cached

        if provider_cfg["name"] == "groq":
            try:
                from groq import Groq
            except Exception as exc:
                raise ValueError("The groq package is not available in this environment.") from exc

            cached = {"backend": "groq", "client": Groq(api_key=provider_cfg["api_key"])}
            self._clients[provider_cfg["name"]] = cached
            return cached

        try:
            from google import genai

            cached = {
                "backend": "google.genai",
                "client": genai.Client(api_key=provider_cfg["api_key"]),
            }
            self._clients[provider_cfg["name"]] = cached
            return cached
        except Exception as exc:
            logger.debug(f"google.genai unavailable: {exc}")

        try:
            import google.generativeai as legacy_genai

            legacy_genai.configure(api_key=provider_cfg["api_key"])
            cached = {
                "backend": "google.generativeai",
                "client": legacy_genai.GenerativeModel(
                    provider_cfg["model"],
                    system_instruction=self._system_instruction,
                ),
            }
            self._clients[provider_cfg["name"]] = cached
            return cached
        except Exception as exc:
            raise ValueError(
                "Neither google.genai nor google.generativeai is available in this environment."
            ) from exc

    def _generate_with_provider(self, provider_cfg: dict[str, str], prompt: str) -> Any:
        client_state = self._get_or_create_client(provider_cfg)
        backend = client_state["backend"]

        if backend == "lmstudio":
            provider_cfg["model"] = self._resolve_lmstudio_model(client_state["base_url"], provider_cfg["model"])
            return self._lmstudio_chat_completion(
                base_url=client_state["base_url"],
                model=provider_cfg["model"],
                prompt=prompt,
                timeout=client_state["timeout"],
            )

        if backend == "groq":
            client = client_state["client"]
            return client.chat.completions.create(
                model=provider_cfg["model"],
                messages=[
                    {"role": "system", "content": self._system_instruction},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )

        if backend == "google.genai":
            client = client_state["client"]
            return client.models.generate_content(
                model=provider_cfg["model"],
                contents=prompt,
                config={
                    "system_instruction": self._system_instruction,
                    "temperature": 0.2,
                },
            )

        if backend == "google.generativeai":
            client = client_state["client"]
            return client.generate_content(
                prompt,
                generation_config={"temperature": 0.2},
            )

        raise RuntimeError(f"Unsupported provider backend: {backend}")

    def _resolve_lmstudio_model(self, base_url: str, configured_model: str) -> str:
        if configured_model and configured_model.lower() != "auto":
            return configured_model

        if self._lmstudio_model_cache:
            return self._lmstudio_model_cache

        payload = self._lmstudio_json_request(
            method="GET",
            base_url=base_url,
            path="models",
            timeout=self._lmstudio_timeout(),
        )
        model = self._pick_lmstudio_model(payload)
        if not model:
            raise RuntimeError("LM Studio did not return any usable LLM models.")

        self._lmstudio_model_cache = model
        return model

    def _pick_lmstudio_model(self, payload: dict[str, Any]) -> str | None:
        records: list[dict[str, Any]] = []
        for item in payload.get("data", []) or payload.get("models", []):
            model_id = item.get("id") or item.get("key") or item.get("selected_variant")
            if not model_id:
                continue
            if item.get("type") == "embedding":
                continue

            records.append(
                {
                    "id": str(model_id),
                    "loaded": bool(item.get("loaded_instances")),
                }
            )

        if not records:
            return None

        for record in records:
            if record["loaded"]:
                return record["id"]

        available = {record["id"] for record in records}
        for preferred in self._LMSTUDIO_MODEL_PREFERENCES:
            if preferred in available:
                return preferred

        for record in records:
            lower_id = record["id"].lower()
            if "instruct" in lower_id or "reason" in lower_id or "chat" in lower_id:
                return record["id"]

        return records[0]["id"]

    def _lmstudio_chat_completion(
        self,
        base_url: str,
        model: str,
        prompt: str,
        timeout: int,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        return self._lmstudio_json_request(
            method="POST",
            base_url=base_url,
            path="chat/completions",
            payload=payload,
            timeout=timeout,
        )

    def _lmstudio_json_request(
        self,
        method: str,
        base_url: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        last_exc: Exception | None = None
        for candidate_url in self._lmstudio_candidate_urls(base_url, path):
            try:
                return self._http_json(
                    method=method,
                    url=candidate_url,
                    payload=payload,
                    timeout=timeout,
                )
            except Exception as exc:
                last_exc = exc
        raise RuntimeError(str(last_exc or "LM Studio request failed."))

    def _lmstudio_candidate_urls(self, base_url: str, path: str) -> list[str]:
        normalized_base = base_url.rstrip("/")
        normalized_path = path.lstrip("/")
        candidates = [f"{normalized_base}/{normalized_path}"]

        alternate_base = None
        if normalized_base.endswith("/api/v1"):
            alternate_base = normalized_base[: -len("/api/v1")] + "/v1"
        elif normalized_base.endswith("/v1"):
            alternate_base = normalized_base[: -len("/v1")] + "/api/v1"

        if alternate_base:
            alternate_url = f"{alternate_base}/{normalized_path}"
            if alternate_url not in candidates:
                candidates.append(alternate_url)

        return candidates

    def _http_json(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, data=data, method=method.upper(), headers=headers)
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {url}: {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Unable to reach {url}: {exc.reason}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON response from {url}.") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError(f"Unexpected response shape from {url}.")
        return parsed

    def _build_prompt(self, text: str, conversation_history: list[dict]) -> str:
        history_lines: list[str] = []
        for item in conversation_history[-6:]:
            role = str(item.get("role", "user")).upper()
            content = str(item.get("content", "")).strip()
            if content:
                history_lines.append(f"{role}: {content}")

        history_block = "\n".join(history_lines) if history_lines else "(no prior conversation)"

        return (
            "Contexte documentaire local (Tunisie):\n"
            f"{self._context_blob}\n\n"
            "Historique recent:\n"
            f"{history_block}\n\n"
            "Nouvelle demande patient:\n"
            f"{text.strip()}\n\n"
            "INSTRUCTIONS DE RÉPONSE OBLIGATOIRES :\n"
            "1. Tu DOIS impérativement utiliser le modèle de réponse structurée fourni ci-dessus sous le nom '[AVC_RAG_Answer_Template_FR.docx.txt]'. Ne change pas sa structure, ses séparateurs ou ses titres.\n"
            "2. Remplis les champs vides (représentés par des tirets bas comme '_____' ou '[HH:MM]') avec les informations cliniques extraites de la demande patient et de l'historique.\n"
            "3. Conserve la mise en page exacte du modèle, y compris le grand titre du début et les lignes de séparation.\n"
            "4. Reste extrêmement concis et ne rajoute aucun commentaire d'introduction ou de conclusion en dehors du modèle.\n"
            "5. Pour le champ 'Niveau retenu', indique uniquement l'une des trois valeurs suivantes : 'URGENCE IMMÉDIATE', 'URGENCE À ÉVALUER RAPIDEMENT' ou 'FAIBLE PROBABILITÉ — SURVEILLANCE REQUISE'.\n\n"
            "NOTE IMPORTANTE SUR L'URGENCE : Un 'mal de tête' ou une 'migraine' classique (même sévère) NE DOIT PAS être classé 'URGENCE IMMÉDIATE'. Ne déclencher 'URGENCE IMMÉDIATE' que s'il y a des déficits neuro-focaux associés (FAST) ou si c'est décrit comme la pire céphalée de la vie (coup de tonnerre)."
        )

    def _build_system_instruction(self) -> str:
        return (
            "You are a clinical stroke triage assistant for Tunisian medical professionals. "
            "You are assisting a licensed doctor, not a patient. "
            "Do not provide patient-facing emergency call instructions. "
            "Use exactly one urgency label from this set: "
            "URGENCE IMMEDIATE, URGENCE A EVALUER RAPIDEMENT, "
            "FAIBLE PROBABILITE MAIS SURVEILLANCE. "
            "CRITICAL RULES FOR URGENCY SCORING: "
            "1. Escalate to 'URGENCE IMMEDIATE' ONLY for sudden FAST symptoms (Face drooping, Arm weakness, Speech difficulty), sudden monocular vision loss, transient focal deficits, or TRUE sudden thunderclap-like headache (worst headache of life peaking in seconds). "
            "2. For general symptoms like 'severe headache', 'headache', 'dizziness', or 'fatigue' without focal neurological deficits, classify as 'URGENCE A EVALUER RAPIDEMENT' or 'FAIBLE PROBABILITE MAIS SURVEILLANCE' depending on severity. Do NOT classify a regular severe headache as immediate stroke urgency unless accompanied by FAST signs or described explicitly as a sudden thunderclap/hemorrhage suspect. "
            "Focus on clinical recommendations: relevant exams, imaging, hospitalization criteria, and specialist referral when appropriate."
        )

    def _build_context_blob(self) -> str:
        parts: list[str] = []
        for path in self._context_paths():
            content = self._read_text_file(path)
            if content:
                parts.append(f"[{path.name}]\n{content}")
        return "\n\n".join(parts).strip()

    def _context_paths(self) -> list[Path]:
        if Config is not None:
            paths = [
                Path(Config.RAG_TEMPLATE_FILE),
                Path(Config.RAG_CASES_FILE),
                Path(Config.RAG_KNOWLEDGE_BASE_FILE),
            ]
        else:
            rag_dir = Path(__file__).resolve().parent.parent / "dataset" / "rag"
            paths = [
                rag_dir / "AVC_RAG_Answer_Template_FR.docx.txt",
                rag_dir / "AVC_Test_Cases_FR.txt",
                rag_dir / "AVC_RAG_Knowledge_Base.txt",
            ]
        return [path for path in paths if path.exists()]

    def _read_text_file(self, path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                return path.read_text(encoding=encoding).strip()
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                logger.warning(f"Unable to read {path}: {exc}")
                break
        return ""

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, dict):
            if isinstance(response.get("text"), str) and response["text"].strip():
                return response["text"]

            choices = response.get("choices") or []
            for choice in choices:
                message = choice.get("message") or {}
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    fragments = [
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict) and isinstance(item.get("text"), str)
                    ]
                    if fragments:
                        return "\n".join(fragment for fragment in fragments if fragment)

        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text

        choices = getattr(response, "choices", None) or []
        for choice in choices:
            message = getattr(choice, "message", None)
            content = getattr(message, "content", None)
            if isinstance(content, str) and content.strip():
                return content

        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            fragments = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
            if fragments:
                return "\n".join(fragments)
        return ""

    def _extract_usage(self, response: Any) -> dict[str, int | None]:
        if isinstance(response, dict):
            usage = response.get("usage") or {}
            return {
                "prompt_tokens": usage.get("prompt_tokens") or usage.get("input_tokens"),
                "completion_tokens": usage.get("completion_tokens") or usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            }

        usage = getattr(response, "usage", None)
        if usage is not None:
            return {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

        return {
            "prompt_tokens": getattr(usage, "prompt_token_count", None),
            "completion_tokens": getattr(usage, "candidates_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
        }

    def _sanitize_response_text(self, text: str) -> str:
        cleaned = text or ""
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = cleaned.replace("<think>", "").replace("</think>", "")

        # If it doesn't look like it already has the template header, clean up conversational prefix
        if not (cleaned.strip().startswith("=") or "REPONSE STRUCTUREE" in cleaned[:150].upper() or "RÉPONSE STRUCTURÉE" in cleaned[:150]):
            urgency_marker = re.search(
                r"Niveau d['’]urgence estim(?:e|é)e?\s*:",
                cleaned,
                flags=re.IGNORECASE,
            )
            if urgency_marker:
                cleaned = cleaned[urgency_marker.start():]

        return cleaned.strip()

    def _extract_urgency(self, text: str) -> str:
        patterns = (
            r"Niveau retenu\s*:\s*(.+)",
            r"Niveau d['’]urgence estime\s*:\s*(.+)",
            r"Niveau d['’]urgence estimee\s*:\s*(.+)",
            r"Niveau d['’]urgence estimé\s*:\s*(.+)",
            r"Niveau d['’]urgence\s*:\s*(.+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._normalize_urgency(match.group(1))

        return self._normalize_urgency(text)

    def _evaluate_locally(self, text: str, exc: Exception) -> dict[str, Any]:
        normalized = self._normalize_text(text)

        has_face = self._contains_any(normalized, ["visage", "face", "bouche", "asymetr", "devi", "tomb"])
        has_limb = self._contains_any(
            normalized,
            ["bras", "jambe", "faiblesse", "faible", "engourdi", "paralys", "lever"],
        )
        has_speech = self._contains_any(
            normalized,
            ["parole", "parler", "aphas", "mots", "comprend", "confus", "confusion"],
        )
        has_vision = self._contains_any(normalized, ["vision", "oeil", "diplopie", "voit plus"])
        has_balance = self._contains_any(
            normalized,
            ["vertige", "equilibre", "marche impossible", "tomber", "instabil", "vomissement"],
        )
        has_thunderclap = self._contains_any(
            normalized,
            ["pire mal de tete", "coup de tonnerre", "nuque raide", "cephalee brutale", "hemorragie"],
        )
        has_seizure = self._contains_any(normalized, ["convulsion", "crise", "epilep"])
        has_transient = self._contains_any(
            normalized,
            ["revenu normal", "tout est revenu", "transitoire", "pendant 10 minutes"],
        )
        repeated_migraine_like = self._contains_any(
            normalized,
            ["episodes similaires", "vision en zigzag", "pulsatile", "migraine", "mal de tete simple", "mal de tete chronique"],
        )
        hypoglycemia_like = self._contains_any(normalized, ["glycemie", "diabet", "sueurs", "tremblements"])

        if (
            has_thunderclap
            or has_vision
            or has_transient
            or has_speech
            or (has_face and has_limb)
            or (has_seizure and has_limb)
        ):
            urgency = URGENCY_IMMEDIATE
            action = "Appeler le 15 / 112 maintenant."
            why = "Des signes neurologiques aigus peuvent correspondre a un AVC ou a une autre urgence neurologique."
        elif has_balance or has_face or hypoglycemia_like:
            urgency = URGENCY_RAPID
            action = "Faire evaluer la personne tres rapidement en urgence."
            why = "Les symptomes justifient une evaluation medicale rapide meme s'il existe des diagnostics imitateurs."
        elif repeated_migraine_like:
            urgency = URGENCY_MONITOR
            action = "Surveiller de pres et consulter rapidement si les symptomes changent, se prolongent ou deviennent focaux."
            why = "Le tableau peut evoquer un imitateur, mais une aggravation ou un premier episode atypique doit etre re-evalue en urgence."
        else:
            urgency = URGENCY_RAPID
            action = "Chercher un avis medical rapide si les symptomes sont nouveaux ou persistent."
            why = "Sans examen clinique, il faut rester prudent."

        bullets = []
        if has_face:
            bullets.append("atteinte du visage")
        if has_limb:
            bullets.append("faiblesse ou engourdissement d'un membre")
        if has_speech:
            bullets.append("trouble de la parole ou confusion")
        if has_vision:
            bullets.append("trouble visuel soudain")
        if has_balance:
            bullets.append("vertiges ou trouble de l'equilibre")
        if has_thunderclap:
            bullets.append("cephalee brutale inhabituelle")
        if has_seizure:
            bullets.append("convulsions")

        summary = ", ".join(bullets) if bullets else "symptomes neurologiques a preciser"
        fallback_note = self._fallback_note(exc)
        response = (
            f"Niveau d'urgence estime : {urgency}\n\n"
            "Resume :\n"
            f"- Action recommandee : {action}\n"
            f"- Pourquoi : {why}\n\n"
            "Ce que j'ai compris :\n"
            f"- Signes reperes : {summary}.\n"
            f"- Description libre : {text.strip()}\n\n"
            "Ce qu'il faut faire maintenant :\n"
            "- Noter l'heure de debut ou de derniere normalite si vous la connaissez.\n"
            "- Ne pas laisser la personne seule si les symptomes sont en cours.\n"
            "- Ne pas conduire soi-meme vers les urgences en cas de deficit neurologique actif.\n"
            "- Si apparition d'asymetrie du visage, faiblesse d'un cote, trouble de parole, perte de vision ou aggravation : appeler le 15 / 112 immediatement.\n\n"
            "Limite :\n"
            f"- Reponse locale de secours utilisee car les services distants etaient indisponibles: {fallback_note}\n"
            "- Cette reponse reste educative et ne remplace pas un avis medical."
        )

        return {
            "response": response,
            "urgency": urgency,
            "model": "local-fallback",
            "provider": "local-fallback",
            "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
        }

    def _normalize_urgency(self, raw: str) -> str:
        normalized = self._normalize_text(str(raw or "")).upper()
        if "URGENCE" in normalized and "IMMEDIATE" in normalized:
            return URGENCY_IMMEDIATE
        if "URGENCE" in normalized and "RAPID" in normalized:
            return URGENCY_RAPID
        if "FAIBLE" in normalized and "SURVEILLANCE" in normalized:
            return URGENCY_MONITOR
        return URGENCY_UNKNOWN

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return normalized.lower()

    def _contains_any(self, text: str, needles: list[str]) -> bool:
        return any(needle in text for needle in needles)

    def _fallback_note(self, exc: Exception) -> str:
        message = " ".join(str(exc).split())
        upper = message.upper()
        if "RESOURCE_EXHAUSTED" in upper or "QUOTA" in upper or "429" in upper:
            return "quota LLM depassee"
        if "API KEY" in upper or "PERMISSION" in upper or "UNAUTH" in upper or "AUTH" in upper:
            return "probleme d'authentification du fournisseur LLM"
        return message[:180] if message else "erreur distante inconnue"
