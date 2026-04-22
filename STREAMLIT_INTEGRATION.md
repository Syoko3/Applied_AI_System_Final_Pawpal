# Integrating Validation into Streamlit App

## Overview

This guide shows how to integrate the validation system into your Streamlit app for real-time schedule validation and improvement.

---

## Complete Integration Example

### Step 1: Add Imports
```python
from pawpal_system import (
    generate_schedule_with_context,
    validate_schedule,
    review_and_fix_schedule,
    validate_and_fix_schedule
)
```

### Step 2: Add Validation Section to app.py

```python
st.divider()

st.subheader("🔍 Schedule Validation & Improvement")
st.caption("Validate generated schedules and fix any issues automatically.")

# Create two columns for validation controls
val_col1, val_col2 = st.columns([2, 1])

with val_col1:
    validate_btn = st.button("Validate Last Schedule", key="validate_btn")

with val_col2:
    auto_fix = st.checkbox("Auto-fix issues", value=True, key="auto_fix")

if validate_btn and hasattr(st.session_state, 'last_schedule'):
    with st.spinner("🔍 Validating schedule..."):
        validation = validate_schedule(st.session_state.last_schedule)
    
    # Display validation results
    if validation['status'] == 'valid':
        st.success("✅ Schedule is valid! No issues found.")
        st.write(f"✓ {validation['task_count']} tasks detected")
    else:
        st.error(f"⚠️  {len(validation['issues'])} issue(s) found:")
        
        # Show each issue
        for issue in validation['issues']:
            st.write(f"• {issue}")
        
        # Offer to fix if enabled
        if auto_fix:
            st.info("🔧 Auto-fixing schedule...")
            with st.spinner("Improving schedule..."):
                improved = review_and_fix_schedule(
                    st.session_state.last_schedule,
                    validation['issues'],
                    pet_type=st.session_state.get('current_species', 'pet'),
                    context=f"Pet: {st.session_state.get('current_pet_name', 'Pet')}"
                )
            
            st.success("✅ Schedule improved!")
            
            with st.expander("View improved schedule"):
                st.write(improved)
                
                # Option to use improved schedule
                if st.button("Use this improved schedule"):
                    st.session_state.last_schedule = improved
                    st.success("Schedule updated!")
                    st.rerun()
```

---

## Full Streamlit Integration Example

Here's a complete section you can add to your Streamlit app:

```python
# After "Generate schedule" button section, add:

st.divider()

st.subheader("✨ AI Schedule Refinement (Beta)")
st.caption("Let AI validate and improve your generated schedule")

# Check if we have a schedule to validate
if 'generated_schedule_text' in st.session_state:
    
    # Validation section
    st.markdown("### 1️⃣ Validate Your Schedule")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Check if your schedule includes all essential elements...")
    with col2:
        if st.button("🔍 Validate", key="validate_schedule"):
            st.session_state.validation_result = validate_schedule(
                st.session_state.generated_schedule_text
            )
    
    # Display validation results if available
    if 'validation_result' in st.session_state:
        validation = st.session_state.validation_result
        
        if validation['status'] == 'valid':
            st.success("✅ Schedule is valid!")
            st.write(validation['summary'])
        else:
            st.warning("⚠️ Schedule needs improvement")
            st.write(validation['summary'])
            
            # Show issues in expandable section
            with st.expander(f"View {len(validation['issues'])} issue(s)"):
                for i, issue in enumerate(validation['issues'], 1):
                    st.write(f"**{i}.** {issue}")
    
    # Improvement section
    st.markdown("### 2️⃣ Improve Your Schedule")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write("Let AI improve your schedule based on validation...")
    with col2:
        improvement_mode = st.selectbox(
            "Action",
            ["Auto-improve if issues", "Force improve"],
            key="improvement_mode"
        )
    with col3:
        if st.button("✨ Improve", key="improve_schedule"):
            if improvement_mode == "Auto-improve if issues":
                if 'validation_result' in st.session_state:
                    if st.session_state.validation_result['status'] == 'invalid':
                        st.session_state.improving = True
                    else:
                        st.info("Schedule is already valid!")
                else:
                    st.warning("Validate first!")
            else:
                st.session_state.improving = True
    
    # Perform improvement if needed
    if st.session_state.get('improving', False):
        with st.spinner("🤖 AI is improving your schedule..."):
            # Get validation if not already done
            if 'validation_result' not in st.session_state:
                validation = validate_schedule(
                    st.session_state.generated_schedule_text
                )
            else:
                validation = st.session_state.validation_result
            
            # Improve schedule
            improved = review_and_fix_schedule(
                st.session_state.generated_schedule_text,
                validation['issues'] if validation['issues'] else 
                    ["Optimize for clarity and completeness"],
                pet_type=st.session_state.get('pet_species', 'pet'),
                context=f"Pet name: {st.session_state.get('pet_name', 'Pet')}"
            )
            
            st.session_state.improved_schedule = improved
            st.session_state.improving = False
    
    # Display improved schedule if available
    if 'improved_schedule' in st.session_state:
        st.markdown("### 3️⃣ Your Improved Schedule")
        
        with st.expander("View improved schedule", expanded=True):
            st.write(st.session_state.improved_schedule)
            
            # Comparison option
            if st.checkbox("Compare with original"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original Schedule:**")
                    st.write(st.session_state.generated_schedule_text)
                with col2:
                    st.markdown("**Improved Schedule:**")
                    st.write(st.session_state.improved_schedule)

else:
    st.info("📝 Generate a schedule first to validate and improve it!")
```

