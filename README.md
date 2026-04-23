### Pawpal+

### Title and Summary

PawPal is an AI pet assistant that uses uploaded pet care pdf documents for RAG-based retrieval and uses the Gemini API to generate personalized schedules. It schedules for completeness and realism. It provides a Streamlit interface for the full upload → retrieve → generate → validate flow.

### Architecture Overview



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
python main.py             # Runs the base scheduler/task demo
python main.py validate    # Runs schedule generation, validation, and optional fixing demo
python main.py rag         # Runs RAG examples using in-memory sample text
python main.py pawpal_rag  # Runs the PawPal pet-care advisor example
python main.py playground  # Runs the merged RAG playground demos
python main.py schedule    # Runs schedule-generation examples
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
