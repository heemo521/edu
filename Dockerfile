FROM python:3.11-slim

# Install Python dependencies
WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn==0.23.2

# Install node for frontend build
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY backend /app/backend
COPY frontend /app/frontend
WORKDIR /app/frontend
RUN npm install && npm run build

WORKDIR /app

# Copy system prompt configuration
COPY prompt.txt /app/prompt.txt

# Expose the path to the system prompt so the application can load it
ENV SYSTEM_PROMPT_PATH=/app/prompt.txt

# Expose API and frontend ports
EXPOSE 8000
EXPOSE 3000

# Run FastAPI backend and serve built frontend
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & python3 -m http.server 3000 --directory frontend/dist"]