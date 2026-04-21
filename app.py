import streamlit as st
from pawpal_system import Owner, Pet, Task, Priority, Scheduler
import uuid
from datetime import time
import re

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def build_task_table(task_pairs, time_overrides=None):
    rows = []
    for pet, task in task_pairs:
        rows.append(
            {
                "Time": (
                    time_overrides.get(task.task_id, task.time)
                    if time_overrides is not None
                    else task.time
                ),
                "Pet": pet.name,
                "Task": task.title,
                "Priority": task.priority.name.title(),
                "Duration (min)": task.duration,
                "Status": "Completed" if task.is_completed else "Pending",
                "Preferred Slot": task.preferred_time.title(),
            }
        )
    return rows


def build_scheduled_task_pairs(schedule):
    return [
        (entry.pet, entry.task)
        for entry in sorted(schedule.scheduled_tasks, key=lambda item: item.start_time)
    ]


def build_scheduled_time_map(schedule):
    return {
        entry.task.task_id: entry.start_time.strftime("%H:%M")
        for entry in schedule.scheduled_tasks
    }


def build_schedule_table(schedule):
    rows = []
    for entry in schedule.scheduled_tasks:
        rows.append(
            {
                "Start": entry.start_time.strftime("%I:%M %p"),
                "End": entry.end_time.strftime("%I:%M %p"),
                "Pet": entry.pet.name,
                "Task": entry.task.title,
                "Priority": entry.task.priority.name.title(),
                "Duration (min)": entry.task.duration,
                "Why It Was Chosen": entry.rationale_note,
            }
        )
    return rows


def strip_ansi(text):
    return ANSI_ESCAPE_RE.sub("", text)

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high", "critical"], index=2)

col4, col5, col6 = st.columns(3)
with col4:
    preferred_slot = st.selectbox(
        "Preferred Slot",
        ["morning", "afternoon", "evening", "night"],
        index=0,
    )
with col5:
    requested_time = st.time_input("Requested Time", value=time(8, 0), step=300)
with col6:
    frequency = st.selectbox("Frequency", ["daily", "weekly"], index=0)

if st.button("Add task"):
    st.session_state.tasks.append(
        {
            "task_id": str(uuid.uuid4())[:8],
            "pet_name": pet_name,
            "species": species,
            "title": task_title,
            "duration_minutes": int(duration),
            "priority": priority,
            "preferred_time": preferred_slot,
            "time": requested_time.strftime("%H:%M"),
            "frequency": frequency,
            "is_completed": False,
        }
    )

if st.session_state.tasks:
    st.success(f"{len(st.session_state.tasks)} task(s) ready for scheduling.")
    st.write("Current tasks:")
    st.table(st.session_state.tasks)

    st.markdown("### Update Task Status")
    selected_task_id = st.selectbox(
        "Choose a task",
        options=[task["task_id"] for task in st.session_state.tasks],
        format_func=lambda task_id: next(
            (
                f'{task["title"]} ({task["pet_name"]}) - '
                f'{"Completed" if task["is_completed"] else "Pending"}'
                for task in st.session_state.tasks
                if task["task_id"] == task_id
            ),
            task_id,
        ),
    )

    selected_task = next(
        task for task in st.session_state.tasks if task["task_id"] == selected_task_id
    )
    new_status = st.checkbox(
        "Mark as completed",
        value=selected_task["is_completed"],
        key=f"complete_{selected_task_id}",
    )

    if st.button("Save task status"):
        selected_task["is_completed"] = new_status
        st.success("Task status updated.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    # Replaced placeholders with the calls to the methods wrote in main.py
    if not st.session_state.tasks:
        st.error("Please add at least one task first!")
    else:
        current_owner = Owner(
            owner_id="O-001",
            name=owner_name,
            email="contact@example.com",
            phone="555-0199",
            preferred_schedule_time="morning",
            daily_time_available=120
        )
        pets_by_name = {}

        for t in st.session_state.tasks:
            pet_key = t["pet_name"].strip().lower()
            current_pet = pets_by_name.get(pet_key)

            if current_pet is None:
                current_pet = Pet(
                    pet_id=str(uuid.uuid4())[:8],
                    name=t["pet_name"],
                    species=t["species"],
                    breed="Mixed",
                    age=2
                )
                current_owner.add_pet(current_pet)
                pets_by_name[pet_key] = current_pet

            pri_enum = Priority[t["priority"].upper()]

            new_task = Task(
                task_id=t["task_id"],
                title=t["title"],
                description="User added task",
                duration=t["duration_minutes"],
                priority=pri_enum,
                frequency=t["frequency"],
                preferred_time=t["preferred_time"],
                time=t["time"],
                is_completed=t["is_completed"],
            )
            current_pet.add_task(new_task)
        
        planner = Scheduler(str(uuid.uuid4()), current_owner)
        daily_plan = planner.generate_schedule()
        scheduled_pairs = build_scheduled_task_pairs(daily_plan)
        scheduled_time_map = build_scheduled_time_map(daily_plan)
        sorted_pairs = scheduled_pairs
        pending_pairs = [(pet, task) for pet, task in scheduled_pairs if not task.is_completed]
        completed_pairs = planner.filter_tasks(is_completed=True)
        requested_time_conflicts = planner.detect_time_conflicts()

        st.success("🗓️ Schedule Successfully Generated!")

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Scheduled Tasks", len(daily_plan.scheduled_tasks))
        metric_col2.metric("Total Minutes", daily_plan.total_duration)
        metric_col3.metric("Requested-Time Conflicts", len(requested_time_conflicts))

        st.markdown("### Today's Schedule")
        if daily_plan.scheduled_tasks:
            st.table(build_schedule_table(daily_plan))
        else:
            st.warning("No tasks fit the current schedule constraints.")

        st.markdown("### Task Views")
        view1, view2 = st.columns(2)

        with view1:
            st.markdown("**Sorted by Time**")
            if sorted_pairs:
                st.table(build_task_table(sorted_pairs, scheduled_time_map))
            else:
                st.warning("No tasks available to sort.")

        with view2:
            st.markdown("**Pending Tasks Only**")
            if pending_pairs:
                st.table(build_task_table(pending_pairs, scheduled_time_map))
            else:
                st.success("Everything is completed.")

        st.markdown("### Status Checks")
        if completed_pairs:
            st.success(f"{len(completed_pairs)} completed task(s) found.")
            st.table(build_task_table(completed_pairs))
        else:
            st.warning("No completed tasks yet.")

        if requested_time_conflicts:
            st.caption(
                "These warnings refer to tasks that were given the same requested HH:MM time, "
                "not overlapping times in the generated schedule."
            )
            for warning in requested_time_conflicts:
                st.warning(warning)
        else:
            st.success("No requested-time conflicts detected.")

        with st.expander("Readable Schedule Summary"):
            st.text(strip_ansi(daily_plan.get_summary()))

        with st.expander("Why was this schedule chosen?"):
            st.text(strip_ansi(planner.explain_reasoning()))
