# RAG System - Quick Reference Guide

## 📦 What You Have

A complete **Retrieval-Augmented Generation** system with:
- PDF extraction
- Text chunking (character-based & sentence-based)
- OpenAI embeddings
- Similarity search (cosine similarity & FAISS)
- RAGSystem class for easy integration

## 🚀 Getting Started (5 Minutes)

### 1. Set Environment Variable
```powershell
# Windows PowerShell
$env:OPENAI_API_KEY = "your-api-key-here"
```

```bash
# macOS/Linux
export OPENAI_API_KEY="your-api-key-here"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Examples
```bash
# Quick playground with sample data (no PDF needed)
python rag_playground.py

# RAG with custom examples
python example_rag_usage.py

# PawPal pet care advisor
python example_pawpal_rag_integration.py
```

## 📚 Core Functions

### Extract PDF Text
```python
from rag_system import extract_text_from_pdf

text = extract_text_from_pdf("document.pdf")
```

### Split Into Chunks
```python
from rag_system import chunk_text, chunk_text_by_sentences

# Option 1: Fixed-size chunks
chunks = chunk_text(text, chunk_size=512, overlap=50)

# Option 2: Sentence-based (recommended)
chunks = chunk_text_by_sentences(text, target_chunk_size=512)
```

### Generate Embeddings
```python
from rag_system import generate_embeddings

embeddings = generate_embeddings(chunks)
# Returns: List of embedding vectors
```

### Search for Relevant Chunks
```python
from rag_system import search_similar_chunks

results = search_similar_chunks(
    query="Your question here",
    chunks=chunks,
    embeddings=embeddings,
    top_k=5  # Return top 5 results
)

for chunk, similarity_score in results:
    print(f"Score: {similarity_score:.4f}")
    print(f"Text: {chunk}")
```

## 🎯 Using RAGSystem Class (Recommended)

Simpler, unified interface:

```python
from rag_system import RAGSystem

# Create system
rag = RAGSystem(use_faiss=False)  # Set True if FAISS installed

# Load PDF
rag.load_pdf("your_document.pdf", chunk_size=512, overlap=50)

# Query
results = rag.query("What is the main topic?", top_k=5)

# Get formatted context
context = rag.get_context("Your question", top_k=3)
print(context)
```

## 🔍 Example: Pet Care Advisor

```python
from rag_system import chunk_text_by_sentences, generate_embeddings, search_similar_chunks
from openai import OpenAI

# Create knowledge base
pet_guide = "Dogs need 60+ minutes exercise daily..."
chunks = chunk_text_by_sentences(pet_guide, target_chunk_size=400)
embeddings = generate_embeddings(chunks)

# Search
query = "How much exercise does my dog need?"
results = search_similar_chunks(query, chunks, embeddings, top_k=3)

# Use results to ground LLM response
context = "\n".join([c for c, _ in results])
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

## 📊 Performance Guide

| Task | Speed | When to Use |
|------|-------|-----------|
| **Cosine Similarity** | 🐢 Slow | <1000 chunks |
| **FAISS Search** | 🚀 Fast | >1000 chunks |

```python
# For small knowledge bases (use default)
rag = RAGSystem(use_faiss=False)

# For large knowledge bases
rag = RAGSystem(use_faiss=True)  # Requires: pip install faiss-cpu
```

## 🎮 Interactive Testing

Test without needing a PDF:

```bash
python rag_playground.py
```

This includes:
- Sample machine learning knowledge base
- Sample pet care knowledge base  
- Interactive queries
- Similarity score demonstrations
- Chunking strategy comparison

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `rag_system.py` | Core RAG implementation (all functions) |
| `rag_playground.py` | Test RAG without PDFs (samples included) |
| `example_rag_usage.py` | Various RAG usage patterns |
| `example_pawpal_rag_integration.py` | Pet care advisor example |
| `RAG.md` | Complete documentation |

## 🔧 Common Patterns

### Pattern 1: Simple Q&A
```python
rag = RAGSystem()
rag.load_pdf("knowledge.pdf")
answer_context = rag.get_context("What is X?")
```

### Pattern 2: Batch Processing
```python
questions = ["Q1", "Q2", "Q3"]
for q in questions:
    results = rag.query(q, top_k=3)
    # Process results
```

### Pattern 3: Threshold Filtering
```python
results = rag.query("question", top_k=10)
relevant = [(c, s) for c, s in results if s > 0.7]  # Only high confidence
```

### Pattern 4: Context Reranking
```python
# Get more candidates, manually rerank with LLM
results = rag.query("question", top_k=10)
# Send top 10 to LLM for semantic reranking
```

## ⚙️ Configuration

### Chunk Size Impact
```python
# Smaller chunks = more precise but more API calls
chunks = chunk_text(text, chunk_size=256)

# Larger chunks = broader context but less precise
chunks = chunk_text(text, chunk_size=1024)
```

### Overlap Impact
```python
# No overlap = faster but may miss context at boundaries
chunks = chunk_text(text, overlap=0)

# High overlap = preserves context but more redundancy
chunks = chunk_text(text, overlap=100)
```

### Top-K Selection
```python
# Retrieve more candidates for post-processing
results = rag.query("q", top_k=10)

# Retrieve just essentials
results = rag.query("q", top_k=3)
```

## 🐛 Troubleshooting

### "OPENAI_API_KEY not set"
```powershell
# Set the variable correctly
$env:OPENAI_API_KEY = "sk-..."
# Verify it's set
$env:OPENAI_API_KEY
```

### "No such module: pypdf"
```bash
pip install pypdf
```

### "FAISS is not installed"
```bash
# Optional, for large datasets
pip install faiss-cpu
```

### "PDF extraction produces empty text"
- Check if PDF is text-based (not scanned images)
- Try with a different PDF
- Check file permissions

## 📈 Optimization Tips

1. **Reuse Embeddings**: Cache generated embeddings to avoid re-generating
2. **Batch Operations**: Process multiple queries together
3. **Semantic Chunking**: Use sentence-based chunking for better quality
4. **Use FAISS**: Switch to FAISS when scaling beyond 1000 chunks
5. **Implement Caching**: Store commonly accessed results

## 🚀 Next Steps

1. ✅ Test with `rag_playground.py`
2. ✅ Load your own PDF with `RAGSystem`
3. ✅ Integrate with your application
4. ✅ Add LLM-based answer generation
5. ✅ Consider vector database for persistence

## 📞 Quick API Reference

```python
# All imports you'll need
from rag_system import (
    RAGSystem,                      # Main class
    extract_text_from_pdf,          # PDF → text
    chunk_text,                     # Character-based chunks
    chunk_text_by_sentences,        # Sentence-based chunks
    generate_embeddings,            # Text → embeddings
    search_similar_chunks,          # Cosine similarity search
    search_with_faiss,              # FAISS search (optional)
    cosine_similarity,              # Manual similarity calculation
)
```

## 💡 Key Concepts

- **Embedding**: Vector representation of text (1536 dimensions for text-embedding-3-small)
- **Chunking**: Breaking text into manageable pieces
- **Similarity**: How related two embeddings are (0=unrelated, 1=identical)
- **Top-K**: Return K most relevant results
- **Context**: Retrieved text used to ground LLM responses
- **RAG**: Retrieval → Augment → Generate workflow
