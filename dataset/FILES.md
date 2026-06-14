# Dataset Files

Datasets used by the AI model project.

## Folders

### `image trainning/`

MRI image dataset used by the image classifier.

Expected structure:

```text
image trainning/
  train/
    Hemorrhagic/
    Ischemic/
    Normal/
  valid/
    Hemorrhagic/
    Ischemic/
    Normal/
  test/
    Hemorrhagic/
    Ischemic/
    Normal/
```

How code uses it:

- `training/image_trainer.py` expects `train`, `valid`, and `test` folders.
- `preprocessing/dataset.py` recursively loads `.jpg`, `.jpeg`, and `.png` files.
- `tests/test_model.py` and `tests/evaluate_model.py` use the `test` folder for evaluation.

Important detail:

- Class folder names should match `Config.EXPECTED_IMAGE_CLASSES`.
- Class order matters because inference treats `Hemorrhagic + Ischemic` as total stroke probability and `Normal` as non-stroke.

This folder contains many image assets, so it is not documented file-by-file.

### `rag/`

Text/PDF/DOCX knowledge material used by the symptom RAG engine.

How code uses it:

- `rag/symptom_rag.py` reads the text files through `_context_paths()`.
- `_build_context_blob()` merges the available knowledge files into the prompt context.
- `_build_prompt()` adds this local context before the patient symptom description.

See `rag/FILES.md` for file-by-file details.
