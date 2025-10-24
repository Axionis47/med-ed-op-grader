FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies
COPY shared/ /app/shared/

# Copy service files
COPY services/question_matching/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/question_matching/app/ /app/services/question_matching/app/

# Expose port
EXPOSE 8003

# Run the service
CMD ["python", "-m", "uvicorn", "services.question_matching.app.main:app", "--host", "0.0.0.0", "--port", "8003"]

