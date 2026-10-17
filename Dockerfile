FROM python:3.12-slim

WORKDIR /app

# Install system dependencies  
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files
COPY backend .

# Create models directory
RUN mkdir -p models

# Set Python path
ENV PYTHONPATH=/app

EXPOSE 5000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
