# HARA AI Assistant

Phase-1 prototype for the Automotive Engineering AI project:
Functional Safety HARA and Safety Requirement Management Assistant.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The current malfunction identification is a simple rule-based prototype.
The next phases will add:
1. Hazard/hazardous-event generation
2. S/E/C guided assessment
3. ASIL recommendation using deterministic rules
4. RAG with approved project documents
5. Safety Goal / FSR / TSR drafting
6. Traceability matrix and reports
