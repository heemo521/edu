# edu

An experimental AI tutoring platform.  
It combines a FastAPI backend with a lightweight
HTML/JavaScript frontend to provide chat-based study help,
progress tracking and simple subscription features.

## Project structure

```
backend/   FastAPI application and unit tests
frontend/  Static single-page interface
Dockerfile Container recipe bundling backend and frontend
tasks.md   Development backlog
```

## Getting started

### Backend
1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. (Optional) set environment variables for the LLM service:
   - `OLLAMA_BASE_URL` – URL of the Ollama server.
   - `LLAMA_MODEL` – model name to use.
   The backend falls back to canned replies if the model is unavailable.
3. Run the API:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

### Frontend
Serve the `frontend/` directory or open `index.html` directly in a browser:

```bash
python -m http.server 3000 -d frontend
```
The page expects the backend to be available at `http://localhost:8000`.

### Docker
To run the full stack in a container:
```bash
docker build -t edu .
docker run -p 8000:8000 -p 3000:3000 edu
```

## Running tests

The backend includes a small unittest suite.  
Execute it from the repository root:

```bash
pytest backend/tests
```

## Next steps

See `tasks.md` for a roadmap of planned improvements and ideas for
contributors who want to explore testing, CI, or new features.

