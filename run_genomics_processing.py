#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run genomics data processing pipeline
"""

import sys
import argparse
from pathlib import Path

# Add the modules directory to the path
sys.path.append(str(Path(__file__).parent / "modules"))

def main():
    """
    Main function to run genomics data processing pipeline
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run genomics data processing pipeline')
    parser.add_argument('--input', '-i', type=str, required=True, 
                        help='Input directory containing genomics data')
    parser.add_argument('--output', '-o', type=str, required=True, 
                        help='Output directory for processed data')
    parser.add_argument('--reference', '-r', type=str, 
                        help='Reference genome file (optional)')
    parser.add_argument('--threads', '-t', type=int, default=4,
                        help='Number of threads to use (default: 4)')
    
    args = parser.parse_args()
    
    # Import the genomics processor
    try:
        from genomics.genomics_processor import process
        print("Successfully imported genomics processor")
    except ImportError as e:
        print(f"Error importing genomics processor: {e}")
        return 1
    
    # Run the processing pipeline
    try:
        print(f"Starting genomics data processing pipeline")
        print(f"Input directory: {args.input}")
        print(f"Output directory: {args.output}")
        if args.reference:
            print(f"Reference genome: {args.reference}")
        print(f"Threads: {args.threads}")
        
        # Run the processing
        process(
            input_path=args.input,
            output_path=args.output,
            reference_genome=args.reference
        )
        
        print("Genomics data processing pipeline completed successfully")
        return 0
        
    except Exception as e:
        print(f"Error running genomics data processing pipeline: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())