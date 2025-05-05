#!/bin/bash

# Exit on error
set -e

# Default to development mode
MODE=${1:-"development"}
echo "Building in $MODE mode..."

# Function to build a package
build_package() {
    local package=$1
    local mode=$2
    
    echo "Building $package..."
    cd $package
    
    if [ "$mode" = "production" ]; then
        # Build and install the package
        pip install .
    else
        # Install in development mode
        pip install -e .
    fi
    
    cd ..
}

# Always build the common package first
build_package fraud_detection_common $MODE

# Build other packages
build_package fraud_detection_db $MODE
build_package fraud_detection_training $MODE
build_package fraud_detection_api $MODE

echo "All projects built successfully in $MODE mode!" 