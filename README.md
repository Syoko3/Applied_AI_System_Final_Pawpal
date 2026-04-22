### Pawpal+

PawPal is an AI pet assistant that uses uploaded pet care documents (RAG) to generate personalized schedules with the Gemini API and validates them for safety.

### Title and Summary



### Architecture Overview



### Setup Instructions

Running the app:
Python 3.12 is recommended for this project. Python 3.13 on Windows may install an experimental NumPy build that produces warnings or instability.

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
python main.py
python main.py validate
python main.py rag
python main.py pawpal_rag
python main.py playground
python main.py schedule
```

Testing the app:
```bash
python -m pytest
```

Environment variable:

```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

You can also store the key in a local `.env` file for development.

### Sample Interactions



### Design Decisions



### Testing Summary



### Reflection

- What are the limitations or biases in your system?

--- 

- Could your AI be misused, and how would you prevent that?

--- 

- What surprised you while testing your AI's reliability?

--- 

- Describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.

--- 
