# Schedule Validation & Improvement System

## Overview

The validation system ensures AI-generated pet schedules are:
✅ **Complete** - Include essential tasks (feeding, exercise, rest)  
✅ **Realistic** - Reasonable task load and proper timing  
✅ **Specific** - Include times and durations  

## Functions

### 1. `validate_schedule(schedule_text: str) -> dict`

Validates a schedule and returns issues found.

**Parameters:**
- `schedule_text`: The schedule to validate

**Returns:**
```python
{
    "status": "valid" or "invalid",
    "issues": [...],  # List of problems
    "summary": "...", # Brief description
    "task_count": 5   # Number of tasks detected
}
```

**Checks:**
- Missing essential tasks (feeding, exercise, rest)
- Missing timing information (times/time slots)
- Task realism (not too packed, not too sparse)
- Missing duration information
- Lack of rest/sleep time

**Example:**
```python
from pawpal_system import validate_schedule

schedule = "8am walk, 12pm feed, rest"
result = validate_schedule(schedule)

if result['status'] == 'invalid':
    for issue in result['issues']:
        print(f"- {issue}")
```

### 2. `review_and_fix_schedule(schedule_text, issues, pet_type, context) -> str`

Uses LLM to improve a schedule based on validation issues.

**Parameters:**
- `schedule_text`: Original schedule
- `issues`: List of validation issues to fix
- `pet_type`: Type of pet (e.g., "dog", "cat")
- `context`: Additional pet info (optional)

**Returns:**
- Improved schedule with specific times, durations, and explanations

**Features:**
- Fixes all identified issues
- Adds specific times (e.g., 8:00 AM)
- Includes activity durations
- Explains scheduling decisions
- Lists key improvements made

**Example:**
```python
from pawpal_system import validate_schedule, review_and_fix_schedule

schedule = generate_schedule_with_context(request, context)
validation = validate_schedule(schedule)

if validation['status'] == 'invalid':
    improved = review_and_fix_schedule(
        schedule,
        validation['issues'],
        pet_type="dog",
        context="3-year-old Golden Retriever, active"
    )
    print(improved)
```

### 3. `validate_and_fix_schedule(schedule_text, pet_type, context) -> dict`

Complete pipeline: validate and automatically fix if needed.

**Parameters:**
- `schedule_text`: Schedule to validate
- `pet_type`: Type of pet
- `context`: Pet information

**Returns:**
```python
{
    "original_schedule": "...",
    "validation_result": {...},  # From validate_schedule()
    "is_valid": True/False,
    "improved_schedule": "..." or None
}
```

**Example:**
```python
from pawpal_system import validate_and_fix_schedule

result = validate_and_fix_schedule(
    schedule_text=schedule,
    pet_type="dog",
    context="Medium energy, suburban area"
)

if result['is_valid']:
    print("✅ Schedule is valid!")
else:
    print("⚠️  Issues found:")
    for issue in result['validation_result']['issues']:
        print(f"  - {issue}")
    print("\n✅ Improved schedule:")
    print(result['improved_schedule'])
```

## Validation Checks Explained

### 1. Essential Tasks Check
- **Looks for:** Feeding, exercise, rest
- **Why:** Complete care requires all three
- **Example issue:** "Missing essential tasks: Exercise, Rest"

### 2. Timing Information Check
- **Looks for:** Specific times (8:00 AM, 2:30 PM) or time slots (morning, afternoon)
- **Why:** Owners need to know when activities occur
- **Example issue:** "Missing timing information. Schedule should include specific times"

### 3. Task Count Check
- **Looks for:** Reasonable number of tasks (3-10 is typical)
- **Why:** Too many = unrealistic; too few = incomplete
- **Example issue:** "Schedule appears overly packed"

### 4. Duration Information Check
- **Looks for:** Time estimates for activities (15 min, 1 hour)
- **Why:** Owners need to plan their day
- **Example issue:** "Missing duration information for tasks"

### 5. Rest Time Check
- **Looks for:** Explicit rest, sleep, or nap times
- **Why:** Pets need significant daily sleep (dogs: 12-14 hrs, cats: 12-16 hrs)
- **Example issue:** "No explicit rest or sleep time scheduled"

