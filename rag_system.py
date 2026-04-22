"""
Retrieval-Augmented Generation (RAG) System
Simple, modular implementation for PDF extraction, text chunking, embeddings, and similarity search.
"""

import os
import math
from typing import List, Tuple
from openai import OpenAI


# ---------------------------------------------------------------------------
# PDF Extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Extracted text as a single string
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ImportError: If pypdf is not installed
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "pypdf is required. Install it with: pip install pypdf"
        )
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    reader = PdfReader(pdf_path)
    text = ""
    
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text += f"\n--- Page {page_num + 1} ---\n{page_text}"
    
    return text.strip()


# ---------------------------------------------------------------------------
# Text Chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Number of characters per chunk
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    chunks = []
    step = chunk_size - overlap
    
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def chunk_text_by_sentences(
    text: str,
    target_chunk_size: int = 512,
) -> List[str]:
    """
    Split text into chunks based on sentence boundaries (more semantic).
    
    Args:
        text: Input text to chunk
        target_chunk_size: Target size for each chunk in characters
    
    Returns:
        List of text chunks
    """
    import re
    
    # Split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= target_chunk_size:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


# ---------------------------------------------------------------------------
# Embeddings Generation
# ---------------------------------------------------------------------------

def generate_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI API.
    
    Args:
        texts: List of text strings to embed
        model: OpenAI embedding model name
    
    Returns:
        List of embedding vectors (each is a list of floats)
    
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it before calling this function."
        )
    
    client = OpenAI(api_key=api_key)
    
    # Filter out empty texts
    texts = [t.strip() for t in texts if t.strip()]
    if not texts:
        return []
    
    response = client.embeddings.create(
        model=model,
        input=texts
    )
    
    # Extract embeddings from response, maintaining order
    embeddings = [item.embedding for item in response.data]
    return embeddings


# ---------------------------------------------------------------------------
# Similarity Search
# ---------------------------------------------------------------------------

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine similarity score (0 to 1)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a ** 2 for a in vec1))
    magnitude2 = math.sqrt(sum(b ** 2 for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def search_similar_chunks(
    query: str,
    chunks: List[str],
    embeddings: List[List[float]],
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Find the top-k most similar chunks to a query using cosine similarity.
    
    Args:
        query: Query string
        chunks: List of text chunks
        embeddings: Pre-computed embeddings for chunks
        top_k: Number of top results to return
    
    Returns:
        List of tuples (chunk_text, similarity_score) sorted by similarity
    
    Raises:
        ValueError: If chunks and embeddings have different lengths
    """
    if len(chunks) != len(embeddings):
        raise ValueError("Number of chunks and embeddings must match")
    
    if not chunks:
        return []
    
    # Generate embedding for query
    query_embedding = generate_embeddings([query])[0]
    
    # Calculate similarity for all chunks
    similarities = [
        (chunk, cosine_similarity(query_embedding, embedding))
        for chunk, embedding in zip(chunks, embeddings)
    ]
    
    # Sort by similarity and return top-k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def search_with_faiss(
    query: str,
    chunks: List[str],
    embeddings: List[List[float]],
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Find the top-k most similar chunks using FAISS (faster for large datasets).
    
    Args:
        query: Query string
        chunks: List of text chunks
        embeddings: Pre-computed embeddings for chunks
        top_k: Number of top results to return
    
    Returns:
        List of tuples (chunk_text, similarity_score) sorted by similarity
    
    Raises:
        ImportError: If faiss-cpu is not installed
        ValueError: If chunks and embeddings have different lengths
    """
    try:
        import faiss
        import numpy as np
    except ImportError:
        raise ImportError(
            "faiss-cpu is required for this function. "
            "Install it with: pip install faiss-cpu"
        )
    
    if len(chunks) != len(embeddings):
        raise ValueError("Number of chunks and embeddings must match")
    
    if not chunks:
        return []
    
    # Convert embeddings to numpy array and build FAISS index
    embeddings_array = np.array(embeddings).astype(np.float32)
    dimension = embeddings_array.shape[1]
    
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    # Generate query embedding and search
    query_embedding = generate_embeddings([query])[0]
    query_array = np.array([query_embedding]).astype(np.float32)
    
    distances, indices = index.search(query_array, min(top_k, len(chunks)))
    
    # Return chunks with similarity scores (convert L2 distance to similarity)
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        # Convert L2 distance to similarity score (1 / (1 + distance))
        similarity = 1.0 / (1.0 + distance)
        results.append((chunks[int(idx)], float(similarity)))
    
    return results


# ---------------------------------------------------------------------------
# Main RAG Pipeline
# ---------------------------------------------------------------------------

class RAGSystem:
    """
    Simple RAG system combining PDF extraction, chunking, embeddings, and search.
    """
    
    def __init__(self, use_faiss: bool = False):
        """
        Initialize RAG system.
        
        Args:
            use_faiss: If True, use FAISS for similarity search (faster for large datasets)
        """
        self.chunks = []
        self.embeddings = []
        self.use_faiss = use_faiss
    
    def load_pdf(self, pdf_path: str, chunk_size: int = 512, overlap: int = 50) -> None:
        """
        Load and process a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
        """
        text = extract_text_from_pdf(pdf_path)
        self.chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        print(f"Extracted {len(self.chunks)} chunks from PDF")
        
        # Generate embeddings
        self.embeddings = generate_embeddings(self.chunks)
        print(f"Generated embeddings for {len(self.embeddings)} chunks")
    
    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Search for relevant chunks based on query.
        
        Args:
            query_text: User query string
            top_k: Number of results to return
        
        Returns:
            List of tuples (chunk_text, similarity_score)
        """
        if not self.chunks or not self.embeddings:
            raise RuntimeError("No documents loaded. Call load_pdf() first.")
        
        if self.use_faiss:
            return search_with_faiss(query_text, self.chunks, self.embeddings, top_k)
        else:
            return search_similar_chunks(query_text, self.chunks, self.embeddings, top_k)
    
    def get_context(self, query_text: str, top_k: int = 5) -> str:
        """
        Get relevant context as a single formatted string.
        
        Args:
            query_text: User query string
            top_k: Number of results to include
        
        Returns:
            Formatted context string
        """
        results = self.query(query_text, top_k)
        
        context_lines = [f"Query: {query_text}\n", "Relevant Context:"]
        for i, (chunk, score) in enumerate(results, 1):
            context_lines.append(f"\n[Result {i}] (similarity: {score:.3f})")
            context_lines.append(f"{chunk[:200]}..." if len(chunk) > 200 else chunk)
        
        return "\n".join(context_lines)
