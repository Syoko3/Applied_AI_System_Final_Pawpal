import pytest
import sys
import os
from unittest.mock import patch
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pawpal_system import (
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    generate_schedule_with_context,
    validate_schedule,
)
from rag_system import search_similar_chunks

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    """A reusable incomplete task for each test."""
    return Task(
        task_id="T1",
        title="Feed the dog",
        description="Morning feeding",
        duration=10,
        priority=Priority.HIGH,
        frequency="daily",
        preferred_time="morning",
    )

@pytest.fixture
def sample_pet():
    """A reusable pet with no tasks attached."""
    return Pet(
        pet_id="P1",
        name="Buddy",
        species="Canine",
        breed="Labrador",
        age=5,
    )

# Tests that marking a task complete changes its internal boolean state.
def test_mark_complete_sets_flag(sample_task):
    """mark_complete() should flip is_completed from False to True."""
    assert sample_task.is_completed is False   # pre-condition
    sample_task.mark_complete()
    assert sample_task.is_completed is True    # post-condition

# Tests that attaching a task correctly increments the pet's task counter.
def test_add_task_increases_pet_task_count(sample_pet, sample_task):
    """Adding a task to a pet should increase its task list length by 1."""
    before = len(sample_pet.tasks)
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == before + 1


# Tests that filtering tasks correctly isolates completed or incomplete tasks.
def test_filter_tasks_by_completion_status():
    """Scheduler.filter_tasks() should return only tasks matching completion state."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 18:00")
    pet = Pet("P1", "Buddy", "Canine", "Labrador", 5)
    owner.add_pet(pet)

    incomplete_task = Task("T1", "Morning walk", "Exercise", 20, Priority.HIGH, "daily", "morning")
    complete_task = Task("T2", "Give meds", "Medicine", 5, Priority.CRITICAL, "daily", "morning")
    complete_task.mark_complete()

    pet.add_task(incomplete_task)
    pet.add_task(complete_task)

    scheduler = Scheduler("S1", owner)

    filtered = scheduler.filter_tasks(is_completed=True)

    assert filtered == [(pet, complete_task)]


# Tests that the scheduler correctly retrieves tasks belonging only to a specific pet.
def test_filter_tasks_by_pet_name():
    """Scheduler.filter_tasks() should return only tasks for the named pet."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 18:00")
    dog = Pet("P1", "Buddy", "Canine", "Labrador", 5)
    cat = Pet("P2", "Mochi", "Feline", "Siamese", 3)
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog_task = Task("T1", "Morning walk", "Exercise", 20, Priority.HIGH, "daily", "morning")
    cat_task = Task("T2", "Clean litter box", "Care", 10, Priority.MEDIUM, "daily", "evening")
    dog.add_task(dog_task)
    cat.add_task(cat_task)

    scheduler = Scheduler("S1", owner)

    filtered = scheduler.filter_tasks(pet_name="mochi")

    assert filtered == [(cat, cat_task)]


# Tests that completing a daily task automatically generates an identical task for tomorrow.
def test_mark_complete_creates_next_daily_task(sample_pet, sample_task):
    """Completing a daily task should create a new incomplete task due tomorrow."""
    sample_pet.add_task(sample_task)

    next_task = sample_task.mark_complete()

    assert sample_task.is_completed is True
    assert next_task is not None
    assert next_task in sample_pet.tasks
    assert next_task.is_completed is False
    assert next_task.title == sample_task.title
    assert next_task.due_date == date.today() + timedelta(days=1)


