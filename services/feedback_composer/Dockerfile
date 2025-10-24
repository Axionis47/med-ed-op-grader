FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ../../shared /app/shared

# Copy service code
COPY ./app /app/services/feedback_composer/app

# Expose port
EXPOSE 8008

# Run the service
CMD ["python", "-m", "uvicorn", "services.feedback_composer.app.main:app", "--host", "0.0.0.0", "--port", "8008"]

