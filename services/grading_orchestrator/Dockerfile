FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies
COPY shared/ /app/shared/

# Copy service files
COPY services/grading_orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/grading_orchestrator/app/ /app/services/grading_orchestrator/app/

# Expose port
EXPOSE 8000

# Run the service
CMD ["python", "-m", "uvicorn", "services.grading_orchestrator.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

