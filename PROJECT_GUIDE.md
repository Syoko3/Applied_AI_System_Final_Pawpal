# PawPal Project Guide

## Overview

This is the consolidated project guide for the current PawPal codebase.
It has been cleaned up so it only references files, commands, and app behavior that exist in the current project.

## What This Project Does

PawPal is an AI pet assistant that:

- generates pet schedules with OpenAI
- validates schedules for completeness and realism
- uses RAG to retrieve context from uploaded pet-care PDFs
- provides a Streamlit interface for the full upload → retrieve → generate → validate flow

## Current Project Files

### Source code

- `app.py`: Streamlit app for PDF upload, retrieval, schedule generation, and validation display
- `main.py`: CLI demos for scheduler, validation, RAG, and schedule generation
- `pawpal_system.py`: pet/task models, scheduling logic, LLM schedule generation, and validation helpers
- `rag_system.py`: PDF extraction, chunking, embeddings, similarity search, and `RAGSystem`

### Tests

- `test_pawpal.py`: pytest-based tests for scheduler behavior, filtering, conflict detection, validation helpers, and mocked AI output

### Documentation

- `PROJECT_GUIDE.md`: this consolidated guide
- `README.md`: short project summary stub

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Set your API key in PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

The app and CLI also load `.env` from the project folder when `python-dotenv` is installed.

## Requirements

Current dependencies in `requirements.txt`:

```txt
streamlit==1.32.2
pytest>=7.0
numpy<2.0
openai>=1.0.0
pypdf>=4.0.0
faiss-cpu>=1.7.0
python-dotenv>=1.0.0
```

Notes:

- `openai` is required for schedule generation and embeddings
- `pypdf` is required for PDF text extraction
- `faiss-cpu` is optional at runtime unless you use FAISS retrieval

## How To Run

### Streamlit app

```bash
streamlit run app.py
```

### CLI demos

```bash
python main.py
python main.py validate
python main.py rag
python main.py pawpal_rag
python main.py playground
python main.py schedule
```

What each command does:

- `python main.py`: runs the base scheduler/task demo
- `python main.py validate`: runs schedule generation, validation, and optional fixing demo
- `python main.py rag`: runs RAG examples using in-memory sample text
- `python main.py pawpal_rag`: runs the PawPal pet-care advisor example
- `python main.py playground`: runs the merged RAG playground demos
- `python main.py schedule`: runs schedule-generation examples

### Tests

```bash
python -m pytest
```

## Streamlit App Flow

The current `app.py` implements this pipeline:

```text
Upload PDF
    ↓
Extract text
    ↓
Chunk text
    ↓
Generate embeddings
    ↓
Retrieve relevant context
    ↓
Generate schedule with OpenAI
    ↓
Validate generated schedule
    ↓
Display schedule, explanation, issues, and retrieved context
```

What the current app supports:

- PDF upload
- text extraction preview
- embedding generation
- context retrieval from uploaded PDF content
- schedule generation from retrieved context
- validation result display
- issue list display when validation fails

What the current app does not yet implement:

- a Streamlit button to auto-run `review_and_fix_schedule()`
- a Streamlit before/after comparison UI for improved schedules

## Validation System

Validation is implemented in `pawpal_system.py`.

### `validate_schedule(schedule_text: str) -> dict`

Checks a generated schedule for:

- essential task coverage such as feeding, exercise, and rest
- time references
- activity count
- duration information
- rest or sleep coverage

Returns a dictionary like:

```python
{
    "status": "valid" or "invalid",
    "issues": ["Issue 1", "Issue 2"],
    "summary": "Brief result summary",
    "task_count": 5,
}
```

### `review_and_fix_schedule(schedule_text, issues, pet_type, context) -> str`

Uses the OpenAI API to rewrite an invalid schedule so it is more complete and specific.

Typical improvements include:

- adding missing time details
- adding durations
- covering missing core activities
- improving clarity and reasoning

