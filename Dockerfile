FROM python:3.11-slim

# Install Python dependencies
WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn==0.23.2

# Copy application code
COPY backend /app/backend
COPY frontend /app/frontend

# Expose API and frontend ports
EXPOSE 8000
EXPOSE 3000

# By default, run the FastAPI backend on port 8000 and serve the frontend on port 3000.
# The backend starts in the background; the http.server for the frontend keeps the container alive.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & python3 -m http.server 3000 --directory frontend"]