# Retrieval-Augmented Generation (RAG) System

A simple, modular implementation of RAG in Python without heavy framework dependencies.

## Features

✅ **PDF Text Extraction** - Extract text from PDF files  
✅ **Smart Text Chunking** - Character-based and sentence-based chunking  
✅ **OpenAI Embeddings** - Generate embeddings using OpenAI's API  
✅ **Similarity Search** - Cosine similarity or FAISS-based search  
✅ **RAG Pipeline** - End-to-end retrieval system with the `RAGSystem` class  

## Installation

```bash
# Basic dependencies
pip install openai pypdf

# Optional: For faster similarity search on large datasets
pip install faiss-cpu
```

## Quick Start

### 1. Extract Text from PDF

```python
from rag_system import extract_text_from_pdf

text = extract_text_from_pdf("document.pdf")
print(text)
```

### 2. Chunk Text

```python
from rag_system import chunk_text, chunk_text_by_sentences

# Character-based chunking
chunks = chunk_text(text, chunk_size=512, overlap=50)

# Sentence-based chunking (more semantic)
chunks = chunk_text_by_sentences(text, target_chunk_size=512)
```

### 3. Generate Embeddings

```python
from rag_system import generate_embeddings

embeddings = generate_embeddings(chunks)
```

### 4. Search Relevant Chunks

```python
from rag_system import search_similar_chunks

query = "What is machine learning?"
results = search_similar_chunks(query, chunks, embeddings, top_k=5)

for chunk, similarity_score in results:
    print(f"Score: {similarity_score:.4f}")
    print(f"Text: {chunk}\n")
```

## Complete Example: RAGSystem Class

```python
from rag_system import RAGSystem

# Create RAG system
rag = RAGSystem(use_faiss=False)  # Set True if FAISS is installed

# Load PDF and automatically chunk & embed
rag.load_pdf("document.pdf", chunk_size=512, overlap=50)

# Query and get results
results = rag.query("Your question here", top_k=5)

# Get formatted context
context = rag.get_context("Your question here", top_k=3)
print(context)
```

## API Reference

### Core Functions

#### `extract_text_from_pdf(pdf_path: str) -> str`
Extracts all text from a PDF file.

**Parameters:**
- `pdf_path`: Path to PDF file

**Returns:** Extracted text as string

**Raises:** `FileNotFoundError`, `ImportError`

---

#### `chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]`
Splits text into character-based overlapping chunks.

**Parameters:**
- `text`: Input text
- `chunk_size`: Characters per chunk
- `overlap`: Overlapping characters between chunks

**Returns:** List of chunks

---

#### `chunk_text_by_sentences(text: str, target_chunk_size: int = 512) -> List[str]`
Splits text into sentence-based chunks (more semantic).

**Parameters:**
- `text`: Input text
- `target_chunk_size`: Target size in characters

**Returns:** List of chunks

---

#### `generate_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]`
Generates embeddings using OpenAI API.

**Parameters:**
- `texts`: List of text strings
- `model`: OpenAI model name

**Returns:** List of embedding vectors

**Requires:** `OPENAI_API_KEY` environment variable

---

#### `search_similar_chunks(query: str, chunks: List[str], embeddings: List[List[float]], top_k: int = 5) -> List[Tuple[str, float]]`
Finds top-k similar chunks using cosine similarity.

**Parameters:**
- `query`: Query string
- `chunks`: List of text chunks
- `embeddings`: Pre-computed embeddings
- `top_k`: Number of results

**Returns:** List of (chunk, similarity_score) tuples

---

#### `search_with_faiss(query: str, chunks: List[str], embeddings: List[List[float]], top_k: int = 5) -> List[Tuple[str, float]]`
Finds top-k similar chunks using FAISS (faster for large datasets).

**Parameters:** Same as `search_similar_chunks`

**Returns:** List of (chunk, similarity_score) tuples

**Requires:** `faiss-cpu` package

---

#### `cosine_similarity(vec1: List[float], vec2: List[float]) -> float`
Calculates cosine similarity between two vectors.

**Parameters:**
- `vec1`: First vector
- `vec2`: Second vector

**Returns:** Similarity score (0 to 1)

---

### RAGSystem Class

#### `__init__(use_faiss: bool = False)`
Initialize RAG system.

#### `load_pdf(pdf_path: str, chunk_size: int = 512, overlap: int = 50) -> None`
Load and process a PDF file.

#### `query(query_text: str, top_k: int = 5) -> List[Tuple[str, float]]`
Search for relevant chunks.

#### `get_context(query_text: str, top_k: int = 5) -> str`
Get formatted context string.

## Configuration

### Set OpenAI API Key

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Performance Considerations

| Method | Speed | Memory | Best For |
|--------|-------|--------|----------|
| Cosine Similarity | Slow for large datasets | Low | Small datasets (<1000 chunks) |
| FAISS | Fast | Medium | Large datasets (>1000 chunks) |

### Chunking Strategy

- **Character-based:** Use when documents are not well-structured
- **Sentence-based:** Use when documents have clear sentence boundaries (better semantic)
- **Overlap:** Helps maintain context at chunk boundaries

## Example: Pet Care Knowledge Base

```python
from rag_system import RAGSystem

# Create a RAG system for pet care documentation
rag = RAGSystem()

# Load your pet care guidelines PDF
rag.load_pdf("pet_care_guidelines.pdf")

# Query the knowledge base
results = rag.query("What are the feeding requirements for a labrador?", top_k=3)

for chunk, score in results:
    print(f"Relevance: {score:.3f}\n{chunk}\n")
```

## Files

- `rag_system.py` - Core RAG implementation
- `example_rag_usage.py` - Usage examples
- `RAG.md` - This documentation

## Testing

Run the examples:
```bash
python example_rag_usage.py
```

## Limitations

- Requires OpenAI API key for embeddings
- FAISS is optional but recommended for large datasets
- PDF extraction may not work perfectly with all PDF formats
- No support for multi-modal embeddings (text only)

## Future Enhancements

- Support for other embedding models (HuggingFace, Anthropic)
- Hybrid search (combining semantic and keyword search)
- Document summarization before chunking
- Semantic similarity using alternative distance metrics
- LLM-based answer generation from retrieved context
