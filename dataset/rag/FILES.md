# RAG Dataset Files

Knowledge-base and test material used by symptom RAG.

The active code path is:

`rag/symptom_rag.py` -> `_context_paths()` -> `_read_text_file()` -> `_build_context_blob()` -> `_build_prompt()`

## Files

### `AVC_RAG_Knowledge_Base.txt`

Main text knowledge base for AVC/stroke symptom reasoning.

Used for:

- medical context injected into the prompt
- symptom interpretation
- emergency-action guidance

This is the most important RAG source because it is directly readable as text.

### `AVC_RAG_Knowledge_Base.pdf`

PDF version of the knowledge base.

Useful for:

- human reading
- sharing with supervisors
- preserving formatted source material

The current RAG code reads text files, so this PDF is reference material unless a PDF ingestion step is added.

### `AVC_RAG_Knowledge_Base.docx`

Word document version of the knowledge base.

Useful for editing the medical knowledge base before exporting to text/PDF.

The current RAG code does not parse DOCX directly.

### `AVC_RAG_Answer_Template_FR.docx.txt`

French answer template used to shape the RAG response.

Used by:

- `SymptomRAG._context_paths()`
- `SymptomRAG._build_context_blob()`

Why it matters:

- Helps keep answers structured and consistent.
- Encourages French clinical output.
- Supports the required urgency format used later by `_extract_urgency()`.

### `AVC_Test_Cases_FR.txt`

French symptom test cases.

Useful for:

- manual RAG testing
- comparing urgency output across providers
- checking that FAST symptoms and less urgent symptoms are handled differently

Related code:

- `symptom_chat.py --query "..."`
- `tests/test_symptoms.py`
