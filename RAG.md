# Retrieval-Augmented Generation (RAG) System

A modular RAG implementation for PawPal that supports PDF extraction, chunking, embedding generation, similarity search, and context retrieval without requiring a heavy framework.

## What You Have

The project includes a complete RAG workflow with:

- PDF extraction
- character-based and sentence-based chunking
- OpenAI embeddings
- cosine-similarity search
- optional FAISS search
- `RAGSystem` class for a simple end-to-end interface
- example scripts and merged playground demos in `main.py`

## Key Features

✅ PDF text extraction  
✅ Smart text chunking  
✅ OpenAI embeddings  
✅ Similarity search with cosine similarity or FAISS  
✅ End-to-end retrieval via `RAGSystem`  
✅ Example integrations for PawPal use cases  

## File Overview

| File | Purpose |
|------|---------|
| `rag_system.py` | Core RAG implementation |
| `example_rag_usage.py` | RAG usage patterns and demonstrations |
| `example_pawpal_rag_integration.py` | PawPal-specific RAG example |
| `main.py` | Includes merged RAG playground demos via `python main.py playground` |
| `RAG.md` | Consolidated RAG guide |

## Installation

```bash
pip install openai pypdf
pip install faiss-cpu
```

If you are using the project environment:

```bash
pip install -r requirements.txt
```

## Configuration

### Set OpenAI API Key

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

macOS/Linux:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### 1. Extract text from a PDF

```python
from rag_system import extract_text_from_pdf

text = extract_text_from_pdf("document.pdf")
print(text)
```

### 2. Split into chunks

```python
from rag_system import chunk_text, chunk_text_by_sentences

chunks = chunk_text(text, chunk_size=512, overlap=50)
chunks = chunk_text_by_sentences(text, target_chunk_size=512)
```

### 3. Generate embeddings

```python
from rag_system import generate_embeddings

embeddings = generate_embeddings(chunks)
```

### 4. Search for relevant chunks

```python
from rag_system import search_similar_chunks

results = search_similar_chunks(
    query="What is machine learning?",
    chunks=chunks,
    embeddings=embeddings,
    top_k=5
)

for chunk, score in results:
    print(score, chunk)
```

## Recommended Interface: `RAGSystem`

```python
from rag_system import RAGSystem

rag = RAGSystem(use_faiss=False)
rag.load_pdf("document.pdf", chunk_size=512, overlap=50)

results = rag.query("Your question here", top_k=5)
context = rag.get_context("Your question here", top_k=3)

print(context)
```

Why use it:

- one object manages chunks and embeddings
- simple `load_pdf()` then `query()` flow
- easy to swap between cosine similarity and FAISS

## Core Functions

### `extract_text_from_pdf(pdf_path: str) -> str`

Extracts text from a PDF file using `pypdf`.

Parameters:

- `pdf_path`: path to the PDF

Returns:

- extracted text as a single string

Raises:

- `FileNotFoundError`
- `ImportError`

### `chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]`

Character-based chunking with overlap.

Use when:

- text is messy or not sentence-friendly
- you want predictable chunk sizes

### `chunk_text_by_sentences(text: str, target_chunk_size: int = 512) -> List[str]`

Sentence-aware chunking.

Use when:

- the document has normal sentence boundaries
- you want more semantically coherent chunks

### `generate_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]`

Generates embeddings using OpenAI.

Requires:

- `OPENAI_API_KEY`

### `search_similar_chunks(query, chunks, embeddings, top_k=5)`

Searches with cosine similarity.

Best for:

- small to medium datasets
- minimal dependencies

### `search_with_faiss(query, chunks, embeddings, top_k=5)`

Searches with FAISS.

Best for:

- larger datasets
- faster retrieval at scale

### `cosine_similarity(vec1, vec2) -> float`

Manual cosine similarity helper used by the simple search path.

## `RAGSystem` Class

### `__init__(use_faiss: bool = False)`

Creates the RAG system and selects the search backend.

### `load_pdf(pdf_path: str, chunk_size: int = 512, overlap: int = 50) -> None`

Runs:

1. PDF extraction
2. chunking
3. embedding generation

### `query(query_text: str, top_k: int = 5)`

Returns the top matching chunks and scores.

### `get_context(query_text: str, top_k: int = 5) -> str`

Formats retrieved results into a readable context block for downstream prompting.

## Common Usage Patterns

### Pattern 1: Simple PDF question answering

```python
from rag_system import RAGSystem

rag = RAGSystem()
rag.load_pdf("knowledge.pdf")
context = rag.get_context("What are the feeding requirements?")
print(context)
```

### Pattern 2: Manual pipeline control

