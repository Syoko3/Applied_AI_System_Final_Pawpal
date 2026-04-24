# PawPal Project Guide

Welcome to the comprehensive guide for **PawPal+**, an AI-powered pet care assistant that leverages Retrieval-Augmented Generation (RAG) and the Gemini API to create, validate, and track personalized pet schedules.

---

## 🛠️ System Architecture

The project is structured into modular components, each handling a specific layer of the application logic:

- **`app.py`**: The primary user interface built with Streamlit. It manages the end-to-end pipeline from PDF upload and RAG retrieval to schedule generation and interactive task tracking.
- **`pawpal_system.py`**: The core engine containing data models (`Owner`, `Pet`, `Task`), scheduling algorithms, Gemini API integration, and heuristic validation logic.
- **`rag_system.py`**: The document intelligence layer. Handles PDF text extraction, sentence-based chunking, embedding generation, and vector similarity search (supporting both Cosine Similarity and FAISS).
- **`main.py`**: A CLI-based playground for developers to test RAG performance, validation workflows, and system integration without the UI.
- **`test_pawpal.py`**: A comprehensive test suite using `pytest` to ensure reliability across scheduling logic, conflict detection, and API interactions.

---

## 📋 Data Models

The system uses a hierarchical data model to represent the relationships between owners, pets, and their care requirements.

### `Owner`
Represents the user of the system.
- **Attributes**: `owner_id`, `name`, `daily_available_time_range`, `preferences`.
- **Key Methods**: `add_pet()`, `all_tasks()`, `get_schedule()`.
- *Note: Email address has been removed to prioritize user privacy.*

### `Pet`
Represents a pet belonging to an owner.
- **Attributes**: `pet_id`, `name`, `species`, `breed`, `age`, `medical_notes`.
- **Key Methods**: `add_task()`, `get_tasks()`, `update_info()`.

### `Task`
Represents a specific activity (e.g., feeding, walking).
- **Attributes**: `task_id`, `title`, `description`, `duration`, `priority` (Enum), `preferred_time`, `time`, `due_date`, `is_completed`.

---

## 🚀 App Pipeline

The Streamlit application implements a sophisticated RAG-driven pipeline:

1.  **Ingestion**: User uploads a pet care PDF.
2.  **Extraction**: `pypdf` extracts raw text from the document.
3.  **Chunking**: Text is split into meaningful segments using sentence-based chunking.
4.  **Embedding**: Gemini API generates high-dimensional vectors for each chunk.
5.  **Retrieval**: Based on the user's request and pet profile, the system retrieves the top $k$ most relevant context chunks.
6.  **Generation**: Gemini generates a structured daily schedule incorporating both retrieved context and manual user tasks.
7.  **Validation**: The system runs a heuristic check for completeness (feeding, exercise, rest) and time conflicts.
8.  **Interaction**: Users can mark tasks as completed directly in the UI.

---

## 🔍 Validation & Intelligence

### Schedule Validation
The `validate_schedule()` function ensures generated plans are realistic and safe:
- **Essential Coverage**: Checks for feeding, exercise, and rest.
- **Temporal Consistency**: Identifies time conflicts and missing duration info.
- **Constraint Compliance**: Ensures tasks fit within the owner's specified time range.

### Automatic Refinement
Invalid schedules can be automatically improved using `review_and_fix_schedule()`, which feeds validation issues back into Gemini for a corrected output.

---

## 📦 Requirements & Setup

Dependencies are managed via `requirements.txt`:
```txt
streamlit==1.32.2
pytest>=7.0
numpy==1.26.4
google-genai>=1.30.0
pypdf>=4.0.0
faiss-cpu>=1.7.0
python-dotenv>=1.0.0
```

### Environment Variables
A `.env` file is required in the root directory:
```bash
GEMINI_API_KEY=your_api_key_here
```

---

## ⚠️ Known Limitations
- **API Dependency**: Requires an active Gemini API key for embeddings and generation.
- **Statelessness**: Vector storage is in-memory; embeddings are regenerated per session.
- **Heuristics**: Validation is keyword-based and may occasionally flag valid creative schedules as missing essential items.

---

## 📝 Summary
PawPal+ transforms static pet care documents into dynamic, actionable daily plans. By combining the reasoning of LLMs with the grounding of RAG, it provides a reliable and personalized care assistant for every pet owner.
