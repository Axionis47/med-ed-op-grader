FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies
COPY shared/ /app/shared/

# Copy service files
COPY services/qa_validation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/qa_validation/app/ /app/services/qa_validation/app/

# Expose port
EXPOSE 8010

# Run the service
CMD ["python", "-m", "uvicorn", "services.qa_validation.app.main:app", "--host", "0.0.0.0", "--port", "8010"]

