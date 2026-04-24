import os
import tempfile
from pathlib import Path
import uuid
import streamlit as st
from pawpal_system import generate_schedule_with_context, validate_schedule, Priority, Owner, Pet, Task
from rag_system import extract_text_from_pdf, chunk_text_by_sentences, generate_embeddings, search_similar_chunks, save_uploaded_pdf

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)

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
        "owner_name": "",
        "owner_email": "",
        "owner_time_range": "",
        "pet_name": "",
        "species": "",
        "pet_breed": "",
        "pet_age": 1,
        "tasks": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def process_uploaded_pdf(uploaded_file) -> tuple[str, list[str], list[list[float]]]:
    # Save the uploaded file to the data folder permanently
    save_path = save_uploaded_pdf(uploaded_file.name, uploaded_file.getbuffer())

    pdf_text = extract_text_from_pdf(save_path)

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

def format_pipeline_error(error: Exception) -> str:
    """Convert raw API errors into friendlier Streamlit messages."""
    error_text = str(error)
    upper_text = error_text.upper()

    if "503" in error_text or "UNAVAILABLE" in upper_text or "HIGH DEMAND" in upper_text:
        return (
            "⚠️ Gemini is temporarily overloaded right now. Please try again in a minute. "
            "The app also retries automatically and falls back to a lighter model."
        )

    if "429" in error_text or "RESOURCE_EXHAUSTED" in upper_text or "QUOTA" in upper_text:
        return (
            "⚠️ Gemini API Quota Exceeded. You've hit the Free Tier limit (likely the 15 requests per minute limit). "
            "Please wait about 60 seconds and try again!"
        )

    if "GEMINI_API_KEY" in error_text:
        return "GEMINI_API_KEY is missing or not loaded. Add it to `.env` and restart Streamlit."

    if "API KEY" in upper_text or "API_KEY" in upper_text or "UNAUTHENTICATED" in upper_text:
        return "The Gemini API key appears invalid. Double-check `GEMINI_API_KEY` in `.env`."

    return f"Pipeline failed: {error}"

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
st.markdown('''
            Welcome to the PawPal+ Pet Care App!
            Enter your name and your pet information first.
            Then upload a pet care PDF and ask for a schedule.
            If you want, you can add your tasks and your requested time range.
            Run the full RAG + generation + validation pipeline.
            ''')

st.subheader("1. Owner and Pet Info")
st.caption("Enter your information and your pet's information.")
st.markdown("**Owner Details**")
owner_c1, owner_c2, owner_c3 = st.columns(3)
with owner_c1:
    st.session_state.owner_name = st.text_input("Owner Name", value=st.session_state.owner_name, placeholder="e.g., Jordan")
with owner_c2:
    st.session_state.owner_email = st.text_input("Email", value=st.session_state.owner_email, placeholder="e.g., jordan@example.com")
with owner_c3:
    st.session_state.owner_time_range = st.text_input("Available Time Range", value=st.session_state.owner_time_range, placeholder="e.g., 08:00 - 10:00")

st.markdown("**Pet Details**")
pet_c1, pet_c2, pet_c3, pet_c4 = st.columns(4)
with pet_c1:
    st.session_state.pet_name = st.text_input("Pet Name", value=st.session_state.pet_name, placeholder="e.g., Mochi")
with pet_c2:
    st.session_state.species = st.text_input("Species", value=st.session_state.species, placeholder="e.g., Dog")
with pet_c3:
    st.session_state.pet_breed = st.text_input("Breed", value=st.session_state.pet_breed, placeholder="e.g., Golden Retriever")
with pet_c4:
    st.session_state.pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=st.session_state.pet_age)

if not os.getenv("GEMINI_API_KEY"):
    st.warning("`GEMINI_API_KEY` is not set. PDF embeddings and schedule generation will fail until it is configured.")

st.divider()

st.subheader("2. Upload Pet Care PDF")
uploaded_pdf = st.file_uploader("Upload a PDF of your pet's care information", type=["pdf"])

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
                st.error(format_pipeline_error(error))
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

st.subheader("3. Describe the Schedule You Want")
user_request = st.text_area(
    "What schedule should PawPal generate?",
    placeholder="Create a daily schedule for my 3-year-old Labrador with feeding, walks, training, and rest.",
    height=140,
)

st.divider()

st.subheader("4. Add Specific Tasks (Optional)")
st.caption("Provide manual tasks that the AI should incorporate into the final plan.")

t_col1, t_col2, t_col3 = st.columns(3)
with t_col1:
    new_task_name = st.text_input("Task Name", placeholder="e.g., Vet Appointment")
    new_priority = st.selectbox("Priority", [p.name for p in Priority], index=1)
with t_col2:
    new_task_time = st.time_input("Requested Time", value=None)
    new_task_pref_time = st.selectbox("Preferred Time Slot", ["morning", "afternoon", "evening", "night"])
