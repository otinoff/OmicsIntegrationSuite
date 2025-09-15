#!/bin/bash

# Run script for OmicsIntegrationSuite Docker container
# Usage: ./run.sh [command] [options]

set -e

# Default image
IMAGE_NAME="omics-suite:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_command() {
    echo -e "${BLUE}[COMMAND]${NC} $1"
}

# Check if Docker image exists
if ! docker images | grep -q "omics-suite"; then
    print_error "Docker image not found. Please run ./build.sh first"
    exit 1
fi

# Get the command
COMMAND=${1:-help}

case $COMMAND in
    test)
        print_status "Running tests in Docker container..."
        docker run --rm \
            -v "$(pwd)/modules:/app/modules" \
            -v "$(pwd)/tests:/app/tests" \
            $IMAGE_NAME \
            python -m pytest tests/ -v
        ;;
        
    shell|bash)
        print_status "Starting interactive shell..."
        docker run -it --rm \
            -v "$(pwd)/data:/data" \
            -v "$(pwd)/modules:/app/modules" \
            -v "$(pwd)/results:/results" \
            --entrypoint /bin/bash \
            $IMAGE_NAME
        ;;
        
    jupyter)
        print_status "Starting Jupyter notebook server..."
        print_warning "Jupyter will be available at http://localhost:8888"
        docker run -it --rm \
            -p 8888:8888 \
            -v "$(pwd)/data:/data" \
            -v "$(pwd)/modules:/app/modules" \
            -v "$(pwd)/notebooks:/notebooks" \
            $IMAGE_NAME \
            bash -c "pip install jupyter notebook && \
                     jupyter notebook --ip=0.0.0.0 --no-browser --allow-root \
                     --NotebookApp.token='' --NotebookApp.password=''"
        ;;
        
    process)
        shift
        INPUT_DIR=${1:-data/input/genomics}
        OUTPUT_DIR=${2:-data/output/genomics}
        REFERENCE=${3:-}
        
        print_status "Processing genomic data..."
        print_status "Input: $INPUT_DIR"
        print_status "Output: $OUTPUT_DIR"
        
        if [ -z "$REFERENCE" ]; then
            docker run --rm \
                -v "$(pwd)/$INPUT_DIR:/data/input" \
                -v "$(pwd)/$OUTPUT_DIR:/data/output" \
                $IMAGE_NAME \
                --input /data/input \
                --output /data/output
        else
            print_status "Reference: $REFERENCE"
            docker run --rm \
                -v "$(pwd)/$INPUT_DIR:/data/input" \
                -v "$(pwd)/$OUTPUT_DIR:/data/output" \
                -v "$(pwd)/$REFERENCE:/data/reference/genome.fa" \
                $IMAGE_NAME \
                --input /data/input \
                --output /data/output \
                --reference /data/reference/genome.fa
        fi
        ;;
        
    check)
        print_status "Checking installed tools in Docker container..."
        docker run --rm $IMAGE_NAME bash -c '
            echo "=== Checking Bioinformatics Tools ==="
            echo ""
            
            echo -n "samtools: "
            if command -v samtools &> /dev/null; then
                samtools --version | head -n1
            else
                echo "NOT FOUND"
            fi
            
            echo -n "bcftools: "
            if command -v bcftools &> /dev/null; then
                bcftools --version | head -n1
            else
                echo "NOT FOUND"
            fi
            
            echo -n "fastp: "
            if command -v fastp &> /dev/null; then
                fastp --version 2>&1 | head -n1
            else
                echo "NOT FOUND"
            fi
            
            echo -n "bwa-mem2: "
            if command -v bwa-mem2 &> /dev/null; then
                bwa-mem2 version 2>&1 | head -n1
            else
                echo "NOT FOUND"
            fi
            
            echo -n "minimap2: "
            if command -v minimap2 &> /dev/null; then
                minimap2 --version
            else
                echo "NOT FOUND"
            fi
            
            echo -n "fastqc: "
            if command -v fastqc &> /dev/null; then
                fastqc --version
            else
                echo "NOT FOUND"
            fi
            
            echo ""
            echo "=== Checking Python Libraries ==="
            python -c "
import sys
print(f\"Python: {sys.version.split()[0]}\")
try:
    import pysam
    print(f\"pysam: {pysam.__version__}\")
except: print(\"pysam: NOT FOUND\")
try:
    import cyvcf2
    print(\"cyvcf2: INSTALLED\")
except: print(\"cyvcf2: NOT FOUND\")
try:
    import Bio
    print(f\"Biopython: {Bio.__version__}\")
except: print(\"Biopython: NOT FOUND\")
try:
    import pybedtools
    print(f\"pybedtools: {pybedtools.__version__}\")
except: print(\"pybedtools: NOT FOUND\")
try:
    import pysamstats
    print(\"pysamstats: INSTALLED\")
except: print(\"pysamstats: NOT FOUND\")
"
        '
        ;;
        
    compose-up)
        print_status "Starting services with docker-compose..."
        docker-compose up -d
        print_status "Services started!"
        echo ""
        echo "Available services:"
        echo "  - Jupyter: http://localhost:8888"
        echo "  - Dev shell: docker exec -it omics-dev bash"
        echo ""
        echo "Stop services with: ./run.sh compose-down"
        ;;
        
    compose-down)
        print_status "Stopping services..."
        docker-compose down
        print_status "Services stopped!"
        ;;
        
    compose-logs)
        print_status "Showing logs..."
        docker-compose logs -f
        ;;
        
    clean)
        print_warning "Cleaning Docker resources..."
        docker-compose down 2>/dev/null || true
        docker system prune -f
        print_status "Cleanup completed!"
        ;;
        
    help|*)
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  test           - Run tests in Docker container"
        echo "  shell|bash     - Start interactive shell in container"
        echo "  jupyter        - Start Jupyter notebook server (port 8888)"
        echo "  process        - Process genomic data"
        echo "                   Usage: $0 process [input_dir] [output_dir] [reference]"
        echo "  check          - Check installed tools and libraries"
        echo "  compose-up     - Start all services with docker-compose"
        echo "  compose-down   - Stop all services"
        echo "  compose-logs   - Show service logs"
        echo "  clean          - Clean Docker resources"
        echo "  help           - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 shell                                    # Interactive shell"
        echo "  $0 jupyter                                  # Start Jupyter"
        echo "  $0 process data/input data/output           # Process with default settings"
        echo "  $0 process data/input data/output ref.fa    # Process with reference genome"
        echo "  $0 check                                    # Check installations"
        ;;
esac