```python
from rag_system import (
    extract_text_from_pdf,
    chunk_text_by_sentences,
    generate_embeddings,
    search_similar_chunks,
)

text = extract_text_from_pdf("document.pdf")
chunks = chunk_text_by_sentences(text, target_chunk_size=400)
embeddings = generate_embeddings(chunks)
results = search_similar_chunks("What is the main topic?", chunks, embeddings, top_k=3)
```

### Pattern 3: PawPal pet-care advisor

```python
from rag_system import chunk_text_by_sentences, generate_embeddings, search_similar_chunks
from openai import OpenAI

pet_guide = "Dogs need daily exercise and a consistent feeding schedule."
chunks = chunk_text_by_sentences(pet_guide, target_chunk_size=400)
embeddings = generate_embeddings(chunks)

query = "How much exercise does my dog need?"
results = search_similar_chunks(query, chunks, embeddings, top_k=3)
context = "\n".join([chunk for chunk, _ in results])

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": f"Based on this context:\n{context}\n\nAnswer: {query}"
    }]
)
print(response.choices[0].message.content)
```

## Playground and Demo Commands

### Quick interactive demos

```bash
python main.py playground
```

### Example usage patterns

```bash
python example_rag_usage.py
python example_pawpal_rag_integration.py
```

### Other RAG demos in `main.py`

```bash
python main.py rag
python main.py pawpal_rag
```

## Performance Guide

| Method | Speed | Memory | Best For |
|--------|-------|--------|----------|
| Cosine similarity | Slower | Low | Small datasets, simple setups |
| FAISS | Faster | Medium | Large datasets, production search |

### Rule of thumb

- under 1000 chunks: cosine similarity is usually fine
- above 1000 chunks: FAISS is usually worth it

## Chunking Guidance

### Character-based chunking

Good when:

- documents are poorly structured
- formatting is inconsistent

Tradeoff:

- less semantic coherence

### Sentence-based chunking

Good when:

- documents are natural prose
- meaning should stay grouped

Tradeoff:

- chunk sizes vary more

### Overlap

Overlap helps preserve context near chunk boundaries, but too much overlap increases redundancy and embedding cost.

## Configuration Tips

### Chunk size

```python
chunks = chunk_text(text, chunk_size=256)
chunks = chunk_text(text, chunk_size=1024)
```

- smaller chunks: more precise retrieval, more chunks, more embeddings
- larger chunks: broader context, fewer chunks, lower precision

### Top-k

```python
results = rag.query("question", top_k=3)
results = rag.query("question", top_k=10)
```

- lower `top_k`: tighter context
- higher `top_k`: broader recall for post-processing

### Threshold filtering

```python
results = rag.query("question", top_k=10)
relevant = [(chunk, score) for chunk, score in results if score > 0.7]
```

Useful when you want to suppress weak matches before sending context to an LLM.

## Performance Characteristics

Approximate behavior from the implementation summary:

| Task | Time | Notes |
|------|------|------|
| Extract PDF (50 pages) | ~1-2s | Depends on PDF quality |
| Generate 100 embeddings | ~2-5s | API-bound |
| Search 1000 chunks with cosine similarity | ~0.5s | Linear scan |
| Search 1000 chunks with FAISS | ~5ms | Much faster retrieval |

## Architecture Notes

This RAG system was designed to be:

- lightweight
- modular
- easy to reuse in scripts and apps
- flexible enough to use via individual functions or a class

It avoids heavy orchestration frameworks and keeps the retrieval pipeline understandable.

## Dependencies

```txt
openai>=1.0.0
pypdf>=4.0.0
faiss-cpu>=1.7.0
```

Notes:

- `faiss-cpu` is optional
- `math` is used for manual cosine similarity and is built in

## Testing

Run:

```bash
python example_rag_usage.py
python example_pawpal_rag_integration.py
python main.py playground
```

Expected outcomes:

- chunking demonstrations
- retrieval examples
- similarity score examples
- PawPal-oriented knowledge-base examples

## Troubleshooting

### `OPENAI_API_KEY not set`

Set the environment variable correctly before running embedding generation.

### `No module named pypdf`

```bash
pip install pypdf
```

### `FAISS is not installed`

```bash
pip install faiss-cpu
```

### PDF extraction returns empty text

Check whether:

- the PDF is text-based instead of scanned images
- the file path is correct
- the PDF has copyable text content

## Limitations

- requires OpenAI API access for embeddings
- FAISS support is optional and separate
- PDF extraction quality depends on the source file
- retrieval is text-only
- there is no persistence layer or vector database built in

## Future Enhancements

- vector database integration
- hybrid keyword + semantic search
- reranking
- caching embeddings for lower cost
- multi-document persistence
- alternative embedding providers
- LLM-based answer generation helpers

## Summary

The RAG system in PawPal gives you:

- a simple PDF-to-context pipeline
- flexible chunking and search options
- a lightweight architecture
- example scripts and demos
- enough structure to integrate retrieval into schedule generation or advisor workflows
