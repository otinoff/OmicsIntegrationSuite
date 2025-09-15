#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for processing VCF files
Normalizes, fixes, and indexes VCF files
"""

import os
import subprocess
import logging
from pathlib import Path
import gzip
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_vcf_files(vcf_files, output_path, reference_genome=None):
    """
    Process VCF files with real implementation
    
    Args:
        vcf_files (list): List of paths to VCF files
        output_path (str): Path to output directory
        reference_genome (str): Path to reference genome (optional)
        
    Returns:
        list: List of processed VCF files
    """
    logger.info("Processing VCF files with real implementation")
    processed_vcf_files = []
    
    for vcf_file in vcf_files:
        logger.info(f"Processing file: {vcf_file}")
        try:
            # Create output directory for this file
            file_output_dir = Path(output_path) / Path(vcf_file).stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Normalize and fix VCF file with bcftools
            normalized_vcf = run_bcftools_normalize(vcf_file, reference_genome, file_output_dir)
            if not normalized_vcf:
                logger.error(f"bcftools normalization failed for {vcf_file}")
                continue
                
            # Step 2: Compress VCF file with bgzip
            compressed_vcf = run_bgzip_compress(normalized_vcf, file_output_dir)
            if not compressed_vcf:
                logger.error(f"bgzip compression failed for {normalized_vcf}")
                continue
                
            # Step 3: Index compressed VCF file with tabix
            indexed = run_tabix_index(compressed_vcf, file_output_dir)
            if not indexed:
                logger.error(f"tabix indexing failed for {compressed_vcf}")
                continue
                
            # Step 4: Final validation with bcftools
            validated = run_bcftools_validate(compressed_vcf, file_output_dir)
            if validated:
                processed_vcf_files.append(compressed_vcf)
                logger.info(f"Successfully processed {vcf_file} -> {compressed_vcf}")
            else:
                logger.error(f"Final validation failed for {vcf_file}")
                
        except Exception as e:
            logger.error(f"Error processing {vcf_file}: {e}")
            
    return processed_vcf_files


def run_bcftools_normalize(input_vcf, reference_genome, output_dir):
    """
    Normalize and fix VCF file with bcftools
    
    Args:
        input_vcf (str): Path to input VCF file
        reference_genome (str): Path to reference genome (optional)
        output_dir (Path): Output directory
        
    Returns:
        str: Path to normalized VCF file or None if failed
    """
    logger.info(f"Running bcftools normalize for {input_vcf}")
    
    try:
        # Define output file
        normalized_vcf = output_dir / f"{Path(input_vcf).stem}_normalized.vcf"
        
        # Build bcftools norm command
        cmd = [
            "bcftools", "norm",
            "-o", str(normalized_vcf)
        ]
        
        # Add reference genome if provided
        if reference_genome:
            cmd.extend(["-f", reference_genome])
            
        cmd.append(input_vcf)
        
        # Run bcftools norm
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"bcftools normalize completed successfully for {input_vcf}")
            return str(normalized_vcf)
        else:
            logger.error(f"bcftools normalize failed for {input_vcf}: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error running bcftools normalize for {input_vcf}: {e}")
        return None


def run_bgzip_compress(input_vcf, output_dir):
    """
    Compress VCF file with bgzip
    
    Args:
        input_vcf (str): Path to input VCF file
        output_dir (Path): Output directory
        
    Returns:
        str: Path to compressed VCF.gz file or None if failed
    """
    logger.info(f"Running bgzip compression for {input_vcf}")
    
    try:
        # Define output file
        compressed_vcf = output_dir / f"{Path(input_vcf).stem}.vcf.gz"
        
        # Build bgzip command
        cmd = [
            "bgzip",
            "-c",  # Write to stdout
            input_vcf
        ]
        
        # Run bgzip and redirect output to file
        with open(compressed_vcf, 'wb') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
            
        if result.returncode == 0:
            logger.info(f"bgzip compression completed successfully for {input_vcf}")
            return str(compressed_vcf)
        else:
            logger.error(f"bgzip compression failed for {input_vcf}: {result.stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"Error running bgzip compression for {input_vcf}: {e}")
        return None


def run_tabix_index(input_vcf_gz, output_dir):
    """
    Index compressed VCF file with tabix
    
    Args:
        input_vcf_gz (str): Path to input compressed VCF file
        output_dir (Path): Output directory
        
    Returns:
        bool: True if indexing successful, False otherwise
    """
    logger.info(f"Running tabix indexing for {input_vcf_gz}")
    
    try:
        # Build tabix command
        cmd = [
            "tabix",
            "-p", "vcf",  # Specify file type as VCF
            input_vcf_gz
        ]
        
        # Run tabix
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"tabix indexing completed successfully for {input_vcf_gz}")
            return True
        else:
            logger.error(f"tabix indexing failed for {input_vcf_gz}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running tabix indexing for {input_vcf_gz}: {e}")
        return False


def run_bcftools_validate(input_vcf, output_dir):
    """
    Validate VCF file with bcftools
    
    Args:
        input_vcf (str): Path to input VCF file
        output_dir (Path): Output directory
        
    Returns:
        bool: True if validation successful, False otherwise
    """
    logger.info(f"Running bcftools validate for {input_vcf}")
    
    try:
        # Build bcftools validate command
        cmd = [
            "bcftools", "validate",
            input_vcf
        ]
        
        # Run bcftools validate
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"bcftools validate completed successfully for {input_vcf}")
            return True
        else:
            logger.error(f"bcftools validate failed for {input_vcf}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running bcftools validate for {input_vcf}: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    pass