---

## Usage Flow in Streamlit

```
1. User generates schedule using "Build Schedule" button
2. Schedule appears in session state
3. New "AI Schedule Refinement" section appears
4. User clicks "Validate" to check for issues
5. System shows validation results:
   ✅ Valid → No action needed
   ⚠️  Invalid → Shows list of issues
6. User clicks "Improve"
7. System fixes all identified issues
8. Improved schedule displayed with comparison option
```

---

## Key Components

### 1. Validation Display
```python
if validation['status'] == 'valid':
    st.success("✅ Schedule is valid!")
else:
    st.error(f"⚠️  {len(validation['issues'])} issues found")
    with st.expander("View issues"):
        for issue in validation['issues']:
            st.write(f"• {issue}")
```

### 2. Auto-Improvement
```python
if validation['status'] == 'invalid':
    with st.spinner("Improving schedule..."):
        improved = review_and_fix_schedule(
            schedule,
            validation['issues'],
            pet_type,
            context
        )
    st.success("✅ Schedule improved!")
    st.write(improved)
```

### 3. Comparison View
```python
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Original:**")
    st.write(original)
with col2:
    st.markdown("**Improved:**")
    st.write(improved)
```

---

## Session State Management

```python
# Store generated schedule
if st.button("Generate Schedule"):
    schedule = generate_schedule_with_context(...)
    st.session_state.generated_schedule_text = schedule

# Store validation result
if st.button("Validate"):
    result = validate_schedule(st.session_state.generated_schedule_text)
    st.session_state.validation_result = result

# Store improved schedule
if st.button("Improve"):
    improved = review_and_fix_schedule(...)
    st.session_state.improved_schedule = improved
```

---

## UI/UX Best Practices

### 1. Progressive Disclosure
Show validation section only after schedule is generated.

### 2. Clear Feedback
- ✅ Green for valid schedules
- ⚠️  Orange/yellow for issues
- 🔧 Show specific improvements made

### 3. Action Buttons
```python
st.button("🔍 Validate", key="validate")
st.button("✨ Improve", key="improve")
st.button("📋 Compare", key="compare")
```

### 4. Expandable Sections
Use `st.expander()` to avoid cluttering the UI.

---

## Error Handling

```python
try:
    validation = validate_schedule(schedule)
except Exception as e:
    st.error(f"Validation error: {str(e)}")

try:
    improved = review_and_fix_schedule(schedule, issues, pet_type)
except ValueError as e:
    st.error("API Key Error: Set OPENAI_API_KEY environment variable")
except Exception as e:
    st.error(f"Improvement error: {str(e)}")
```

---

## Complete Sidebar Option

Add validation controls to the sidebar:

```python
with st.sidebar:
    st.markdown("### 🔧 Schedule Tools")
    
    if st.button("Validate Schedule", key="sidebar_validate"):
        # Validation logic
        pass
    
    if st.button("Auto-Improve", key="sidebar_improve"):
        # Improvement logic
        pass
    
    auto_validate = st.checkbox(
        "Auto-validate on generate",
        value=False
    )
```

---

## Advanced: Custom Validation Rules

```python
def validate_with_custom_rules(schedule, pet_info):
    """Validate schedule with pet-specific rules."""
    validation = validate_schedule(schedule)
    
    # Add pet-specific checks
    if pet_info['age'] > 10:
        if 'rest' not in schedule.lower():
            validation['issues'].append(
                "Senior pets need explicit rest periods"
            )
    
    if pet_info['energy_level'] == 'high':
        walks = schedule.lower().count('walk')
        if walks < 2:
            validation['issues'].append(
                "High-energy dogs need multiple walks daily"
            )
    
    validation['status'] = 'invalid' if validation['issues'] else 'valid'
    return validation
```

---

## Testing Integration

```bash
# Test the Streamlit app
streamlit run app.py

# Then:
# 1. Click "Generate schedule"
# 2. Click "Validate"
# 3. See validation results
# 4. Click "Improve" if needed
# 5. View improved schedule
```

---

## Performance Tips

1. **Cache validation results**
   ```python
   @st.cache_data
   def validate_cached(schedule):
       return validate_schedule(schedule)
   ```

2. **Use spinners for long operations**
   ```python
   with st.spinner("Validating..."):
       result = validate_schedule(schedule)
   ```

3. **Disable buttons during processing**
   ```python
   disabled = st.session_state.get('processing', False)
   if st.button("Validate", disabled=disabled):
       st.session_state.processing = True
   ```

---

## Summary

Integration adds:
✅ Real-time schedule validation  
✅ Visual issue reporting  
✅ One-click schedule improvement  
✅ Before/after comparison  
✅ Transparent feedback  
✅ Pet-aware refinement  

Users can now generate, validate, and improve schedules all in one interface!
