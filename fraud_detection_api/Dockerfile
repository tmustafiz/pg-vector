FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/config

# Copy packages and config files
COPY fraud_detection_common /app/fraud_detection_common/
COPY fraud_detection_api /app/fraud_detection_api/
COPY config/* /app/config/

# Install fraud_detection_common first
WORKDIR /app/fraud_detection_common
RUN pip install .

# Install API package
WORKDIR /app/fraud_detection_api
RUN pip install .

# Set working directory back to app root
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FRAUD_DETECTION_CONFIG=/app/config/database_config.json

# Expose the port the app runs on
EXPOSE 8000

# Command to run the API
CMD ["python", "-m", "fraud_detection_api.api"] 