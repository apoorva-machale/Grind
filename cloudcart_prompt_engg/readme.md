CloudCart Prompt Engg
This project is split into two main parts:

backend/ — FastAPI service
frontend/ — Streamlit app

1) Backend structure
backend/app.py
This is the FastAPI entrypoint.
It creates app = FastAPI(...).
It imports api_router from backend.routes and attaches it.
When you run the backend, this file starts the server on http://localhost:8000.
backend/routes/ - This folder defines the API endpoints.

health.py → GET /health
validation.py → POST /validate
analysis.py → POST /analyze-vulnerability
invocation.py → POST /invoke, POST /process, POST /submit
version.py → GET /versions, POST /switch-version

2) Backend service layer
backend/services/input_validation.py - Contains InputValidator
It checks user text for: empty input, too-long input, prompt injection patterns (ignore previous instructions, system prompt, etc.)

backend/services/vulnerability.py - Builds a “vulnerability analysis” result for a given input. Builds a safe prompt template
Can optionally invoke the safe template with the LLM
This is mainly used for analysis and debugging.

backend/services/prompt_manager.py - Loads prompt YAML files from backend/services/prompts/cloudcart/. Compiles YAML into a ChatPromptTemplate. Calls the LLM via Ollama. Parses the LLM output into structured JSON. Uses the active YAML version from current.yaml by default.

backend/services/prompts/cloudcart/ -
Contains versioned prompts:
1. v1.0.0.yaml
2. v1.1.0.yaml
3. current.yaml
current.yaml is the active prompt used by the backend

3) Frontend structure
frontend/streamlit_app.py
Simple Streamlit UI
One text input field
Sends the entered text to backend POST /submit
Shows either:
success response
blocked response with reason