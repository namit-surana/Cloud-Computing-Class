# Use official Python slim image as base
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Copy and install dependencies first (better layer caching)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ .

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