# Tests that the scheduler correctly orders tasks based on their assigned time slots.
def test_sort_by_time_returns_tasks_in_chronological_order():
    """Scheduler.sort_by_time() should order tasks from earliest to latest HH:MM."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 18:00")
    pet = Pet("P1", "Buddy", "Canine", "Labrador", 5)
    owner.add_pet(pet)

    midday_task = Task("T1", "Lunch", "Midday meal", 15, Priority.MEDIUM, "daily", "afternoon", "12:30")
    early_task = Task("T2", "Breakfast", "Morning meal", 10, Priority.HIGH, "daily", "morning", "07:15")
    late_task = Task("T3", "Evening walk", "Night exercise", 20, Priority.LOW, "daily", "evening", "18:45")

    scheduler = Scheduler("S1", owner)
    sorted_tasks = scheduler.sort_by_time([midday_task, late_task, early_task])

    assert sorted_tasks == [early_task, midday_task, late_task]


# Tests that completing a weekly task successfully schedules the next occurrence seven days later.
def test_mark_complete_creates_next_weekly_task(sample_pet):
    """Completing a weekly task should create a new incomplete task due next week."""
    weekly_task = Task(
        task_id="T2",
        title="Bath time",
        description="Weekly grooming",
        duration=30,
        priority=Priority.MEDIUM,
        frequency="weekly",
        preferred_time="evening",
    )
    sample_pet.add_task(weekly_task)

    next_task = weekly_task.mark_complete()

    assert weekly_task.is_completed is True
    assert next_task is not None
    assert next_task in sample_pet.tasks
    assert next_task.due_date == date.today() + timedelta(weeks=1)


# Tests that scheduling concurrent tasks for different pets properly triggers a conflict warning.
def test_detect_time_conflicts_returns_warning():
    """Scheduler.detect_time_conflicts() should warn when tasks share the same time."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 18:00")
    dog = Pet("P1", "Buddy", "Canine", "Labrador", 5)
    cat = Pet("P2", "Mochi", "Feline", "Siamese", 3)
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog_task = Task("T1", "Morning walk", "Exercise", 20, Priority.HIGH, "daily", "morning", "08:00")
    cat_task = Task("T2", "Breakfast", "Feeding", 10, Priority.MEDIUM, "daily", "morning", "08:00")
    dog.add_task(dog_task)
    cat.add_task(cat_task)

    scheduler = Scheduler("S1", owner)
    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Morning walk [Buddy]" in warnings[0]
    assert "Breakfast [Mochi]" in warnings[0]


# Tests that multiple overlapping tasks for the exact same pet accurately trigger conflict warnings.
def test_detect_time_conflicts_flags_duplicate_times():
    """Scheduler.detect_time_conflicts() should flag multiple incomplete tasks at the same time."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 18:00")
    pet = Pet("P1", "Buddy", "Canine", "Labrador", 5)
    owner.add_pet(pet)

    breakfast = Task("T1", "Breakfast", "Morning feeding", 10, Priority.HIGH, "daily", "morning", "08:30")
    meds = Task("T2", "Medicine", "Morning meds", 5, Priority.CRITICAL, "daily", "morning", "08:30")
    pet.add_task(breakfast)
    pet.add_task(meds)

    scheduler = Scheduler("S1", owner)
    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "08:30" in warnings[0]
    assert "Breakfast [Buddy]" in warnings[0]
    assert "Medicine [Buddy]" in warnings[0]

class _FakeGeminiModels:
    def generate_content(self, **kwargs):
        return type(
            "Response",
            (),
            {
                "text": (
                    "SCHEDULE:\n"
                    "7:00 AM - Feed the dog\n"
                    "8:00 AM - Morning walk\n\n"
                    "EXPLANATION:\n"
                    "This schedule uses the retrieved context and provides a clear routine."
                )
            },
        )()


class _FakeGeminiClient:
    def __init__(self, api_key=None):
        self.models = _FakeGeminiModels()


def _fake_generate_embeddings(texts, model="gemini-embedding-001"):
    embeddings = []
    for text in texts:
        lowered = text.lower()
        embeddings.append(
            [
                1.0 if "exercise" in lowered or "walk" in lowered else 0.0,
                1.0 if "feed" in lowered or "meal" in lowered else 0.0,
                1.0 if "rest" in lowered or "sleep" in lowered else 0.0,
            ]
        )
    return embeddings


# Tests that calling the LLM returns the strictly formatted scheduling layout.
def test_schedule_generation_returns_output():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("pawpal_system.genai.Client", _FakeGeminiClient):
            result = generate_schedule_with_context(
                "Create a daily dog schedule",
                "The dog needs feeding, exercise, and rest.",
            )

    assert result
    assert "SCHEDULE:" in result
    assert "EXPLANATION:" in result


# Tests the system's ability to flag a generated schedule that drops essential tasks.
def test_validation_detects_missing_tasks():
    incomplete_schedule = """
    SCHEDULE:
    8:00 AM - Feed the dog
    12:00 PM - Lunch

    EXPLANATION:
    A short feeding-focused routine.
    """

    result = validate_schedule(incomplete_schedule)

    assert result["status"] == "invalid"
    assert result["issues"]
    assert any("Missing essential tasks" in issue for issue in result["issues"])


# Tests that the internal RAG algorithm accurately retrieves chunks based on semantic similarity.
def test_retrieval_returns_relevant_chunks():
    chunks = [
        "Dogs need daily exercise like walks and active play.",
        "Cats benefit from quiet rest and sleep during the day.",
        "Feeding should happen on a consistent schedule.",
    ]
    embeddings = _fake_generate_embeddings(chunks)

    with patch("rag_system.generate_embeddings", _fake_generate_embeddings):
        results = search_similar_chunks(
            "How much exercise does my dog need?",
            chunks,
            embeddings,
            top_k=2,
        )

    assert results
    assert "exercise" in results[0][0].lower() or "walk" in results[0][0].lower()


# Tests the entire end-to-end pipeline combining user tasks, time bounds, and RAG retrieval.
def test_rag_with_added_tasks():
    chunks = [
        "Dogs need daily exercise like walks and active play.",
        "Cats benefit from quiet rest and sleep during the day.",
        "Feeding should happen on a consistent schedule.",
    ]
    embeddings = _fake_generate_embeddings(chunks)

    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 18:00")
    pet = Pet("P1", "Max", "Dog", "Labrador", 3)
    owner.add_pet(pet)
    
    task1 = Task("T1", "Vet Appointment", "Checkup", 60, Priority.CRITICAL, "once", "morning", "09:00")
    pet.add_task(task1)
    
    profile_context = f"Owner is available between {owner.daily_available_time_range}."
    user_request = "Create a schedule."
    enhanced_request = f"{profile_context}\n\nRequest: {user_request}\n\nTasks:\n- {task1.title} at {task1.time}"
    
    with patch("rag_system.generate_embeddings", _fake_generate_embeddings):
        results = search_similar_chunks(
            enhanced_request,
            chunks,
            embeddings,
            top_k=2,
        )
    
    retrieved_context = "\n".join([chunk for chunk, _ in results])
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("pawpal_system.genai.Client", _FakeGeminiClient):
            schedule_result = generate_schedule_with_context(
                enhanced_request,
                retrieved_context,
            )
            
    assert schedule_result
    assert "SCHEDULE:" in schedule_result


# Tests that standard textual time boundaries correctly map into numerical minutes budgets.
def test_scheduler_parses_time_range():
    """Scheduler should properly parse string 'HH:MM - HH:MM' into total_time_available minutes."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 10:00")
    scheduler = Scheduler("S1", owner)
    assert scheduler.total_time_available == 120


