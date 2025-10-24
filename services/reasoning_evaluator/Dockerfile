FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies
COPY shared/ /app/shared/

# Copy service files
COPY services/reasoning_evaluator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/reasoning_evaluator/app/ /app/services/reasoning_evaluator/app/

# Expose port
EXPOSE 8005

# Run the service
CMD ["python", "-m", "uvicorn", "services.reasoning_evaluator.app.main:app", "--host", "0.0.0.0", "--port", "8005"]

