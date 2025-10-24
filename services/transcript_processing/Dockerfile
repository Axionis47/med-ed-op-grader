FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY services/transcript_processing/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /app/shared

# Copy service code
COPY services/transcript_processing/app /app/services/transcript_processing/app

# Expose port (will be set per service)
EXPOSE 8000

# Run the service
CMD ["python", "-m", "uvicorn", "services.transcript_processing.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

