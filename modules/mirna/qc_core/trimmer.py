#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA Adapter Trimming Module
Implements hybrid approach: cutadapt (PRIMARY) + BioPython (FALLBACK)
"""

import os
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional

try:
    from Bio import SeqIO
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("BioPython not available. Only cutadapt mode will work.")

# Configure logging
logger = logging.getLogger(__name__)


def has_cutadapt() -> bool:
    """
    Check if cutadapt is installed and available

    Returns:
        bool: True if cutadapt is available, False otherwise
    """
    return shutil.which("cutadapt") is not None


def trim_with_cutadapt(
    input_fastq: str,
    output_fastq: str,
    min_length: int = 18,
    max_length: int = 25,
    quality_cutoff: int = 20,
    adapter: Optional[str] = None
) -> Dict:
    """
    Trim adapters using cutadapt (PRIMARY METHOD - fast C tool)

    Args:
        input_fastq: Path to input FASTQ file
        output_fastq: Path to output FASTQ file
        min_length: Minimum read length to keep (default 18 for miRNA)
        max_length: Maximum read length to keep (default 25 for miRNA)
        quality_cutoff: Quality threshold (default 20)
        adapter: Adapter sequence to trim (None = auto-detect common adapters)

    Returns:
        dict: {
            'trimmed_fastq': path to output file,
            'total_reads': number of reads processed,
            'trimmed_reads': reads after adapter trimming,
            'filtered_reads': reads after length filter,
            'percent_kept': percentage of reads kept
        }
    """
    logger.info(f"[PRIMARY] Trimming with cutadapt: {input_fastq}")

    # Common Illumina adapter for miRNA-seq
    if adapter is None:
        adapter = "AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC"  # TruSeq adapter

    # Build cutadapt command
    cmd = [
        "cutadapt",
        "-a", adapter,  # Adapter sequence
        f"-q", str(quality_cutoff),  # Quality cutoff
        f"-m", str(min_length),  # Minimum length
        f"-M", str(max_length),  # Maximum length
        "-o", output_fastq,  # Output file
        input_fastq  # Input file
    ]

    try:
        # Run cutadapt
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        if result.returncode != 0:
            logger.error(f"cutadapt failed: {result.stderr}")
            raise RuntimeError(f"cutadapt error: {result.stderr}")

        # Parse cutadapt output for statistics
        output = result.stderr  # cutadapt writes stats to stderr
        metrics = _parse_cutadapt_output(output)

        logger.info(f"✓ Trimmed: {metrics['filtered_reads']:,} / {metrics['total_reads']:,} reads kept ({metrics['percent_kept']:.1f}%)")

        return {
            'trimmed_fastq': output_fastq,
            **metrics
        }

    except subprocess.TimeoutExpired:
        logger.error("cutadapt timeout (>10 minutes)")
        raise RuntimeError("cutadapt timeout")
    except Exception as e:
        logger.error(f"cutadapt failed: {e}")
        raise


def _parse_cutadapt_output(output: str) -> Dict:
    """
    Parse cutadapt stderr output to extract statistics

    Args:
        output: cutadapt stderr text

    Returns:
        dict with metrics
    """
    metrics = {
        'total_reads': 0,
        'trimmed_reads': 0,
        'filtered_reads': 0,
        'percent_kept': 0.0
    }

    for line in output.split('\n'):
        if 'Total reads processed:' in line:
            metrics['total_reads'] = int(line.split(':')[1].strip().replace(',', ''))
        elif 'Reads written (passing filters):' in line:
            # Extract number and percentage
            parts = line.split(':')[1].strip().split()
            metrics['filtered_reads'] = int(parts[0].replace(',', ''))
            if len(parts) > 1 and '%' in parts[1]:
                metrics['percent_kept'] = float(parts[1].strip('()%'))

    # If trimmed_reads not explicitly stated, assume same as total
    metrics['trimmed_reads'] = metrics['total_reads']

    return metrics


def trim_with_biopython(
    input_fastq: str,
    output_fastq: str,
    min_length: int = 18,
    max_length: int = 25,
    quality_threshold: int = 20
) -> Dict:
    """
    Trim and filter reads using BioPython (FALLBACK METHOD - slower but no dependencies)

    This is a simple implementation that:
    1. Filters by read length
    2. Basic quality filtering
    (No adapter trimming in this fallback - would need manual implementation)

    Args:
        input_fastq: Path to input FASTQ file
        output_fastq: Path to output FASTQ file
        min_length: Minimum read length to keep
        max_length: Maximum read length to keep
        quality_threshold: Minimum average quality score

    Returns:
        dict with metrics
    """
    if not BIOPYTHON_AVAILABLE:
        raise ImportError("BioPython is required for fallback mode")

    logger.warning("[FALLBACK] Using BioPython (slower, no adapter trimming)")
    logger.info(f"Filtering reads: {input_fastq}")

    total_reads = 0
    filtered_reads = 0

    # Determine if input is gzipped
    input_path = Path(input_fastq)
    format_type = "fastq" if not input_path.suffix == ".gz" else "fastq"

    try:
        with open(output_fastq, 'w') as out_handle:
            for record in SeqIO.parse(input_fastq, format_type):
                total_reads += 1

                # Filter by length
                seq_len = len(record.seq)
                if seq_len < min_length or seq_len > max_length:
                    continue

                # Filter by quality (average quality)
                if hasattr(record, 'letter_annotations') and 'phred_quality' in record.letter_annotations:
                    avg_quality = sum(record.letter_annotations['phred_quality']) / len(record)
                    if avg_quality < quality_threshold:
                        continue

                # Write passing read
                SeqIO.write(record, out_handle, "fastq")
                filtered_reads += 1

        percent_kept = (filtered_reads / total_reads * 100) if total_reads > 0 else 0.0

        logger.info(f"✓ Filtered: {filtered_reads:,} / {total_reads:,} reads kept ({percent_kept:.1f}%)")

        return {
            'trimmed_fastq': output_fastq,
            'total_reads': total_reads,
            'trimmed_reads': total_reads,  # No actual trimming in fallback
            'filtered_reads': filtered_reads,
            'percent_kept': percent_kept
        }

    except Exception as e:
        logger.error(f"BioPython filtering failed: {e}")
        raise


def trim_adapters(
    input_fastq: str,
    output_dir: str,
    min_length: int = 18,
    max_length: int = 25,
    sample_id: Optional[str] = None
) -> Dict:
    """
    Hybrid adapter trimming: try cutadapt first, fallback to BioPython

    This is the MAIN FUNCTION to use for adapter trimming.

    Args:
        input_fastq: Path to input FASTQ file
        output_dir: Output directory path
        min_length: Minimum read length (default 18 for miRNA from ТЗ)
        max_length: Maximum read length (default 25 for miRNA from ТЗ)
        sample_id: Sample identifier (optional, for naming)

    Returns:
        dict: {
            'trimmed_fastq': path to output FASTQ,
            'total_reads': int,
            'trimmed_reads': int,
            'filtered_reads': int,
            'percent_kept': float,
            'method': 'cutadapt' or 'biopython'
        }
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    input_name = Path(input_fastq).stem
    if input_name.endswith('.fastq'):
        input_name = input_name[:-6]

    if sample_id:
        output_filename = f"{sample_id}_trimmed.fastq"
    else:
        output_filename = f"{input_name}_trimmed.fastq"

    output_fastq = str(output_path / output_filename)

    # Try PRIMARY method: cutadapt
    if has_cutadapt():
        try:
            logger.info("✓ cutadapt found - using PRIMARY method")
            result = trim_with_cutadapt(
                input_fastq,
                output_fastq,
                min_length=min_length,
                max_length=max_length
            )
            result['method'] = 'cutadapt'
            return result
        except Exception as e:
            logger.warning(f"cutadapt failed: {e}, trying fallback...")

    # FALLBACK method: BioPython
    if BIOPYTHON_AVAILABLE:
        logger.info("⚠ cutadapt not available - using FALLBACK BioPython")
        result = trim_with_biopython(
            input_fastq,
            output_fastq,
            min_length=min_length,
            max_length=max_length
        )
        result['method'] = 'biopython'
        return result
    else:
        raise RuntimeError(
            "Neither cutadapt nor BioPython available. "
            "Install one of them:\n"
            "  pip install biopython\n"
            "  conda install -c bioconda cutadapt"
        )


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing miRNA Trimmer Module")
    print("=" * 50)

    # Check available methods
    print(f"\ncutadapt available: {has_cutadapt()}")
    print(f"BioPython available: {BIOPYTHON_AVAILABLE}")

    # Test would go here with actual FASTQ file
    print("\nReady for testing with real FASTQ data!")
