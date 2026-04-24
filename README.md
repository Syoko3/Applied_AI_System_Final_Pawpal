### Pawpal+

Pawpal+ is an AI-powered pet care assistant that leverages Retrieval-Augmented Generation (RAG) and the Gemini API to create, validate, and track personalized pet schedules. It schedules for completeness and realism, and provides a Streamlit interface for the full upload -> retrieve -> generate -> validate flow.

---

### Title and Summary

Pawpal+ 

### Architecture Overview

UML Diagram:
![alt text](assets/UML_Pawpal+_RAG.png)

- The Owner class is the central actor, which owns one or more Pet objects and are linked to a single Scheduler that manages their daily planning. 

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
python main.py                      # Run basic test
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
```

Testing the app:
```bash
python -m pytest  # macOS/Linux only
py -m pytest      # Windows only
```

Environment variable:
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```
You can also store the key in a local `.env` file for development.

### Sample Interactions



### Design Decisions



### Testing Summary

From test_pawpal.py:


### Reflection

- What are the limitations or biases in your system?

--- 

- Could your AI be misused, and how would you prevent that?

--- 

- What surprised you while testing your AI's reliability?

--- 

- Describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.

--- 