## Complete Workflow: Generate → Validate → Fix

```python
from pawpal_system import (
    generate_schedule_with_context,
    validate_and_fix_schedule
)

# STEP 1: Generate
schedule = generate_schedule_with_context(
    user_input="Schedule for my 3-year-old dog",
    context="Golden Retriever, active, suburban"
)

# STEP 2: Validate & Fix (complete pipeline)
result = validate_and_fix_schedule(
    schedule,
    pet_type="dog",
    context="3-year-old Golden Retriever"
)

# STEP 3: Output
if result['is_valid']:
    print("✅ Generated schedule is valid!")
    print(result['original_schedule'])
else:
    print("⚠️  Schedule improved based on validation")
    print(result['improved_schedule'])
```

## Running the Demo

### Basic test (original functionality)
```bash
python main.py
```

### Validation demo (new functionality)
```bash
python main.py validate
```

The validation demo shows:
1. Schedule generation
2. Validation with issue detection
3. Schedule improvement
4. Complete pipeline execution

## Integration with Streamlit

To add validation to `app.py`:

```python
from pawpal_system import validate_schedule, review_and_fix_schedule

# After generating schedule
if st.button("Generate Schedule"):
    schedule = generate_schedule_with_context(request, context)
    
    # Validate
    validation = validate_schedule(schedule)
    
    st.write(f"Status: {validation['status']}")
    
    if validation['status'] == 'invalid':
        st.warning(f"Issues found ({len(validation['issues'])})")
        for issue in validation['issues']:
            st.write(f"- {issue}")
        
        # Fix
        if st.button("Improve Schedule"):
            improved = review_and_fix_schedule(
                schedule,
                validation['issues'],
                pet_type="dog"
            )
            st.success("Schedule improved!")
            st.write(improved)
```

## Customization

### Adjust validation sensitivity

Modify these in `validate_schedule()`:

```python
# Task count thresholds
if task_count > 15:  # Change to > 20 for more lenient
    issues.append("Schedule appears overly packed")

# Essential task keywords
essential_tasks = {
    "feeding": ["feed", "meal", ...],  # Add/remove keywords
    "exercise": ["walk", "play", ...],
    "rest": ["sleep", "rest", ...]
}
```

### Customize LLM improvements

Modify the prompt in `review_and_fix_schedule()`:

```python
prompt = f"""...
# Add specific requirements:
- Include water breaks
- Include outdoor time
- Consider weather
..."""
```

## Common Scenarios

### Scenario 1: Incomplete Schedule
**Original:** "8am walk, rest"  
**Issues:** Missing feeding, exercise; no timing  
**Fixed:** Adds feeding times, exercise duration, sleep periods

### Scenario 2: Overpacked Schedule
**Original:** 15+ activities listed  
**Issues:** Unrealistic schedule  
**Fixed:** Consolidates activities, creates manageable routine

### Scenario 3: Valid Schedule
**Original:** "8am feed, 9am walk (30min), 12pm play (20min), evening rest"  
**Result:** ✅ Valid - no improvements needed

## Best Practices

1. **Always validate** - Generated schedules may miss details
2. **Review improvements** - AI fixes are suggestions, not requirements
3. **Customize for pet** - Use `context` parameter for specific needs
4. **Handle errors** - Wrap in try-except for production use
5. **Show validation feedback** - Users appreciate transparency

## Error Handling

```python
from pawpal_system import validate_schedule

try:
    validation = validate_schedule(schedule)
    if validation['status'] == 'invalid':
        # Handle issues
        pass
except Exception as e:
    print(f"Validation error: {e}")
    # Fallback logic
```

## Performance

- **validate_schedule()**: <100ms (local checks)
- **review_and_fix_schedule()**: 2-5 seconds (LLM call)
- **validate_and_fix_schedule()**: 2-5 seconds (both)

## Limitations

- Relies on keyword matching for task detection
- LLM improvements may not perfectly match your style
- Some valid schedules may be flagged if keywords are unusual
- Requires OPENAI_API_KEY for improvement function

## Future Enhancements

- Support multiple pets in one schedule
- Pet-specific validation rules (breed, age)
- Comparison with veterinary guidelines
- Schedule conflict detection
- Optimization for owner's time availability
