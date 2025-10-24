FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ../../shared /app/shared

# Copy service code
COPY ./app /app/services/structure_evaluator/app

# Expose port
EXPOSE 8004

# Run the service
CMD ["python", "-m", "uvicorn", "services.structure_evaluator.app.main:app", "--host", "0.0.0.0", "--port", "8004"]

