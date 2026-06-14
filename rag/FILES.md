# RAG Files

This folder contains symptom RAG logic. It reads local AVC knowledge-base files, builds a medical triage prompt, calls an LLM provider, extracts an urgency label, and falls back to local rules if remote providers fail.

## `symptom_rag.py`

Defines `SymptomRAG`.

## `SymptomRAG`

Educational stroke triage assistant with provider failover.

Supported provider order can include:

- Groq
- OpenRouter
- LM Studio
- local fallback rules

### `__init__(api_key=None, model=None)`

Initializes the RAG engine.

What it builds:

- requested API key/model
- provider order
- local context blob from dataset files
- system instruction
- provider-client cache

Raises:

- `ValueError` if no provider is configured.

### `evaluate(text, conversation_history=None)`

Main entry point for symptom RAG.

Steps:

- builds a prompt with local knowledge context and recent conversation
- tries each configured provider
- extracts text from the provider response
- cleans unwanted reasoning tags
- extracts the urgency label
- returns response, urgency, provider, model, and token usage
- if all providers fail, calls `_evaluate_locally()`

Returns:

```python
{
    "response": response_text,
    "urgency": urgency,
    "model": model,
    "provider": provider,
    "usage": {...},
}
```

### `chat(history, message)`

Small helper for multi-turn conversations.

It calls `evaluate()`, appends the user and assistant messages to the history, and returns:

```python
(reply_text, new_history)
```

### `_build_provider_order()`

Chooses provider failover order.

Examples:

- Explicit Groq key -> Groq first, then LM Studio/OpenRouter.
- OpenRouter-looking model/key -> OpenRouter first.
- Local LM Studio configured -> LM Studio can be used.
- Default -> Groq, then OpenRouter, then LM Studio.

### `_append_provider(...)`

Adds a provider config to the order if it is usable and not already present.

For LM Studio it also normalizes the base URL.

### `_detect_provider(api_key, model)`

Infers the provider from:

- key prefix, for example `gsk_` means Groq
- model naming
- whether LM Studio base URL exists

### `_resolve_model(provider, requested_model)`

Chooses the actual model name.

It uses:

- explicit model if provided
- config defaults
- fallback model names

### `_get_or_create_client(provider_cfg)`

Creates and caches provider clients.

Backends:

- LM Studio uses HTTP JSON requests.
- Groq uses the `groq` package.
- OpenRouter uses the OpenAI-compatible client with OpenRouter base URL.

### `_generate_with_provider(provider_cfg, prompt)`

Actually sends a prompt to the chosen provider.

For cloud providers it sends:

- system instruction
- user prompt
- low temperature `0.2`

### `_resolve_lmstudio_model(base_url, configured_model)`

If LM Studio model is `auto`, it asks LM Studio for available models and chooses the best loaded/preferred one.

### `_pick_lmstudio_model(payload)`

Model selection logic:

- prefer already loaded models
- then preferred known model names
- then names containing `instruct`, `reason`, or `chat`
- then the first model returned

### `_lmstudio_chat_completion(...)`

Builds an OpenAI-style chat completion request for LM Studio.

### `_lmstudio_json_request(...)` and `_http_json(...)`

Low-level HTTP helpers for LM Studio.

They handle:

- alternate `/v1` vs `/api/v1` paths
- JSON encoding/decoding
- HTTP and URL errors

### `_build_prompt(text, conversation_history)`

Creates the full medical prompt.

Includes:

- local RAG context from dataset files
- last six conversation turns
- new patient description
- required first-line urgency format
- special rule: ordinary headache should not be immediate unless focal deficits or thunderclap description exist

### `_build_system_instruction()`

Defines global assistant behavior.

Key rule:

- FAST symptoms, vision loss, transient focal deficits, and thunderclap headache should escalate urgently.

### `_build_context_blob()` and `_context_paths()`

Loads local knowledge files from `dataset/rag`.

Main files:

- answer template
- test cases
- knowledge base

### `_extract_text(response)`

Normalizes response objects from different providers into one text string.

Supports:

- dict responses
- OpenAI/Groq style `choices`
- Gemini-like candidates/parts

### `_extract_usage(response)`

Normalizes token usage fields across providers.

### `_sanitize_response_text(text)`

Removes `<think>` blocks and trims text before the urgency marker if needed.

### `_extract_urgency(text)` and `_normalize_urgency(raw)`

Find and normalize the urgency label into one of:

- `URGENCE IMMEDIATE`
- `URGENCE A EVALUER RAPIDEMENT`
- `FAIBLE PROBABILITE MAIS SURVEILLANCE`
- `UNKNOWN`

### `_evaluate_locally(text, exc)`

Rule-based fallback used when all LLM providers fail.

It checks normalized text for:

- face drooping / asymmetry
- limb weakness
- speech problems
- vision problems
- thunderclap headache

Then returns a safe educational response with an urgency label and a note explaining why fallback was used.

### `_fallback_note(exc)`

Turns provider exceptions into short human-readable reasons, such as:

- quota/rate limit
- authentication problem
- empty response
- remote provider error
