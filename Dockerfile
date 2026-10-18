FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements first (for caching)
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend directory contents to /app
COPY backend/ /app/

# Create models directory with sample model
RUN mkdir -p /app/models /app/data

# Set environment variables
ENV PORT=5000
ENV PYTHONPATH=/app
ENV RENDER=true

EXPOSE 5000

# Run the application with gunicorn
# Target: /app/run.py -> app = create_app()
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--chdir", "/app", "run:app"]