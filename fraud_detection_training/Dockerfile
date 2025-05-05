FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies
RUN pip install --upgrade pip hatchling

# Create necessary directories
RUN mkdir -p /app/config /app/data

# Copy packages and config files
COPY fraud_detection_common /app/fraud_detection_common/
COPY fraud_detection_training /app/fraud_detection_training/
COPY config/* /app/config/

# Copy wait-for-db script
COPY fraud_detection_training/wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

# Install fraud_detection_common first
WORKDIR /app/fraud_detection_common
RUN pip install .

# Install training package
WORKDIR /app/fraud_detection_training
RUN pip install .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV POSTGRES_PASSWORD=postgres

# Create volume mount points
VOLUME ["/app/data", "/app/config"]

# Set working directory back to app root
WORKDIR /app

# Command to run the training
CMD ["/app/wait-for-db.sh", "db", "python", "-m", "fraud_detection_training.train"] 