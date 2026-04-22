# Schedule Validation Guide

## Overview

The schedule validation system helps ensure AI-generated pet schedules are:

- Complete: include feeding, exercise, and rest
- Realistic: avoid overly packed or vague routines
- Specific: include times and activity durations

This guide consolidates the content from:

- `VALIDATION_COMPLETE.md`
- `VALIDATION_INDEX.md`
- `VALIDATION_QUICK_REFERENCE.md`
- `VALIDATION_SYSTEM.md`

## Core Functions

### `validate_schedule(schedule_text: str) -> dict`

Validates a generated schedule using local checks only.

Returns:

```python
{
    "status": "valid" or "invalid",
    "issues": ["Issue 1", "Issue 2"],
    "summary": "Brief result summary",
    "task_count": 5
}
```

What it checks:

- Essential tasks: feeding, exercise, rest
- Timing information: specific times or time slots
- Task count: reasonable number of daily activities
- Duration information: estimated time for tasks
- Rest and sleep coverage

Example:

```python
from pawpal_system import validate_schedule

result = validate_schedule(schedule_text)

if result["status"] == "invalid":
    for issue in result["issues"]:
        print(issue)
```

### `review_and_fix_schedule(schedule_text, issues, pet_type, context) -> str`

Uses an LLM to improve a schedule based on validation issues.

What it does:

- Fixes missing or weak schedule elements
- Adds specific times
- Adds durations
- Balances feeding, exercise, and rest
- Explains scheduling choices

Example:

```python
from pawpal_system import validate_schedule, review_and_fix_schedule

validation = validate_schedule(schedule_text)

if validation["status"] == "invalid":
    improved = review_and_fix_schedule(
        schedule_text,
        validation["issues"],
        pet_type="dog",
        context="3-year-old Golden Retriever, active"
    )
    print(improved)
```

### `validate_and_fix_schedule(schedule_text, pet_type, context) -> dict`

Runs the full pipeline: validate first, then fix only if needed.

Returns:

```python
{
    "original_schedule": "...",
    "validation_result": {...},
    "is_valid": True,
    "improved_schedule": None
}
```

Example:

```python
from pawpal_system import validate_and_fix_schedule

result = validate_and_fix_schedule(
    schedule_text,
    pet_type="dog",
    context="Medium energy, suburban area"
)

if result["is_valid"]:
    print(result["original_schedule"])
else:
    print(result["improved_schedule"])
```

## Validation Checks

| Check | Looks For | Example Problem |
|------|------|------|
| Essential tasks | Feeding, exercise, rest | Missing exercise |
| Timing | `8:00 AM`, `morning`, `evening` | No time info |
| Task count | Reasonable daily workload | Too many tasks |
| Durations | `15 min`, `1 hour` | No time estimates |
| Rest time | Sleep, nap, downtime | No rest scheduled |

## Typical Workflow

```text
Generate schedule
    ↓
Validate
    ├─ Valid → Output original schedule
    └─ Invalid → Review and fix
                     ↓
               Output improved schedule
```

Full example:

```python
from pawpal_system import (
    generate_schedule_with_context,
    validate_and_fix_schedule
)

schedule = generate_schedule_with_context(
    user_input="Create a daily schedule for my dog",
    context="Active dog, suburban area"
)

result = validate_and_fix_schedule(
    schedule,
    pet_type="dog",
    context="Active dog, suburban area"
)

final_schedule = result["improved_schedule"] or result["original_schedule"]
print(final_schedule)
```

## Quick Usage Patterns

### Validate only

```python
validation = validate_schedule(schedule)
if validation["status"] == "valid":
    print("Schedule looks good")
else:
    print(validation["issues"])
```

### Auto-fix pipeline

```python
result = validate_and_fix_schedule(schedule, "dog", context)
use_schedule = result["improved_schedule"] or result["original_schedule"]
```

### Manual fix control

```python
validation = validate_schedule(schedule)
if validation["issues"]:
    fixed = review_and_fix_schedule(
        schedule,
        validation["issues"],
        "dog",
        context
    )
```

## Example Outcomes

### Valid schedule

```text
8:00 AM - Feed dog (10 min)
8:30 AM - Morning walk (30 min)
12:00 PM - Lunch feeding (10 min)
1:00 PM - Playtime (20 min)
6:00 PM - Dinner (10 min)
9:00 PM - Rest and sleep
```

Result:

- Status: valid
- Issues: none

### Invalid schedule

```text
8:00 AM - Feed dog
12:00 PM - Feed dog
Evening - Rest
```

Possible issues:

- Missing essential tasks: exercise
- Missing duration information
- Missing detailed timing

## Streamlit Integration

```python
from pawpal_system import validate_schedule, review_and_fix_schedule

schedule = generate_schedule_with_context(request, context)
validation = validate_schedule(schedule)

st.write(f"Status: {validation['status']}")

if validation["status"] == "invalid":
    st.warning(f"Issues found: {len(validation['issues'])}")
    for issue in validation["issues"]:
        st.write(f"- {issue}")

    if st.button("Improve Schedule"):
        improved = review_and_fix_schedule(
            schedule,
            validation["issues"],
            pet_type="dog",
            context=context
        )
        st.success("Schedule improved")
        st.write(improved)
```

## Demo Commands

### Validation tests

```bash
python test_validation.py
```

### Full validation workflow

```bash
python main.py validate
```

## Performance

- `validate_schedule()`: under 100ms
- `review_and_fix_schedule()`: around 2-5 seconds
- `validate_and_fix_schedule()`: under 100ms if already valid, otherwise around 2-5 seconds

## Customization

You can adjust the validation logic in `validate_schedule()` to be more strict or more lenient.

Examples:

```python
# Change the "too many tasks" threshold
if task_count > 20:
    issues.append("Schedule appears overly packed")
```

```python
# Add custom keyword groups
essential_tasks = {
    "feeding": ["feed", "meal", "food"],
    "exercise": ["walk", "play", "run"],
    "rest": ["rest", "sleep", "nap"],
}
```

You can also adjust the prompt in `review_and_fix_schedule()` to enforce style or domain-specific requirements.

## Error Handling

```python
try:
    result = validate_and_fix_schedule(schedule, "dog", context)
except ValueError as error:
    print(f"Validation error: {error}")
    result = {"original_schedule": schedule, "improved_schedule": None}
```

## Limitations

- Validation relies mostly on keyword matching
- Some valid schedules may be flagged if wording is unusual
- LLM fixes require `OPENAI_API_KEY`
- Improved schedules may still need human review

## File Map

Primary implementation files:

- `pawpal_system.py`: validation functions
- `main.py`: validation demo entry point
- `test_validation.py`: sample validation tests
- `STREAMLIT_INTEGRATION.md`: UI integration examples

## Summary

The validation system gives you three levels of control:

- Validate only
- Validate, then manually decide whether to fix
- Run the full validate-and-fix pipeline automatically

Use it when you want schedule output that is more complete, transparent, and safer to present to users.
