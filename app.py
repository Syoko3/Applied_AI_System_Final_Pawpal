import os
import tempfile

import streamlit as st

from pawpal_system import generate_schedule_with_context, validate_schedule
from rag_system import extract_text_from_pdf, chunk_text_by_sentences, generate_embeddings, search_similar_chunks


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")


def ensure_session_state() -> None:
    defaults = {
        "pdf_name": None,
        "pdf_text": "",
        "chunks": [],
        "embeddings": [],
        "retrieved_context": "",
        "schedule_text": "",
        "schedule_only": "",
        "explanation_only": "",
        "validation_result": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def process_uploaded_pdf(uploaded_file) -> tuple[str, list[str], list[list[float]]]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.getbuffer())
        temp_path = temp_pdf.name

    try:
        pdf_text = extract_text_from_pdf(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not pdf_text.strip():
        raise ValueError("No readable text was extracted from the uploaded PDF.")

    chunks = chunk_text_by_sentences(pdf_text, target_chunk_size=500)
    if not chunks:
        raise ValueError("The PDF was processed, but no text chunks were created.")

    embeddings = generate_embeddings(chunks)
    return pdf_text, chunks, embeddings


def retrieve_context(user_request: str, chunks: list[str], embeddings: list[list[float]], top_k: int = 3) -> str:
    results = search_similar_chunks(user_request, chunks, embeddings, top_k=top_k)
    context_parts = [chunk for chunk, _score in results]
    return "\n\n".join(context_parts)


def split_schedule_response(response_text: str) -> tuple[str, str]:
    schedule_marker = "SCHEDULE:"
    explanation_marker = "EXPLANATION:"

    if schedule_marker in response_text and explanation_marker in response_text:
        schedule_start = response_text.index(schedule_marker) + len(schedule_marker)
        explanation_start = response_text.index(explanation_marker)
        schedule = response_text[schedule_start:explanation_start].strip()
        explanation = response_text[explanation_start + len(explanation_marker):].strip()
        return schedule, explanation

    return response_text.strip(), "No separate explanation section was found in the model output."


def reset_pipeline_outputs() -> None:
    st.session_state.retrieved_context = ""
    st.session_state.schedule_text = ""
    st.session_state.schedule_only = ""
    st.session_state.explanation_only = ""
    st.session_state.validation_result = None


ensure_session_state()

st.title("🐾 PawPal+")
st.caption("Upload a pet care PDF, ask for a schedule, and run the full RAG + generation + validation pipeline.")

if not os.getenv("OPENAI_API_KEY"):
    st.warning("`OPENAI_API_KEY` is not set. PDF embeddings and schedule generation will fail until it is configured.")

st.subheader("1. Upload Pet Care PDF")
uploaded_pdf = st.file_uploader("Upload a PDF with pet care information", type=["pdf"])

if uploaded_pdf is not None:
    is_new_file = st.session_state.pdf_name != uploaded_pdf.name

    if is_new_file:
        reset_pipeline_outputs()
        with st.spinner("Processing PDF and generating embeddings..."):
            try:
                pdf_text, chunks, embeddings = process_uploaded_pdf(uploaded_pdf)
            except Exception as error:
                st.session_state.pdf_name = None
                st.session_state.pdf_text = ""
                st.session_state.chunks = []
                st.session_state.embeddings = []
                st.error(f"PDF processing failed: {error}")
            else:
                st.session_state.pdf_name = uploaded_pdf.name
                st.session_state.pdf_text = pdf_text
                st.session_state.chunks = chunks
                st.session_state.embeddings = embeddings
                st.success(f"Processed `{uploaded_pdf.name}` into {len(chunks)} chunks.")

if st.session_state.chunks:
    info_col1, info_col2 = st.columns(2)
    info_col1.metric("Chunks", len(st.session_state.chunks))
    info_col2.metric("Characters Extracted", len(st.session_state.pdf_text))

    with st.expander("Preview extracted PDF text"):
        st.text(st.session_state.pdf_text[:3000])

st.divider()

st.subheader("2. Describe the Schedule You Want")
user_request = st.text_area(
    "What schedule should PawPal generate?",
    placeholder="Create a daily schedule for my 3-year-old Labrador with feeding, walks, training, and rest.",
    height=140,
)

run_pipeline = st.button("Run Full Pipeline", type="primary", use_container_width=True)

if run_pipeline:
    if not uploaded_pdf or not st.session_state.chunks:
        st.error("Upload and process a PDF before running the pipeline.")
    elif not user_request.strip():
        st.error("Enter a schedule request first.")
    else:
        try:
            with st.spinner("Retrieving relevant context from the PDF..."):
                retrieved_context = retrieve_context(
                    user_request=user_request,
                    chunks=st.session_state.chunks,
                    embeddings=st.session_state.embeddings,
                )

            with st.spinner("Generating schedule from retrieved context..."):
                schedule_text = generate_schedule_with_context(user_request, retrieved_context)

            validation_result = validate_schedule(schedule_text)
            schedule_only, explanation_only = split_schedule_response(schedule_text)

            st.session_state.retrieved_context = retrieved_context
            st.session_state.schedule_text = schedule_text
            st.session_state.schedule_only = schedule_only
            st.session_state.explanation_only = explanation_only
            st.session_state.validation_result = validation_result
        except Exception as error:
            st.error(f"Pipeline failed: {error}")

if st.session_state.schedule_text:
    st.divider()
    st.subheader("Results")

    result_col1, result_col2 = st.columns(2)
    with result_col1:
        st.markdown("### Schedule")
        st.text(st.session_state.schedule_only)

    with result_col2:
        st.markdown("### Explanation")
        st.write(st.session_state.explanation_only)

    st.markdown("### Validation Result")
    validation = st.session_state.validation_result
    if validation["status"] == "valid":
        st.success(validation["summary"])
    else:
        st.error(validation["summary"])

    metrics_col1, metrics_col2 = st.columns(2)
    metrics_col1.metric("Status", validation["status"].title())
    metrics_col2.metric("Tasks Detected", validation["task_count"])

    if validation["issues"]:
        st.markdown("#### Issues Found")
        for issue in validation["issues"]:
            st.warning(issue)

    with st.expander("Retrieved Context"):
        st.text(st.session_state.retrieved_context)

    with st.expander("Raw Model Output"):
        st.text(st.session_state.schedule_text)