# Tests that low-priority tasks are dropped when total task durations exceed the allotted time budget.
def test_scheduler_apply_constraints_drops_excess_tasks():
    """Scheduler should omit low-priority tasks if they exceed the time budget."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "08:00 - 10:00") # 120 mins
    pet = Pet("P1", "Max", "Dog", "Lab", 3)
    owner.add_pet(pet)
    
    t1 = Task("T1", "Task 1", "D1", 60, Priority.CRITICAL, "daily", "morning")
    t2 = Task("T2", "Task 2", "D2", 60, Priority.HIGH, "daily", "morning")
    t3 = Task("T3", "Task 3", "D3", 30, Priority.LOW, "daily", "morning")
    pet.add_task(t3)
    pet.add_task(t1)
    pet.add_task(t2)
    
    scheduler = Scheduler("S1", owner)
    scheduler.load_tasks()
    constrained = scheduler.apply_constraints()
    
    # Total available is 120. CRITICAL (60) and HIGH (60) should fit. LOW (30) gets dropped.
    assert len(constrained) == 2
    assert constrained[0][1] == t1
    assert constrained[1][1] == t2


# Tests that the system accurately saves an uploaded PDF file directly into the data folder.
def test_save_uploaded_pdf_creates_file():
    from rag_system import save_uploaded_pdf
    
    test_file_name = "test_upload_file.pdf"
    test_buffer = b"dummy pdf content"
    
    saved_path = save_uploaded_pdf(test_file_name, test_buffer)
    
    assert os.path.exists(saved_path)
    assert os.path.basename(saved_path) == test_file_name
    
    with open(saved_path, "rb") as f:
        assert f.read() == test_buffer
        
    # Cleanup
    os.remove(saved_path)
