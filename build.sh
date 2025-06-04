#!/bin/bash

# Exit on error
set -e

# Default to development mode
MODE=${1:-"development"}
echo "Building in $MODE mode..."

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

# Function to build a package
build_package() {
    local package=$1
    local mode=$2
    
    echo "Building $package..."
    cd $package
    
    # Update pip first
    $PIP_CMD install --upgrade pip
    
    # Install build dependencies
    $PIP_CMD install --upgrade setuptools wheel
    
    if [ "$mode" = "production" ]; then
        # Build and install the package
        $PIP_CMD install .
    else
        # Install in development mode
        $PIP_CMD install -e .
    fi
    
    cd ..
}

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Always build the common package first
build_package fraud_detection_common $MODE

# Build other packages
build_package fraud_detection_training $MODE
build_package fraud_detection_api $MODE

echo "All projects built successfully in $MODE mode!"
echo "To start the services:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Start training: python -m fraud_detection_training.train"
echo "3. Start API: python -m fraud_detection_api.api" 