#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA Alignment Module
Implements hybrid approach: bowtie (PRIMARY) + Python pure alignment (FALLBACK)
"""

import os
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, List
from collections import defaultdict

try:
    from Bio import SeqIO
    from Bio.Seq import Seq
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("BioPython not available. Only bowtie mode will work.")

# Configure logging
logger = logging.getLogger(__name__)


def has_bowtie() -> bool:
    """
    Check if bowtie is installed and available

    Returns:
        bool: True if bowtie is available, False otherwise
    """
    return shutil.which("bowtie") is not None


def build_bowtie_index(
    reference_fasta: str,
    index_base: str,
    force_rebuild: bool = False
) -> bool:
    """
    Build bowtie index from reference FASTA

    Args:
        reference_fasta: Path to miRBase FASTA file
        index_base: Base name for index files (without extension)
        force_rebuild: Rebuild index even if it exists

    Returns:
        bool: True if index built successfully, False otherwise
    """
    logger.info(f"[CHECK] Building bowtie index: {index_base}")

    # Check if index already exists
    index_files = [f"{index_base}.{i}.ebwt" for i in range(1, 5)]
    if not force_rebuild and all(os.path.exists(f) for f in index_files):
        logger.info(f"✓ Bowtie index already exists: {index_base}")
        return True

    # Build index
    cmd = ["bowtie-build", reference_fasta, index_base]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )

        if result.returncode != 0:
            logger.error(f"bowtie-build failed: {result.stderr}")
            return False

        logger.info(f"✓ Bowtie index built: {index_base}")
        return True

    except subprocess.TimeoutExpired:
        logger.error("bowtie-build timeout (>5 minutes)")
        return False
    except Exception as e:
        logger.error(f"bowtie-build failed: {e}")
        return False


def align_with_bowtie(
    input_fastq: str,
    output_sam: str,
    bowtie_index: str,
    mismatches: int = 1,
    threads: int = 4
) -> Dict:
    """
    Align reads to miRBase using bowtie (PRIMARY METHOD - fast C tool)

    Args:
        input_fastq: Path to trimmed FASTQ file
        output_sam: Path to output SAM file
        bowtie_index: Path to bowtie index (basename, no extension)
        mismatches: Number of mismatches allowed (default 1)
        threads: Number of threads (default 4)

    Returns:
        dict: {
            'sam_file': path to SAM file,
            'total_reads': number of reads processed,
            'aligned_reads': number of aligned reads,
            'alignment_rate': percentage of aligned reads,
            'method': 'bowtie'
        }
    """
    logger.info(f"[PRIMARY] Aligning with bowtie: {input_fastq}")

    # Build bowtie command
    # -v: mismatch mode (allow up to N mismatches)
    # -a: report all valid alignments
    # -S: output SAM format
    # -p: threads
    # --best --strata: report only best alignments
    cmd = [
        "bowtie",
        "-v", str(mismatches),  # Allow mismatches
        "-a",  # Report all valid alignments
        "--best", "--strata",  # Only best alignments
        "-S",  # SAM output
        "-p", str(threads),  # Threads
        bowtie_index,  # Index
        input_fastq,  # Input FASTQ
        output_sam  # Output SAM
    ]

    try:
        # Run bowtie
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )

        if result.returncode != 0:
            logger.error(f"bowtie failed: {result.stderr}")
            raise RuntimeError(f"bowtie error: {result.stderr}")

        # Parse bowtie stderr for statistics
        # Example: "# reads processed: 1000\n# reads with at least one alignment: 950 (95.00%)"
        metrics = _parse_bowtie_output(result.stderr)

        logger.info(
            f"✓ Aligned: {metrics['aligned_reads']:,} / {metrics['total_reads']:,} "
            f"({metrics['alignment_rate']:.1f}%)"
        )

        return {
            'sam_file': output_sam,
            **metrics,
            'method': 'bowtie'
        }

    except subprocess.TimeoutExpired:
        logger.error("bowtie timeout (>10 minutes)")
        raise RuntimeError("bowtie timeout")
    except Exception as e:
        logger.error(f"bowtie failed: {e}")
        raise


def _parse_bowtie_output(output: str) -> Dict:
    """
    Parse bowtie stderr output to extract alignment statistics

    Args:
        output: bowtie stderr text

    Returns:
        dict with metrics
    """
    metrics = {
        'total_reads': 0,
        'aligned_reads': 0,
        'alignment_rate': 0.0
    }

    for line in output.split('\n'):
        if 'reads processed:' in line:
            # Extract number from "# reads processed: 1000"
            parts = line.split(':')
            if len(parts) > 1:
                metrics['total_reads'] = int(parts[1].strip())

        elif 'reads with at least one' in line or 'reads with at least one alignment' in line:
            # Extract from "# reads with at least one alignment: 950 (95.00%)"
            parts = line.split(':')
            if len(parts) > 1:
                # Extract number and percentage
                value_part = parts[1].strip()
                if '(' in value_part:
                    num_str = value_part.split('(')[0].strip()
                    metrics['aligned_reads'] = int(num_str)

                    pct_str = value_part.split('(')[1].strip(' )%')
                    metrics['alignment_rate'] = float(pct_str)

    return metrics


def align_with_python(
    input_fastq: str,
    output_sam: str,
    reference_fasta: str,
    max_mismatches: int = 1
) -> Dict:
    """
    Align reads to miRBase using pure Python (FALLBACK METHOD - slower)

    This is a simple implementation using exact/near-exact string matching.
    Not as fast or sophisticated as bowtie, but requires no dependencies.

    Args:
        input_fastq: Path to trimmed FASTQ file
        output_sam: Path to output SAM file
        reference_fasta: Path to miRBase FASTA reference
        max_mismatches: Maximum mismatches allowed (default 1)

    Returns:
        dict with metrics
    """
    if not BIOPYTHON_AVAILABLE:
        raise ImportError("BioPython is required for fallback mode")

    logger.warning("[FALLBACK] Using pure Python alignment (slower)")
    logger.info(f"Aligning reads: {input_fastq}")

    # Load reference sequences
    logger.info(f"[CHECK] Loading reference: {reference_fasta}")
    ref_db = {}
    for record in SeqIO.parse(reference_fasta, "fasta"):
        ref_db[record.id] = str(record.seq).upper()

    logger.info(f"✓ Loaded {len(ref_db)} reference sequences")

    # Align reads
    total_reads = 0
    aligned_reads = 0

    with open(output_sam, 'w') as sam_out:
        # Write SAM header
        sam_out.write("@HD\tVN:1.0\tSO:unsorted\n")
        for ref_id, ref_seq in ref_db.items():
            sam_out.write(f"@SQ\tSN:{ref_id}\tLN:{len(ref_seq)}\n")

        # Align each read
        for record in SeqIO.parse(input_fastq, "fastq"):
            total_reads += 1
            read_seq = str(record.seq).upper()

            # Try to find match in reference
            best_match = _find_best_match(read_seq, ref_db, max_mismatches)

            if best_match:
                aligned_reads += 1
                ref_id, pos, num_mismatches = best_match

                # Write SAM alignment line
                # Format: QNAME FLAG RNAME POS MAPQ CIGAR RNEXT PNEXT TLEN SEQ QUAL
                flag = 0  # Mapped
                mapq = 255 if num_mismatches == 0 else 40  # Mapping quality
                cigar = f"{len(read_seq)}M"  # Match

                sam_out.write(
                    f"{record.id}\t{flag}\t{ref_id}\t{pos}\t{mapq}\t{cigar}\t"
                    f"*\t0\t0\t{read_seq}\t{record.letter_annotations['phred_quality']}\n"
                )
            else:
                # Write unmapped read
                flag = 4  # Unmapped
                sam_out.write(
                    f"{record.id}\t{flag}\t*\t0\t0\t*\t*\t0\t0\t{read_seq}\t"
                    f"{record.letter_annotations['phred_quality']}\n"
                )

    alignment_rate = (aligned_reads / total_reads * 100) if total_reads > 0 else 0.0

    logger.info(f"✓ Aligned: {aligned_reads:,} / {total_reads:,} ({alignment_rate:.1f}%)")

    return {
        'sam_file': output_sam,
        'total_reads': total_reads,
        'aligned_reads': aligned_reads,
        'alignment_rate': alignment_rate,
        'method': 'python'
    }


def _find_best_match(
    read_seq: str,
    ref_db: Dict[str, str],
    max_mismatches: int
) -> Optional[tuple]:
    """
    Find best match for read in reference database

    Args:
        read_seq: Query sequence
        ref_db: Dictionary of reference sequences {id: seq}
        max_mismatches: Maximum mismatches allowed

    Returns:
        (ref_id, position, num_mismatches) if match found, None otherwise
    """
    best_match = None
    best_mismatches = max_mismatches + 1

    for ref_id, ref_seq in ref_db.items():
        # Try to find read in reference (sliding window)
        for pos in range(len(ref_seq) - len(read_seq) + 1):
            ref_window = ref_seq[pos:pos + len(read_seq)]

            # Count mismatches
            mismatches = sum(r != q for r, q in zip(ref_window, read_seq))

            if mismatches <= max_mismatches and mismatches < best_mismatches:
                best_match = (ref_id, pos + 1, mismatches)  # SAM is 1-indexed
                best_mismatches = mismatches

                if mismatches == 0:
                    # Perfect match, stop searching
                    return best_match

    return best_match


def align_to_mirbase(
    input_fastq: str,
    reference_fasta: str,
    output_dir: str,
    sample_id: Optional[str] = None,
    index_dir: Optional[str] = None
) -> Dict:
    """
    Hybrid miRNA alignment: try bowtie first, fallback to Python

    This is the MAIN FUNCTION to use for miRNA alignment.

    Args:
        input_fastq: Path to trimmed FASTQ file
        reference_fasta: Path to miRBase FASTA reference
        output_dir: Output directory path
        sample_id: Sample identifier (optional, for naming)
        index_dir: Directory to store bowtie index (default: same as reference)

    Returns:
        dict: {
            'sam_file': path to output SAM,
            'total_reads': int,
            'aligned_reads': int,
            'alignment_rate': float,
            'method': 'bowtie' or 'python'
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
        output_filename = f"{sample_id}_aligned.sam"
    else:
        output_filename = f"{input_name}_aligned.sam"

    output_sam = str(output_path / output_filename)

    # Try PRIMARY method: bowtie
    if has_bowtie():
        try:
            logger.info("✓ bowtie found - using PRIMARY method")

            # Determine index location
            if index_dir is None:
                index_dir = str(Path(reference_fasta).parent)

            # Build index base name
            ref_name = Path(reference_fasta).stem
            index_base = str(Path(index_dir) / f"{ref_name}_idx")

            # Build index if needed
            if not build_bowtie_index(reference_fasta, index_base):
                raise RuntimeError("Failed to build bowtie index")

            # Align with bowtie
            result = align_with_bowtie(
                input_fastq,
                output_sam,
                index_base
            )
            return result

        except Exception as e:
            logger.warning(f"bowtie failed: {e}, trying fallback...")

    # FALLBACK method: Python
    if BIOPYTHON_AVAILABLE:
        logger.info("⚠ bowtie not available - using FALLBACK Python alignment")
        result = align_with_python(
            input_fastq,
            output_sam,
            reference_fasta
        )
        return result
    else:
        raise RuntimeError(
            "Neither bowtie nor BioPython available. "
            "Install one of them:\n"
            "  pip install biopython\n"
            "  conda install -c bioconda bowtie"
        )


# Test function
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    print("Testing miRNA Aligner Module")
    print("=" * 50)

    # Check available methods
    print(f"\nbowtie available: {has_bowtie()}")
    print(f"BioPython available: {BIOPYTHON_AVAILABLE}")

    print("\nReady for testing with real data!")
