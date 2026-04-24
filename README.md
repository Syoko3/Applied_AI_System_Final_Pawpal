##### Pawpal+ #####

PawPal+ is an AI-powered pet care scheduling system that combines a deterministic scheduling engine with a Retrieval-Augmented Generation (RAG) pipeline to automatically build, validate, and refine daily care plans for one or more pets. It allows owners to define their pets, assign tasks with priorities and time preferences, and have Gemini LLM generate a grounded, natural-language schedule backed by knowledge retrieved from uploaded pet care PDFs. The system also includes a self-correction loop that validates generated schedules against essential care rules — feeding, exercise, and rest — and automatically rewrites them if issues are found, while exposing a Streamlit web interface and a CLI entry point for flexible usage.

---

### Title and Summary

Pawpal+ is an AI-powered daily pet care assistant. It takes an owner's pets, their tasks, and their available time window, and produces a structured, time-stamped daily plan that respects priorities, avoids conflicts, and fits within the owner's schedule. It uses a Gemini LLM grounded in real pet care knowledge from uploaded PDFs to generate natural-language schedules with per-task rationale, then validates and self-corrects them before the owner ever sees the result. The system works in three layers. First, the scheduler loads all incomplete tasks across every pet and schedules them based on priority and user's available time range. Second, the Gemini agent takes that structured context plus retrieved pet care guidelines from the RAG system and produces a human-readable schedule with explanations. Third, there is a validation to check the output for missing essentials — feeding, exercise, rest — time conflicts, and any custom tasks the owner requested, and if anything is wrong, it sends the issues back to the LLM for an automatic rewrite. This design matters because it respects to the owner's real constraints, can handle multiple pets, grounds AI output with real knowledge, catches any mistakes, and bridges AI output and structured data.

---

### Architecture Overview

UML Diagram:
![alt text](assets/UML_Pawpal+_RAG.png)

The domain layer (Owner, Pet, Task, Priority) defines the real-world data model — who owns which animals and what care activities need to happen. The scheduling layer (Scheduler, Schedule, ScheduledTask, ScheduleAdjustment) applies purely deterministic logic — prioritization by urgency, time-budget constraints, conflict detection — to turn that data into a concrete, time-stamped daily plan. The AI layer (GeminiAgent, RAGSystem) wraps the plan in natural language grounded in real pet care knowledge retrieved from PDFs, validates it against a rule set, self-corrects it if needed, and then parses the result back into structured Task objects so the domain layer can track them — closing the loop between AI output and the application's data model. The relationships form a clear ownership chain from top to bottom: an Owner manages a Scheduler, owns multiple Pet objects, and each pet holds multiple Task objects. The Scheduler consumes that chain — reading all tasks across all pets — and produces a Schedule made up of time-stamped ScheduledTask entries. Each ScheduledTask points back to both the source Task and the Pet it belongs to, so the schedule always retains full context about what needs to be done and for whom. The AI layer sits alongside this chain rather than inside it. RAGSystem feeds knowledge into GeminiAgent, which generates and validates natural-language schedules, then parses them back into Task objects — bridging the gap between LLM output and the structured domain model. ScheduleAdjustment acts as the human override mechanism, allowing targeted post-generation edits without disrupting the rest of the schedule.

---

### Setup Instructions

Running the app:
Note: Python 3.12 is recommended for this project. Python 3.13 on Windows may install an experimental NumPy build that produces warnings or instability.

If you are using Windows:
```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

If you are using macOS/Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Running the demo (main.py):
```bash
python main.py                      # Run basic demo
python main.py upload               # Run demo simulating user PDF upload to data folder
python main.py validate             # Run schedule validation demo
python main.py validate_tasks       # Run demo showing validation catching dropped user tasks
python main.py validate_conflicts   # Run demo showing validation catching time conflicts
python main.py rag_basic            # Run basic PawPal RAG integration example
python main.py rag_tasks            # Run RAG demo incorporating user-added tasks and time range
python main.py constraints          # Run demo showing how time budgets drop low-priority tasks
python main.py playground           # Run the merged RAG playground demos
python main.py schedule             # Run schedule generation examples
python main.py completion           # Run demo showing task completion and automatic recurrence
python main.py multi_pet            # Run comprehensive multi-pet pipeline demo (RAG + Validation)
python main.py reset                # Run demo showing how all app data (PDFs) are deleted
```

Testing the app:
```bash
python -m pytest                    # macOS/Linux only
py -m pytest                        # Windows only
```

Environment variable:
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```
You can also store the key in a local `.env` file for development.

---

### Sample Interactions



---

### Design Decisions



---

### Testing Summary

The tests are implemented in test_pawpal.py, and it includes a total of 22 tests using pytest. The system combines automated unit testing, AI output validation, and controlled mocking to ensure correctness, while constraint checks and retrieval evaluation guarantee realistic and reliable schedules. The automated tests are the core logic, scheduler constraints, AI integration, and RAG pipeline. The validation layer shows the detection of missing essential tasks, verification of the user-requested tasks are included, and flagging time conflicts and formatting issues. Controlled testing includes reproducibility, elimination of external API variability, and reliable edge cases. The tests also include retrieval accuracy checks by similarity search to verify that relevant chunks are ranked highest, and multi-pet queries retrieve context for all entities. The tests also include constraint-based scheduling to make sure the scheduler enforces time budget limits and conflict detection across pets and tasks. The automated tests and constraint-based scheduling worked well in both single-pet and multi-pet scenarios. On the other hand, real Gemini API calls could not be tested directly. Overall, I learned that deterministic logic is very easier to test than AI output, and the parser is the most fragile component when extracting data from LLM output.

---

### Reflection

What are the limitations or biases in your system?

- 

Could your AI be misused, and how would you prevent that?

- 

What surprised you while testing your AI's reliability?

- 

Describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.

- 
