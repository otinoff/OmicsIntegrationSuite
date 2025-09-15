#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for processing BAM/CRAM files
Extracts variants from BAM/CRAM files using bcftools or GATK
"""

import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_bam_files(bam_files, output_path, reference_genome=None):
    """
    Process BAM/CRAM files with real implementation
    
    Args:
        bam_files (list): List of paths to BAM/CRAM files
        output_path (str): Path to output directory
        reference_genome (str): Path to reference genome (optional)
        
    Returns:
        list: List of processed VCF files
    """
    logger.info("Processing BAM/CRAM files with real implementation")
    processed_vcf_files = []
    
    for bam_file in bam_files:
        logger.info(f"Processing file: {bam_file}")
        try:
            # Create output directory for this file
            file_output_dir = Path(output_path) / Path(bam_file).stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Extract variants using bcftools or GATK
            if reference_genome:
                vcf_file = run_variant_calling(bam_file, reference_genome, file_output_dir)
                if not vcf_file:
                    logger.error(f"Variant calling failed for {bam_file}")
                    continue
                    
                # Step 2: Validate VCF file with bcftools
                validated = run_bcftools_validate(vcf_file, file_output_dir)
                if validated:
                    processed_vcf_files.append(vcf_file)
                    logger.info(f"Successfully processed {bam_file} -> {vcf_file}")
                else:
                    logger.error(f"VCF validation failed for {bam_file}")
            else:
                logger.warning(f"No reference genome provided, skipping variant calling for {bam_file}")
                
        except Exception as e:
            logger.error(f"Error processing {bam_file}: {e}")
            
    return processed_vcf_files


def run_variant_calling(input_bam, reference_genome, output_dir):
    """
    Extract variants from BAM/CRAM file using bcftools or GATK
    
    Args:
        input_bam (str): Path to input BAM/CRAM file
        reference_genome (str): Path to reference genome
        output_dir (Path): Output directory
        
    Returns:
        str: Path to output VCF file or None if failed
    """
    logger.info(f"Running variant calling for {input_bam}")
    
    try:
        # Define output file
        vcf_file = output_dir / f"{Path(input_bam).stem}.vcf"
        
        # Try bcftools first
        if is_tool_available("bcftools"):
            logger.info("Using bcftools for variant calling")
            cmd = [
                "bcftools", "mpileup",
                "-f", reference_genome,
                "-Ou",  # Output uncompressed BCF
                input_bam,
                "|",
                "bcftools", "call",
                "-mv",  # Multiallelic caller, output variants only
                "-Ov",  # Output VCF
                "-o", str(vcf_file)
            ]
            
            # Run bcftools mpileup and call
            result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"bcftools variant calling completed successfully for {input_bam}")
                return str(vcf_file)
            else:
                logger.error(f"bcftools variant calling failed for {input_bam}: {result.stderr}")
        elif is_tool_available("gatk"):
            logger.info("Using GATK for variant calling")
            cmd = [
                "gatk", "HaplotypeCaller",
                "-R", reference_genome,
                "-I", input_bam,
                "-O", str(vcf_file)
            ]
            
            # Run GATK HaplotypeCaller
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"GATK variant calling completed successfully for {input_bam}")
                return str(vcf_file)
            else:
                logger.error(f"GATK variant calling failed for {input_bam}: {result.stderr}")
        else:
            logger.error("Neither bcftools nor GATK is available")
            return None
            
    except Exception as e:
        logger.error(f"Error running variant calling for {input_bam}: {e}")
        return None


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