#!/bin/bash

# Build script for OmicsIntegrationSuite Docker images
# Usage: ./build.sh [full|minimal]

set -e

echo "==================================="
echo "OmicsIntegrationSuite Docker Build"
echo "==================================="

# Default to minimal build if no argument provided
BUILD_TYPE=${1:-minimal}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

case $BUILD_TYPE in
    full)
        print_status "Building FULL image with all bioinformatics tools..."
        print_warning "This will take 10-15 minutes and download ~2GB of data"
        
        # Build full image
        docker build -t omics-suite:latest -t omics-suite:full .
        
        if [ $? -eq 0 ]; then
            print_status "Full image built successfully!"
            docker images | grep omics-suite
        else
            print_error "Failed to build full image"
            exit 1
        fi
        ;;
        
    minimal)
        print_status "Building MINIMAL image (Python dependencies only)..."
        
        # Build minimal image
        docker build -f Dockerfile.minimal -t omics-suite:minimal .
        
        if [ $? -eq 0 ]; then
            print_status "Minimal image built successfully!"
            docker images | grep omics-suite
        else
            print_error "Failed to build minimal image"
            exit 1
        fi
        ;;
        
    both)
        print_status "Building both FULL and MINIMAL images..."
        
        # Build minimal first (faster)
        print_status "Building minimal image..."
        docker build -f Dockerfile.minimal -t omics-suite:minimal .
        
        # Build full image
        print_status "Building full image..."
        docker build -t omics-suite:latest -t omics-suite:full .
        
        if [ $? -eq 0 ]; then
            print_status "Both images built successfully!"
            docker images | grep omics-suite
        else
            print_error "Failed to build images"
            exit 1
        fi
        ;;
        
    *)
        print_error "Invalid build type: $BUILD_TYPE"
        echo "Usage: $0 [full|minimal|both]"
        echo "  full    - Build full image with all bioinformatics tools"
        echo "  minimal - Build minimal image with Python dependencies only"
        echo "  both    - Build both images"
        exit 1
        ;;
esac

echo ""
print_status "Build completed!"
echo ""
echo "Next steps:"
echo "1. Test the image: ./run.sh test"
echo "2. Run processing: ./run.sh process"
echo "3. Start Jupyter: ./run.sh jupyter"
echo "4. Enter shell: ./run.sh shell"