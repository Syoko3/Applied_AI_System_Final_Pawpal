import os
import re
from pathlib import Path
import uuid
import streamlit as st
from pawpal_system import generate_schedule_with_context, validate_schedule, parse_ai_tasks, Priority, Owner, Pet, Task
from rag_system import extract_text_from_pdf, save_uploaded_pdf, clear_data_directory, RAGSystem

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide", initial_sidebar_state="collapsed")

def ensure_session_state() -> None:
    defaults = {
        "pdf_names": [],
        "pdf_text": "",
        "pdf_contents": {},
        "rag_system": None,
        "retrieved_context": "",
        "schedule_text": "",
        "schedule_only": "",
        "explanation_only": "",
        "validation_result": None,
        "owner_name": "",
        "owner_time_range": "",
        "pet_name": "",
        "species": "",
        "pet_breed": "",
        "pet_age": 1,
        "tasks": [],
        "ai_tasks": [],
        "pets_list": [],
        "pet_expander_expanded": True,
        "task_expander_expanded": False,
        "pet_added_trigger": False,
        "task_added_trigger": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def process_uploaded_pdf(uploaded_file) -> tuple[str, RAGSystem]:
    # Save the uploaded file to the data folder permanently
    save_path = save_uploaded_pdf(uploaded_file.name, uploaded_file.getbuffer())

    pdf_text = extract_text_from_pdf(save_path)

    if not pdf_text.strip():
        raise ValueError("No readable text was extracted from the uploaded PDF.")

    rag = RAGSystem()
    rag.load_pdf(save_path, chunk_size=500, overlap=50)
    
    if not rag.chunks:
        raise ValueError("The PDF was processed, but no text chunks were created.")

    return pdf_text, rag

def retrieve_context(user_request: str, rag: RAGSystem, top_k: int = 4) -> str:
    """Smart retrieval that tries to find context for all entities mentioned."""
    # Split by pet names if multiple pets are involved for better coverage
    # (Simplified for now: just query the whole thing, but top_k is increased)
    results = rag.query(user_request, top_k=top_k)
    context_parts = [chunk for chunk, _score in results]
    
    # Ensure variety by checking if we have chunks for each pet
    # In a more complex version, we would loop through pets_list and query for each
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
    # Case-insensitive search for markers
    upper_text = response_text.upper()
    schedule_marker = "SCHEDULE:"
    explanation_marker = "EXPLANATION:"
    
    if schedule_marker in upper_text and explanation_marker in upper_text:
        s_idx = upper_text.index(schedule_marker) + len(schedule_marker)
        e_idx = upper_text.index(explanation_marker)
        
        # If markers are in the wrong order, or schedule is after explanation, handle gracefully
        if s_idx < e_idx:
            schedule = response_text[s_idx:e_idx].strip()
            explanation = response_text[e_idx + len(explanation_marker):].strip()
            return schedule, explanation

    return response_text.strip(), "No separate explanation section was found in the model output."

def reset_pipeline_outputs() -> None:
    st.session_state.retrieved_context = ""
    st.session_state.schedule_text = ""
    st.session_state.schedule_only = ""
    st.session_state.explanation_only = ""
    st.session_state.validation_result = None
    st.session_state.ai_tasks = []
    # Note: We keep pets_list and tasks as they are user-defined data

ensure_session_state()

st.title("🐾 PawPal+")
st.markdown('''
            Welcome to the PawPal+ Pet Care App!
            Enter your name and your pet information first.
            Then upload a pet care PDF and ask for a schedule.
            If you want, you can add your tasks and your requested time range.
            Run the full RAG + generation + validation pipeline.
            ''')

with st.sidebar:
    st.subheader("Settings & Maintenance")
    if st.button("🔄 Reset All App Data", use_container_width=True):
        # 1. Clear files
        files_deleted = clear_data_directory()
        # 2. Clear state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # st.success(f"Cleared state and deleted {files_deleted} files.") # Success msg might be lost on rerun, but let's try
        st.rerun()

    st.divider()
    st.caption("Current Memory Usage Optimization:")
    if st.session_state.pdf_names:
        st.info(f"Files Processed: {len(st.session_state.pdf_names)}")
        if st.button("🗑️ Clear Extracted Text Cache"):
            st.session_state.pdf_text = "[Cleared]"
            st.session_state.pdf_contents = {}
            st.rerun()

st.subheader("1. Owner Info")
st.caption("Enter your name and available time range.")
owner_c1, owner_c2 = st.columns(2)
with owner_c1:
    st.session_state.owner_name = st.text_input("Owner Name", value=st.session_state.owner_name, placeholder="e.g., Jordan")
with owner_c2:
    st.session_state.owner_time_range = st.text_input("Available Time Range", value=st.session_state.owner_time_range, placeholder="e.g., 08:00 - 10:00")

st.divider()

st.subheader("2. Manage Your Pets")
st.caption("Add one or more pets to your profile.")
 
# Pet Input Form
# Open by default only if no pets exist
pet_expanded = True if not st.session_state.pets_list else False

with st.container(key=f"pet_container_{len(st.session_state.pets_list)}"):
    with st.expander("➕ Add a New Pet", expanded=pet_expanded):
        with st.form("pet_form", clear_on_submit=True):
            pet_c1, pet_c2 = st.columns(2)
            with pet_c1:
                new_pet_name = st.text_input("Pet Name", placeholder="e.g., Mochi")
                new_species = st.text_input("Species", placeholder="e.g., Dog")
            with pet_c2:
                new_pet_breed = st.text_input("Breed", placeholder="e.g., Golden Retriever")
                new_pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
                
            if st.form_submit_button("Add Pet to List"):
                if new_pet_name and new_species:
                    pet_data = {
                        "pet_id": str(uuid.uuid4())[:8],
                        "name": new_pet_name,
                        "species": new_species,
                        "breed": new_pet_breed,
                        "age": new_pet_age
                    }
                    st.session_state.pets_list.append(pet_data)
                    st.success(f"Added {new_pet_name} to your pets!")
                    st.rerun() 
                else:
                    st.error("Pet Name and Species are required.")

# Display Added Pets
if st.session_state.pets_list:
    st.markdown("#### Your Pets")
    for i, p in enumerate(st.session_state.pets_list):
        col1, col2 = st.columns([4, 1])
        col1.info(f"**{p['name']}** ({p['species']}, {p['breed']}, {p['age']} years old)")
        if col2.button("🗑️", key=f"remove_pet_{p['pet_id']}"):
            st.session_state.pets_list.pop(i)
            st.rerun()
    
if not os.getenv("GEMINI_API_KEY"):
    st.warning("`GEMINI_API_KEY` is not set. PDF embeddings and schedule generation will fail until it is configured.")
    
st.divider()

st.subheader("3. Upload Pet Care PDF(s)")
st.caption("You can upload multiple PDFs if you have different guides for each pet.")
uploaded_pdfs = st.file_uploader("Upload PDF(s) of your pet's care information", type=["pdf"], accept_multiple_files=True)

if uploaded_pdfs:
    # Check if we have new files that aren't in our pdf_names list
    new_pdfs = [f for f in uploaded_pdfs if f.name not in st.session_state.pdf_names]
        
    if new_pdfs:
        if not st.session_state.rag_system:
            st.session_state.rag_system = RAGSystem()
            # st.session_state.pdf_text = "" # Keep previous text if any

        with st.spinner(f"Processing {len(new_pdfs)} new PDF(s) and updating embeddings..."):
            try:
                for uploaded_pdf in new_pdfs:
                    save_path = save_uploaded_pdf(uploaded_pdf.name, uploaded_pdf.getbuffer())
                    pdf_text = extract_text_from_pdf(save_path)
                        
                    # Store for individual preview
                    st.session_state.pdf_contents[uploaded_pdf.name] = pdf_text
                    
                    # Append text for legacy preview/logic
                    st.session_state.pdf_text += f"\n\n--- {uploaded_pdf.name} ---\n{pdf_text}"
                        
                    # Add to RAG system (appending)
                    st.session_state.rag_system.load_pdf(save_path, append=True)
                    st.session_state.pdf_names.append(uploaded_pdf.name)
                    
                    st.success(f"Successfully added {len(new_pdfs)} new PDF(s). Total chunks: {len(st.session_state.rag_system.chunks)}")
            except Exception as error:
                st.error(format_pipeline_error(error))
    
if st.session_state.rag_system and st.session_state.rag_system.chunks:
    info_col1, info_col2 = st.columns(2)
    info_col1.metric("Total Chunks", len(st.session_state.rag_system.chunks))
    info_col2.metric("Files Processed", len(st.session_state.pdf_names))
    
    with st.expander("Preview extracted PDF text"):
        if st.session_state.pdf_contents:
            for filename, text in st.session_state.pdf_contents.items():
                st.markdown(f"**File: {filename}**")
                st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
                st.divider()
        else:
            # Fallback for legacy data or if pdf_contents is empty but pdf_text isn't
            st.text(st.session_state.pdf_text[:5000])
    
st.divider()
    
st.subheader("4. Describe the Schedule You Want")
user_request = st.text_area(
    "What schedule should PawPal generate?",
    placeholder="Create a daily schedule for my 3-year-old Labrador with feeding, walks, training, and rest.",
    height=140,
)
    
st.divider()
    
st.subheader("5. Add Specific Tasks (Optional)")
st.caption("Provide manual tasks that the AI should incorporate into the final plan.")
    
# We want this to collapse every time a task is added
with st.container(key=f"task_container_{len(st.session_state.tasks)}"):
    with st.expander("➕ Add a New Task", expanded=False):
        with st.form("task_form", clear_on_submit=True):
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                new_task_name = st.text_input("Task Name", placeholder="e.g., Vet Appointment")
                if st.session_state.pets_list:
                    pet_options = [p['name'] for p in st.session_state.pets_list]
                    selected_pet_name = st.selectbox("For Pet", pet_options)
                else:
                    st.warning("Add a pet first.")
                    selected_pet_name = None
            with t_col2:
                new_task_time = st.time_input("Requested Time", value=None)
                new_task_pref_time = st.selectbox("Preferred Time Slot", ["morning", "afternoon", "evening", "night"])
            with t_col3:
                new_priority = st.selectbox("Priority", [p.name for p in Priority], index=1)
                new_task_duration = st.number_input("Duration (minutes)", min_value=5, max_value=1440, value=30, step=5)
        
            if st.form_submit_button("Add Task to List"):
                if not selected_pet_name:
                    st.error("Please add a pet first.")
                elif new_task_name:
                    task_obj = Task(
                        task_id=str(uuid.uuid4())[:8],
                        title=new_task_name,
                        description="",
                        duration=new_task_duration,
                        priority=Priority[new_priority],
                        preferred_time=new_task_pref_time,
                        time=new_task_time.strftime("%H:%M") if new_task_time else "Anytime"
                    )
                    # Store pet name temporarily in task object for display/logic
                    task_obj.pet_name = selected_pet_name 
                    st.session_state.tasks.append(task_obj)
                    st.success(f"Added task: {new_task_name} for {selected_pet_name}")
                    st.rerun()
                else:
                    st.error("Please enter a task name.")
    
if st.session_state.tasks:
    task_display = []
    for t in st.session_state.tasks:
        task_display.append({
            "Task": t.title,
            "Pet": getattr(t, 'pet_name', 'Unknown'),
            "Time": t.time,
            "Duration": f"{t.duration} min",
            "Priority": t.priority.name
        })
    st.table(task_display)
    
run_pipeline = st.button("Run Full Pipeline", type="primary", use_container_width=True)
    
if run_pipeline:
    if not st.session_state.pdf_names or not st.session_state.rag_system:
        st.error("Upload and process at least one PDF before running the pipeline.")
    elif not st.session_state.owner_name.strip() or not st.session_state.pets_list:
        st.error("Please provide Owner Name and at least one Pet.")
    elif not user_request.strip():
        st.error("Enter a schedule request first.")
    else:
        try:
            current_owner = Owner(
                owner_id="O-001",
                name=st.session_state.owner_name,
                daily_available_time_range=st.session_state.owner_time_range
            )
                
            pets_by_name = {}
            for p_data in st.session_state.pets_list:
                pet_obj = Pet(
                    pet_id=p_data["pet_id"],
                    name=p_data["name"],
                    species=p_data["species"],
                    breed=p_data["breed"],
                    age=p_data["age"]
                )
                current_owner.add_pet(pet_obj)
                pets_by_name[pet_obj.name] = pet_obj
    
            pet_info_summaries = []
            for p in current_owner.pets:
                pet_info_summaries.append(f"{p.name} ({p.age}-year-old {p.breed} {p.species})")
                
            profile_context = f"This is a schedule for {', '.join(pet_info_summaries)}, owned by {current_owner.name}."
            if st.session_state.owner_time_range:
                profile_context += f"\nOwner is available between {st.session_state.owner_time_range}."
    
            enhanced_request = f"{profile_context}\n\nRequest: {user_request}"
    
            if st.session_state.tasks:
                for task_obj in st.session_state.tasks:
                    pet_name = getattr(task_obj, 'pet_name', None)
                    if pet_name in pets_by_name:
                        pets_by_name[pet_name].add_task(task_obj)
                    
                manual_tasks_str = "\n".join([
                    f"- {t.title} for {t.pet.name} at {t.time} (Duration: {t.duration} min, Priority: {t.priority.name})" 
                    for _, t in current_owner.all_tasks()
                ])
                enhanced_request += f"\n\nPlease specifically include these tasks and organize the output with a separate schedule block for each pet:\n{manual_tasks_str}"
    
            with st.spinner("Retrieving relevant context from the PDF..."):
                retrieved_context = retrieve_context(
                    user_request=enhanced_request,
                    rag=st.session_state.rag_system,
                )
    
            with st.spinner("Generating schedule from retrieved context..."):
                schedule_text = generate_schedule_with_context(enhanced_request, retrieved_context)
    
            validation_result = validate_schedule(schedule_text, user_tasks=st.session_state.tasks)
                
            # --- FEEDBACK LOOP ---
            if validation_result["status"] == "invalid":
                with st.spinner("Initial schedule had issues. AI is reviewing and fixing..."):
                    from pawpal_system import review_and_fix_schedule
                        
                    # Determine primary pet type for context if possible
                    pet_type = "pets" 
                    if len(st.session_state.pets_list) == 1:
                        pet_type = st.session_state.pets_list[0]["species"]
                            
                    fixed_schedule_text = review_and_fix_schedule(
                        schedule_text=schedule_text,
                        issues=validation_result["issues"],
                        pet_type=pet_type,
                        context=retrieved_context
                    )
                        
                # Re-validate the fixed schedule
                new_validation = validate_schedule(fixed_schedule_text, user_tasks=st.session_state.tasks)
                        
                # Update local variables
                schedule_text = fixed_schedule_text
                validation_result = new_validation
                st.info("AI performed an automatic correction pass to improve the schedule.")
    
            schedule_only, explanation_only = split_schedule_response(schedule_text)
    
            st.session_state.retrieved_context = retrieved_context
            st.session_state.schedule_text = schedule_text
            st.session_state.schedule_only = schedule_only
            st.session_state.explanation_only = explanation_only
            st.session_state.validation_result = validation_result
            st.session_state.ai_tasks = parse_ai_tasks(schedule_only)
        except Exception as error:
            st.error(format_pipeline_error(error))
    
if st.session_state.schedule_text:
    st.divider()
    st.subheader("Results")
    
    result_col1, result_col2 = st.columns(2)
    with result_col1:
        st.markdown("### Schedule")
        st.markdown(st.session_state.schedule_only)
    
    with result_col2:
        st.markdown("### Explanation")
        st.write(st.session_state.explanation_only)
    
    st.markdown("### Validation Result")
    validation = st.session_state.validation_result
    if validation and "status" in validation:
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
            
        st.markdown("#### Validation Checks Performed")
        st.write([
            "✔ Required pet care tasks included",
            "✔ Schedule completeness checked",
            "✔ User-defined tasks included",
            "✔ Checked for time conflicts"
        ])
    
    # Combine manual and AI tasks for unified tracking
    all_trackable_tasks = []
    if st.session_state.tasks:
        all_trackable_tasks.extend(st.session_state.tasks)
    if st.session_state.ai_tasks:
        all_trackable_tasks.extend(st.session_state.ai_tasks)
        
    if all_trackable_tasks:
        st.divider()
        st.subheader("Task Tracking (AI Generated Schedule)")
        
        filter_col, pet_filter_col = st.columns([1, 2])
        with filter_col:
            st.caption("Status:")
            filter_option = st.radio("Status Filter", ["All", "Pending", "Completed"], horizontal=True, label_visibility="collapsed")
        
        with pet_filter_col:
            st.caption("Filter by Pet(s):")
            all_pets = sorted(list(set([getattr(t, 'pet_name', 'Unknown') for t in all_trackable_tasks])))
            selected_pets = st.multiselect("Pet Filter", all_pets, default=all_pets, label_visibility="collapsed")
                
        st.caption("Mark tasks as complete once you finish them:")
            
        # Apply filter
        display_tasks = all_trackable_tasks
        
        # 1. Filter by Status
        if filter_option == "Pending":
            display_tasks = [t for t in display_tasks if not t.is_completed]
        elif filter_option == "Completed":
            display_tasks = [t for t in display_tasks if t.is_completed]
            
        # 2. Filter by Pet
        if selected_pets:
            display_tasks = [t for t in display_tasks if getattr(t, 'pet_name', 'Unknown') in selected_pets]
        else:
            display_tasks = [] # If nothing selected, show nothing
                
        # Group by Pet for better organization
        tasks_by_pet = {}
        for t in display_tasks:
            p_name = getattr(t, 'pet_name', 'Unknown')
            if p_name not in tasks_by_pet:
                tasks_by_pet[p_name] = []
            tasks_by_pet[p_name].append(t)
                
        if not display_tasks:
            st.info(f"No {filter_option.lower()} tasks to show.")
        else:
            for p_name, p_tasks in tasks_by_pet.items():
                st.markdown(f"**🐾 {p_name}**")
                for task in sorted(p_tasks, key=lambda x: x.time):
                    # Show more info in the label
                    priority_label = f"[{task.priority.name}]"
                    display_label = f"**{task.time}** - {task.title} ({task.duration} min) {priority_label}"
                    
                    task.is_completed = st.checkbox(
                        display_label,
                        value=task.is_completed,
                        key=f"chk_{task.task_id}"
                    )
                    if task.rationale:
                        st.info(f"💡 {task.rationale}")
                st.write("") # Spacing

    st.subheader("Retrieved Context (Used for Generation)")
    st.caption("The following context was retrieved from the uploaded PDF and used to generate the schedule.")
    st.text(st.session_state.retrieved_context[:1500])

    with st.expander("Raw Model Output"):
        st.text(st.session_state.schedule_text)