### `validate_and_fix_schedule(schedule_text, pet_type, context) -> dict`

Runs the full validation pipeline:

1. validate the original schedule
2. return the original if it is already valid
3. call `review_and_fix_schedule()` only when needed

Typical return shape:

```python
{
    "original_schedule": "...",
    "validation_result": {...},
    "is_valid": True,
    "improved_schedule": None,
}
```

### Validation workflow

```text
Generate schedule
    ↓
Validate
    ├─ Valid → keep original schedule
    └─ Invalid → review and fix
                     ↓
               return improved schedule
```

### Validation example

```python
from pawpal_system import validate_and_fix_schedule

result = validate_and_fix_schedule(
    schedule_text,
    pet_type="dog",
    context="3-year-old Labrador with high energy",
)

final_schedule = result["improved_schedule"] or result["original_schedule"]
```

## RAG System

RAG is implemented in `rag_system.py`.

### Main capabilities

- extract text from PDFs
- split text into chunks
- generate embeddings with OpenAI
- retrieve similar chunks with cosine similarity
- optionally retrieve with FAISS
- expose a simple end-to-end `RAGSystem` class

### Core functions

```python
extract_text_from_pdf(pdf_path: str) -> str
chunk_text(text, chunk_size=512, overlap=50) -> list[str]
chunk_text_by_sentences(text, target_chunk_size=512) -> list[str]
generate_embeddings(texts, model="text-embedding-3-small") -> list[list[float]]
search_similar_chunks(query, chunks, embeddings, top_k=5)
search_with_faiss(query, chunks, embeddings, top_k=5)
cosine_similarity(vec1, vec2) -> float
```

### `RAGSystem` class

`RAGSystem` wraps the basic workflow:

1. load a PDF
2. chunk the text
3. generate embeddings
4. query for relevant chunks
5. format retrieved context

Example:

```python
from rag_system import RAGSystem

rag = RAGSystem(use_faiss=False)
rag.load_pdf("pet_care_guide.pdf")
context = rag.get_context("What feeding guidance is most relevant?", top_k=3)
print(context)
```

### Retrieval guidance

- sentence-based chunking is usually better for natural prose
- cosine similarity is fine for small to medium chunk sets
- FAISS is more useful when scaling to larger collections

## Key Application Functions

### Schedule generation

```python
from pawpal_system import generate_schedule_with_context

schedule = generate_schedule_with_context(
    "Create a daily schedule for my 3-year-old Labrador.",
    "Feed twice daily, include exercise, training, and rest."
)
```

### Manual RAG pipeline

```python
from rag_system import (
    extract_text_from_pdf,
    chunk_text_by_sentences,
    generate_embeddings,
    search_similar_chunks,
)

text = extract_text_from_pdf("guide.pdf")
chunks = chunk_text_by_sentences(text, target_chunk_size=500)
embeddings = generate_embeddings(chunks)
results = search_similar_chunks("How often should I walk my dog?", chunks, embeddings, top_k=3)
```

## Verification Checklist

- `pawpal_system.py` contains schedule generation and validation helpers
- `rag_system.py` contains extraction, chunking, embedding, and retrieval helpers
- `app.py` supports PDF upload and shows validation results for generated schedules
- `main.py playground` runs the merged RAG demos
- `python -m pytest` runs the existing test suite in `test_pawpal.py`

## Known Limitations

- schedule generation and embedding creation require `OPENAI_API_KEY`
- validation relies mostly on heuristic checks and keyword matching
- PDF extraction quality depends on whether the PDF contains readable text
- the current Streamlit app validates schedules but does not auto-fix them in the UI
- there is no persistent vector database; retrieval is in memory

## Summary

Use this file as the single source of truth for the current PawPal project. It reflects the repo as it exists now: a pet scheduling assistant with validation, RAG-based PDF retrieval, CLI demos, a Streamlit app, and one active test module.
