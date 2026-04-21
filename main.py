from pawpal_system import Task, Pet, Owner, Scheduler, Priority
import uuid
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def print_task_list(title, task_pairs):
    print(f"\n{title}")
    print("-" * len(title))
    for pet, task in task_pairs:
        status = "done" if task.is_completed else "pending"
        print(
            f"{task.time} | {pet.name:<4} | {task.title:<22} | "
            f"{task.priority.name:<8} | {status}"
        )


def run_test():
    owner = Owner(str(uuid.uuid4()), "Sohdai", "sohdai@gmail.com", "123-456-7890", "morning", 120)

    dog = Pet(str(uuid.uuid4()), "Dog", "Canine", "Labrador", 5)
    cat = Pet(str(uuid.uuid4()), "Cat", "Feline", "Siamese", 3)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # Add tasks out of order to demonstrate time sorting.
    task1 = Task("T1", "Feed the dog", "Care", 10, Priority.HIGH, "daily", "morning", "08:30")
    task2 = Task("T2", "Play with the cat", "Playing", 30, Priority.MEDIUM, "weekly", "morning", "08:30")
    task3 = Task("T3", "Take the dog for a walk", "Exercise", 60, Priority.HIGH, "weekly", "afternoon", "14:00")
    task4 = Task("T4", "Brush the cat", "Grooming", 15, Priority.LOW, "weekly", "evening", "21:00")
    task5 = Task("T5", "Give the dog medicine", "Medicine", 5, Priority.CRITICAL, "daily", "morning", "07:45")
    task4.mark_complete()

    dog.add_task(task1)
    dog.add_task(task3)
    dog.add_task(task5)
    cat.add_task(task2)
    cat.add_task(task4)

    scheduler = Scheduler(str(uuid.uuid4()), owner)

    all_tasks = owner.all_tasks()
    print_task_list("Tasks in added order", all_tasks)

    sorted_tasks = scheduler.sort_by_time([task for _, task in all_tasks])
    sorted_pairs = [(task.pet, task) for task in sorted_tasks]
    print_task_list("Tasks sorted by HH:MM time", sorted_pairs)

    print_task_list("Completed tasks only", scheduler.filter_tasks(is_completed=True))
    print_task_list("Cat tasks only", scheduler.filter_tasks(pet_name="Cat"))
    print_task_list(
        "Pending dog tasks only",
        scheduler.filter_tasks(is_completed=False, pet_name="Dog"),
    )

    conflict_warnings = scheduler.detect_time_conflicts()
    print("\nConflict warnings")
    print("-----------------")
    if conflict_warnings:
        for warning in conflict_warnings:
            print(warning)
    else:
        print("No time conflicts detected.")

    scheduler.generate_schedule()
    print("\nToday's Schedule:")
    if scheduler.generated_schedule and scheduler.generated_schedule.warnings:
        print("\nSchedule warnings")
        print("-----------------")
        for warning in scheduler.generated_schedule.warnings:
            print(warning)
    scheduler.display_plan()
    print(scheduler.explain_reasoning())


if __name__ == "__main__":
    run_test()
