#!/bin/bash

# Exit on error
set -e

# Detect Python and pip versions
PYTHON_CMD="python3"
PIP_CMD="pip3"

# Check if python3 exists, fall back to python if not
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if pip3 exists, fall back to pip if not
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "Using Python: $($PYTHON_CMD --version)"
echo "Using pip: $($PIP_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Update pip and install build dependencies
echo "Updating pip and installing build dependencies..."
$PIP_CMD install --upgrade pip setuptools wheel

# Install common package
echo "Installing common package..."
cd fraud_detection_common
$PIP_CMD install .
cd ..

# Install and configure services
for service in fraud_detection_training fraud_detection_api; do
    echo "Installing $service..."
    cd $service
    $PIP_CMD install .
    
    # Create service-specific config if needed
    if [ ! -f "config.json" ]; then
        echo "Creating config for $service..."
        cp ../config/model_config.json config.json
    fi
    
    cd ..
done

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    echo "Creating config directory..."
    mkdir -p config
fi

# Copy default config if it doesn't exist
if [ ! -f "config/database_config.json" ]; then
    echo "Creating default database config..."
    cp config/database_config.json config/database_config.local.json
fi

echo "Deployment completed successfully!"
echo "To start the services:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Start training: python -m fraud_detection_training.train"
echo "3. Start API: python -m fraud_detection_api.api" 