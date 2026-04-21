import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date, timedelta

from pawpal_system import Owner, Priority, Scheduler, Task, Pet


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


# ---------------------------------------------------------------------------
# Test 1 — Task Completion
# ---------------------------------------------------------------------------

def test_mark_complete_sets_flag(sample_task):
    """mark_complete() should flip is_completed from False to True."""
    assert sample_task.is_completed is False   # pre-condition
    sample_task.mark_complete()
    assert sample_task.is_completed is True    # post-condition


# ---------------------------------------------------------------------------
# Test 2 — Task Addition
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count(sample_pet, sample_task):
    """Adding a task to a pet should increase its task list length by 1."""
    before = len(sample_pet.tasks)
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == before + 1


def test_filter_tasks_by_completion_status():
    """Scheduler.filter_tasks() should return only tasks matching completion state."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "555-0101", "morning", 120)
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


def test_filter_tasks_by_pet_name():
    """Scheduler.filter_tasks() should return only tasks for the named pet."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "555-0101", "morning", 120)
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


def test_sort_by_time_returns_tasks_in_chronological_order():
    """Scheduler.sort_by_time() should order tasks from earliest to latest HH:MM."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "555-0101", "morning", 120)
    pet = Pet("P1", "Buddy", "Canine", "Labrador", 5)
    owner.add_pet(pet)

    midday_task = Task("T1", "Lunch", "Midday meal", 15, Priority.MEDIUM, "daily", "afternoon", "12:30")
    early_task = Task("T2", "Breakfast", "Morning meal", 10, Priority.HIGH, "daily", "morning", "07:15")
    late_task = Task("T3", "Evening walk", "Night exercise", 20, Priority.LOW, "daily", "evening", "18:45")

    scheduler = Scheduler("S1", owner)
    sorted_tasks = scheduler.sort_by_time([midday_task, late_task, early_task])

    assert sorted_tasks == [early_task, midday_task, late_task]


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


def test_detect_time_conflicts_returns_warning():
    """Scheduler.detect_time_conflicts() should warn when tasks share the same time."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "555-0101", "morning", 120)
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


def test_detect_time_conflicts_flags_duplicate_times():
    """Scheduler.detect_time_conflicts() should flag multiple incomplete tasks at the same time."""
    owner = Owner("O1", "Jordan", "jordan@example.com", "555-0101", "morning", 120)
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
