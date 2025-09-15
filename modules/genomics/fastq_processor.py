#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for processing FASTQ files
Performs preprocessing, alignment, and BAM file generation
"""

import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_fastq_files(fastq_files, output_path, reference_genome=None):
    """
    Process FASTQ files with real implementation
    
    Args:
        fastq_files (list): List of paths to FASTQ files
        output_path (str): Path to output directory
        reference_genome (str): Path to reference genome (optional)
        
    Returns:
        list: List of processed BAM files
    """
    logger.info("Processing FASTQ files with real implementation")
    processed_bam_files = []
    
    for fastq_file in fastq_files:
        logger.info(f"Processing file: {fastq_file}")
        try:
            # Create output directory for this file
            file_output_dir = Path(output_path) / Path(fastq_file).stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Preprocessing with fastp
            fastp_output = run_fastp(fastq_file, file_output_dir)
            if not fastp_output:
                logger.error(f"fastp preprocessing failed for {fastq_file}")
                continue
                
            # Step 2: Alignment with BWA-MEM2 or Minimap2
            if reference_genome:
                bam_file = run_alignment(fastp_output['clean_fastq'], reference_genome, file_output_dir)
                if not bam_file:
                    logger.error(f"Alignment failed for {fastq_file}")
                    continue
                    
                # Step 3: Sort and index BAM file with samtools
                sorted_bam = run_samtools_sort_index(bam_file, file_output_dir)
                if sorted_bam:
                    processed_bam_files.append(sorted_bam)
                    logger.info(f"Successfully processed {fastq_file} -> {sorted_bam}")
                else:
                    logger.error(f"samtools processing failed for {fastq_file}")
            else:
                logger.warning(f"No reference genome provided, skipping alignment for {fastq_file}")
                
        except Exception as e:
            logger.error(f"Error processing {fastq_file}: {e}")
            
    return processed_bam_files


def run_fastp(input_fastq, output_dir):
    """
    Run fastp for preprocessing FASTQ files
    
    Args:
        input_fastq (str): Path to input FASTQ file
        output_dir (Path): Output directory
        
    Returns:
        dict: Dictionary with paths to output files or None if failed
    """
    logger.info(f"Running fastp preprocessing for {input_fastq}")
    
    try:
        # Define output files
        clean_fastq = output_dir / f"{Path(input_fastq).stem}_clean.fastq"
        html_report = output_dir / f"{Path(input_fastq).stem}_fastp.html"
        json_report = output_dir / f"{Path(input_fastq).stem}_fastp.json"
        
        # Build fastp command
        cmd = [
            "fastp",
            "-i", input_fastq,
            "-o", str(clean_fastq),
            "-h", str(html_report),
            "-j", str(json_report),
            "--thread", "4"
        ]
        
        # Run fastp
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"fastp completed successfully for {input_fastq}")
            return {
                'clean_fastq': str(clean_fastq),
                'html_report': str(html_report),
                'json_report': str(json_report)
            }
        else:
            logger.error(f"fastp failed for {input_fastq}: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error running fastp for {input_fastq}: {e}")
        return None


def run_alignment(input_fastq, reference_genome, output_dir):
    """
    Run alignment with BWA-MEM2 or Minimap2
    
    Args:
        input_fastq (str): Path to input FASTQ file
        reference_genome (str): Path to reference genome
        output_dir (Path): Output directory
        
    Returns:
        str: Path to output BAM file or None if failed
    """
    logger.info(f"Running alignment for {input_fastq}")
    
    try:
        # Determine which aligner to use based on reference genome
        # For now, we'll try BWA-MEM2 first, then Minimap2
        bam_file = output_dir / f"{Path(input_fastq).stem}.bam"
        
        # Try BWA-MEM2 first
        if is_tool_available("bwa-mem2"):
            logger.info("Using BWA-MEM2 for alignment")
            cmd = [
                "bwa-mem2", "mem",
                "-t", "4",
                reference_genome,
                input_fastq
            ]
            
            # Run BWA-MEM2 and pipe to samtools for BAM conversion
            with open(bam_file, 'wb') as bam_out:
                bwa_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                samtools_process = subprocess.Popen(
                    ["samtools", "view", "-b", "-"],
                    stdin=bwa_process.stdout,
                    stdout=bam_out
                )
                bwa_process.stdout.close()
                samtools_process.communicate()
                
                if bwa_process.returncode == 0 and samtools_process.returncode == 0:
                    logger.info(f"BWA-MEM2 alignment completed successfully for {input_fastq}")
                    return str(bam_file)
                else:
                    logger.error(f"BWA-MEM2 alignment failed for {input_fastq}")
        elif is_tool_available("minimap2"):
            logger.info("Using Minimap2 for alignment")
            cmd = [
                "minimap2",
                "-ax", "sr",
                "-t", "4",
                reference_genome,
                input_fastq
            ]
            
            # Run Minimap2 and pipe to samtools for BAM conversion
            with open(bam_file, 'wb') as bam_out:
                minimap2_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                samtools_process = subprocess.Popen(
                    ["samtools", "view", "-b", "-"],
                    stdin=minimap2_process.stdout,
                    stdout=bam_out
                )
                minimap2_process.stdout.close()
                samtools_process.communicate()
                
                if minimap2_process.returncode == 0 and samtools_process.returncode == 0:
                    logger.info(f"Minimap2 alignment completed successfully for {input_fastq}")
                    return str(bam_file)
                else:
                    logger.error(f"Minimap2 alignment failed for {input_fastq}")
        else:
            logger.error("Neither BWA-MEM2 nor Minimap2 is available")
            return None
            
    except Exception as e:
        logger.error(f"Error running alignment for {input_fastq}: {e}")
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


def is_tool_available(tool_name):
    """
    Check if a tool is available in the system PATH
    
    Args:
        tool_name (str): Name of the tool to check
        
    Returns:
        bool: True if tool is available, False otherwise
    """
    try:
        subprocess.run([tool_name, "--help"], 
                      capture_output=True, 
                      text=True, 
                      timeout=5)
        return True
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


if __name__ == "__main__":
    # Example usage
    pass