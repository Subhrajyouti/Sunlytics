# Use the official Python slim image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy requirements first (caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure Python output is unbuffered (logs show up immediately)
ENV PYTHONUNBUFFERED=1

# Expose the port your app will run on
EXPOSE 8000

# Default command — uvicorn will read PORT env var (set by Fly.io or Docker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]

