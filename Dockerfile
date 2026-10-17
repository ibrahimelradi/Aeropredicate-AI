FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root
COPY requirements.txt .

# Install Python dependencies  
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend directory contents to /app
COPY backend /app/

# Create models directory
RUN mkdir -p models

# Ensure PORT is set correctly
ENV PORT=5000
ENV PYTHONPATH=/app
ENV RENDER=true

EXPOSE 5000

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--chdir", "/app", "run:app"]
