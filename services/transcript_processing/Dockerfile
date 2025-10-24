FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies
COPY shared/ /app/shared/

# Copy service files
COPY services/transcript_processing/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/transcript_processing/app/ /app/services/transcript_processing/app/

# Expose port
EXPOSE 8002

# Run the service
CMD ["python", "-m", "uvicorn", "services.transcript_processing.app.main:app", "--host", "0.0.0.0", "--port", "8002"]

