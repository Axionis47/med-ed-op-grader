FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY services/rubric_management/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /app/shared

# Copy service code
COPY services/rubric_management/app /app/services/rubric_management/app

# Create data directory
RUN mkdir -p /app/data/rubrics

# Expose port
EXPOSE 8001

# Run the service
CMD ["python", "-m", "uvicorn", "services.rubric_management.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

