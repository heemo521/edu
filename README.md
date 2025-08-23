# edu

An experimental AI tutoring platform combining a FastAPI backend with a
lightweight HTML/JavaScript frontend.  It offers chat-based study help,
progress tracking, and simple subscription features.

## Project structure

```
backend/   FastAPI application and unit tests
frontend/  Static single-page interface
Dockerfile Container recipe bundling backend and frontend
tasks.md   Development backlog
```

## Installation

### Requirements
- Python 3.11+
- [Ollama](https://github.com/ollama/ollama) running locally or remotely
- (Optional) Docker and docker-compose

### Environment variables
These variables configure how the backend connects to the language model and
where to read the system prompt.

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | URL of the Ollama server | `http://localhost:11434` |
| `LLAMA_MODEL` | Model name to request | `llama3` |
| `SYSTEM_PROMPT_PATH` | Path to a text file with a custom system prompt | *(built-in prompt)* |

Create a `.env` file (or copy `.env.example`) to provide these values.

## Running locally (Python)
1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start the API:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
3. Serve the frontend:
   ```bash
   python -m http.server 3000 -d frontend
   ```
   The page expects the backend at `http://localhost:8000`.

## Running with Docker
Build and run the combined backend/frontend image:
```bash
docker build -t edu .
docker run --env-file .env -p 8000:8000 -p 3000:3000 edu
```

## Running with docker-compose
A sample `docker-compose.yml` is provided to coordinate the API, static server,
and Ollama model.
```bash
docker-compose up --build
```
The compose file reads variables from `.env` and exposes ports 8000, 3000, and
11434.

## Deployment notes
- Use a persistent volume for the SQLite database.
- Ensure environment variables are set securely in production.
- Place a reverse proxy (e.g., Nginx) in front of the services for TLS
  termination and routing.
- Customize the system prompt via `SYSTEM_PROMPT_PATH` to tune tutoring style.

## Running tests
The backend includes a small unittest suite:
```bash
pytest backend/tests
```

## Next steps
See `tasks.md` for a roadmap of planned improvements and ideas for contributors
who want to explore testing, CI, or new features.
