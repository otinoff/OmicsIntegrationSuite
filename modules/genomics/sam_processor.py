#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for processing SAM files
Converts SAM to BAM, sorts and indexes BAM files
"""

import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_sam_files(sam_files, output_path):
    """
    Process SAM files with real implementation
    
    Args:
        sam_files (list): List of paths to SAM files
        output_path (str): Path to output directory
        
    Returns:
        list: List of processed BAM files
    """
    logger.info("Processing SAM files with real implementation")
    processed_bam_files = []
    
    for sam_file in sam_files:
        logger.info(f"Processing file: {sam_file}")
        try:
            # Create output directory for this file
            file_output_dir = Path(output_path) / Path(sam_file).stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Convert SAM to BAM
            bam_file = run_sam_to_bam(sam_file, file_output_dir)
            if not bam_file:
                logger.error(f"SAM to BAM conversion failed for {sam_file}")
                continue
                
            # Step 2: Sort and index BAM file with samtools
            sorted_bam = run_samtools_sort_index(bam_file, file_output_dir)
            if sorted_bam:
                processed_bam_files.append(sorted_bam)
                logger.info(f"Successfully processed {sam_file} -> {sorted_bam}")
            else:
                logger.error(f"samtools processing failed for {sam_file}")
                
        except Exception as e:
            logger.error(f"Error processing {sam_file}: {e}")
            
    return processed_bam_files


def run_sam_to_bam(input_sam, output_dir):
    """
    Convert SAM file to BAM using samtools
    
    Args:
        input_sam (str): Path to input SAM file
        output_dir (Path): Output directory
        
    Returns:
        str: Path to output BAM file or None if failed
    """
    logger.info(f"Converting SAM to BAM for {input_sam}")
    
    try:
        # Define output file
        bam_file = output_dir / f"{Path(input_sam).stem}.bam"
        
        # Build samtools view command
        cmd = [
            "samtools", "view",
            "-b",  # Output BAM format
            "-o", str(bam_file),  # Output file
            input_sam
        ]
        
        # Run samtools view
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"SAM to BAM conversion completed successfully for {input_sam}")
            return str(bam_file)
        else:
            logger.error(f"SAM to BAM conversion failed for {input_sam}: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error converting SAM to BAM for {input_sam}: {e}")
        return None


def run_samtools_sort_index(input_bam, output_dir):
    """
    Sort and index BAM file with samtools
    
    Args:
        input_bam (str): Path to input BAM file
        output_dir (Path): Output directory
        
    Returns:
        str: Path to sorted and indexed BAM file or None if failed
    """
    logger.info(f"Running samtools sort and index for {input_bam}")
    
    try:
        # Define output files
        sorted_bam = output_dir / f"{Path(input_bam).stem}_sorted.bam"
        index_file = f"{sorted_bam}.bai"
        
        # Sort BAM file
        sort_cmd = [
            "samtools", "sort",
            "-o", str(sorted_bam),
            "-@",
 "4",
            input_bam
        ]
        
        result = subprocess.run(sort_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"samtools sort failed for {input_bam}: {result.stderr}")
            return None
            
        # Index sorted BAM file
        index_cmd = [
            "samtools", "index",
            str(sorted_bam)
        ]
        
        result = subprocess.run(index_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"samtools index failed for {sorted_bam}: {result.stderr}")
            return None
            
        logger.info(f"samtools sort and index completed successfully for {input_bam}")
        return str(sorted_bam)
        
    except Exception as e:
        logger.error(f"Error running samtools sort and index for {input_bam}: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    pass