with t_col3:
    new_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    new_task_duration = st.number_input("Duration (minutes)", min_value=5, max_value=1440, value=30, step=5)

if st.button("Add Task to List"):
    if new_task_name:
        task_obj = Task(
            task_id=str(uuid.uuid4())[:8],
            title=new_task_name,
            description="",
            duration=new_task_duration,
            priority=Priority[new_priority],
            frequency=new_frequency,
            preferred_time=new_task_pref_time,
            time=new_task_time.strftime("%H:%M") if new_task_time else "Anytime"
        )
        st.session_state.tasks.append(task_obj)
        st.success(f"Added task: {new_task_name}")
    else:
        st.error("Please enter a task name.")

if st.session_state.tasks:
    task_display = []
    for t in st.session_state.tasks:
        task_display.append({
            "Task": t.title,
            "Time": t.time,
            "Duration": f"{t.duration} min",
            "Priority": t.priority.name,
            "Frequency": t.frequency
        })
    st.table(task_display)

run_pipeline = st.button("Run Full Pipeline", type="primary", use_container_width=True)

if run_pipeline:
    if not uploaded_pdf or not st.session_state.chunks:
        st.error("Upload and process a PDF before running the pipeline.")
    elif not st.session_state.owner_name.strip() or not st.session_state.pet_name.strip() or not st.session_state.species.strip():
        st.error("Please provide Owner Name, Pet Name, and Species.")
    elif not user_request.strip():
        st.error("Enter a schedule request first.")
    else:
        try:
            current_owner = Owner(
                owner_id="O-001",
                name=st.session_state.owner_name,
                email=st.session_state.owner_email,
                daily_available_time_range=st.session_state.owner_time_range
            )
            
            current_pet = Pet(
                pet_id="P-001",
                name=st.session_state.pet_name,
                species=st.session_state.species,
                breed=st.session_state.pet_breed,
                age=st.session_state.pet_age
            )
            current_owner.add_pet(current_pet)

            profile_context = f"This is a schedule for {current_pet.name} (a {current_pet.age}-year-old {current_pet.breed} {current_pet.species}), owned by {current_owner.name}."
            if st.session_state.owner_time_range:
                profile_context += f"\nOwner is available between {st.session_state.owner_time_range}."

            enhanced_request = f"{profile_context}\n\nRequest: {user_request}"

            if st.session_state.tasks:
                for task_obj in st.session_state.tasks:
                    current_pet.add_task(task_obj)
                
                manual_tasks_str = "\n".join([
                    f"- {t.title} at {t.time} (Duration: {t.duration} min, Priority: {t.priority.name}, Frequency: {t.frequency})" 
                    for t in current_pet.tasks
                ])
                enhanced_request += f"\n\nIn addition to the description above, please specifically include these tasks:\n{manual_tasks_str}"

            with st.spinner("Retrieving relevant context from the PDF..."):
                retrieved_context = retrieve_context(
                    user_request=enhanced_request,
                    chunks=st.session_state.chunks,
                    embeddings=st.session_state.embeddings,
                )

            with st.spinner("Generating schedule from retrieved context..."):
                schedule_text = generate_schedule_with_context(enhanced_request, retrieved_context)

            validation_result = validate_schedule(schedule_text, user_tasks=st.session_state.tasks)
            schedule_only, explanation_only = split_schedule_response(schedule_text)

            st.session_state.retrieved_context = retrieved_context
            st.session_state.schedule_text = schedule_text
            st.session_state.schedule_only = schedule_only
            st.session_state.explanation_only = explanation_only
            st.session_state.validation_result = validation_result
        except Exception as error:
            st.error(format_pipeline_error(error))

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

    if st.session_state.tasks:
        st.divider()
        st.subheader("Task Tracking")
        
        filter_col, _ = st.columns([1, 2])
        with filter_col:
            filter_option = st.radio("Filter:", ["All", "Pending", "Completed"], horizontal=True, label_visibility="collapsed")
            
        st.caption("Mark your custom tasks as complete once you finish them:")
        
        # Apply filter
        display_tasks = st.session_state.tasks
        if filter_option == "Pending":
            display_tasks = [t for t in st.session_state.tasks if not t.is_completed]
        elif filter_option == "Completed":
            display_tasks = [t for t in st.session_state.tasks if t.is_completed]
            
        if not display_tasks:
            st.info(f"No {filter_option.lower()} tasks to show.")
        else:
            for task in display_tasks:
                task.is_completed = st.checkbox(
                    f"{task.title} at {task.time} ({task.duration} min, {task.priority.name} Priority)",
                    value=task.is_completed,
                    key=f"chk_{task.task_id}"
                )

    with st.expander("Retrieved Context"):
        st.text(st.session_state.retrieved_context)

    with st.expander("Raw Model Output"):
        st.text(st.session_state.schedule_text)
