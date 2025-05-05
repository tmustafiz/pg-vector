#!/bin/bash

# Exit on error
set -e

# Create virtual environment
echo "Creating virtual environment..."
python -m venv .venv
source .venv/bin/activate

# Install common package
echo "Installing common package..."
cd fraud_detection_common
pip install .
cd ..

# Install and configure services
for service in fraud_detection_training fraud_detection_api; do
    echo "Installing $service..."
    cd $service
    pip install .
    
    # Create service-specific config if needed
    if [ ! -f "config.json" ]; then
        echo "Creating config for $service..."
        cp ../config/model_config.json config.json
    fi
    
    cd ..
done

echo "Deployment completed successfully!"
echo "To start the training service: fraud_detection_training train"
echo "To start the API service: fraud_detection_api start-api" 