#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA Counting Module
Parse SAM alignments and generate counts.tsv per ТЗ requirements

Output format (from ТЗ Section 1.2.4):
    miRNA_id    sample_id    count
    hsa-miR-21-5p    sample_001    1543
    hsa-let-7a-5p    sample_001    892
    ...
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict, Counter

# Configure logging
logger = logging.getLogger(__name__)


def parse_sam_alignments(sam_file: str) -> Dict[str, int]:
    """
    Parse SAM file and count reads per miRNA

    Args:
        sam_file: Path to SAM alignment file

    Returns:
        dict: {mirna_id: count}
    """
    logger.info(f"[CHECK] Parsing SAM alignments: {sam_file}")

    mirna_counts = Counter()
    total_reads = 0
    aligned_reads = 0

    with open(sam_file, 'r') as f:
        for line in f:
            # Skip header lines
            if line.startswith('@'):
                continue

            # Parse SAM fields
            # Format: QNAME FLAG RNAME POS MAPQ CIGAR RNEXT PNEXT TLEN SEQ QUAL
            fields = line.strip().split('\t')
            if len(fields) < 11:
                continue

            total_reads += 1

            # Extract fields
            flag = int(fields[1])
            rname = fields[2]  # Reference name (miRNA ID)

            # Check if read is mapped (FLAG bit 0x4 = unmapped)
            is_unmapped = (flag & 0x4) != 0

            if not is_unmapped and rname != '*':
                # Read is mapped to a miRNA
                aligned_reads += 1
                mirna_counts[rname] += 1

    logger.info(
        f"✓ Parsed: {total_reads:,} reads, "
        f"{aligned_reads:,} aligned, "
        f"{len(mirna_counts):,} unique miRNAs"
    )

    return dict(mirna_counts)


def write_counts_tsv(
    counts_dict: Dict[str, int],
    output_file: str,
    sample_id: str
) -> None:
    """
    Write counts to TSV file in ТЗ format

    Args:
        counts_dict: Dictionary {mirna_id: count}
        output_file: Path to output TSV file
        sample_id: Sample identifier
    """
    logger.info(f"[CHECK] Writing counts to TSV: {output_file}")

    # Sort by count (descending) for better readability
    sorted_counts = sorted(
        counts_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )

    with open(output_file, 'w') as f:
        # Write header (ТЗ format)
        f.write("miRNA_id\tsample_id\tcount\n")

        # Write counts
        for mirna_id, count in sorted_counts:
            f.write(f"{mirna_id}\t{sample_id}\t{count}\n")

    logger.info(f"✓ Wrote {len(counts_dict):,} miRNA counts to {output_file}")


def generate_counts_tsv(
    sam_file: str,
    output_dir: str,
    sample_id: str,
    output_filename: Optional[str] = None
) -> Dict:
    """
    Generate counts.tsv from SAM alignment file

    This is the MAIN FUNCTION for miRNA counting.

    Args:
        sam_file: Path to SAM alignment file
        output_dir: Output directory path
        sample_id: Sample identifier
        output_filename: Custom output filename (default: {sample_id}_counts.tsv)

    Returns:
        dict: {
            'counts_tsv': path to counts.tsv file,
            'total_reads': total reads in SAM,
            'aligned_reads': reads aligned to miRNA,
            'unique_mirnas': number of unique miRNAs detected,
            'top_mirnas': list of top 10 abundant miRNAs [(id, count), ...]
        }
    """
    logger.info(f"[COUNTER] Generating counts.tsv from SAM: {sam_file}")

    # Validate input
    if not os.path.exists(sam_file):
        raise FileNotFoundError(f"SAM file not found: {sam_file}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Determine output filename
    if output_filename is None:
        output_filename = f"{sample_id}_counts.tsv"

    output_tsv = str(output_path / output_filename)

    # Parse SAM and count reads per miRNA
    mirna_counts = parse_sam_alignments(sam_file)

    if not mirna_counts:
        logger.warning("⚠ No aligned reads found in SAM file!")
        # Still create empty TSV with header
        with open(output_tsv, 'w') as f:
            f.write("miRNA_id\tsample_id\tcount\n")

        return {
            'counts_tsv': output_tsv,
            'total_reads': 0,
            'aligned_reads': 0,
            'unique_mirnas': 0,
            'top_mirnas': []
        }

    # Write counts to TSV
    write_counts_tsv(mirna_counts, output_tsv, sample_id)

    # Calculate metrics
    total_aligned = sum(mirna_counts.values())
    unique_mirnas = len(mirna_counts)

    # Get top 10 abundant miRNAs
    top_mirnas = sorted(
        mirna_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    # Log summary
    logger.info("\n" + "=" * 60)
    logger.info("COUNTING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Sample ID: {sample_id}")
    logger.info(f"Total aligned reads: {total_aligned:,}")
    logger.info(f"Unique miRNAs detected: {unique_mirnas:,}")
    logger.info("\nTop 10 abundant miRNAs:")
    for i, (mirna_id, count) in enumerate(top_mirnas, 1):
        pct = (count / total_aligned * 100) if total_aligned > 0 else 0
        logger.info(f"  {i:2d}. {mirna_id:30s} {count:6,} ({pct:5.1f}%)")
    logger.info("=" * 60)

    return {
        'counts_tsv': output_tsv,
        'total_reads': total_aligned,  # Note: This is from SAM, may differ from FASTQ
        'aligned_reads': total_aligned,
        'unique_mirnas': unique_mirnas,
        'top_mirnas': top_mirnas
    }


def merge_counts_tables(
    counts_files: list,
    output_file: str,
    fill_missing: int = 0
) -> None:
    """
    Merge multiple counts.tsv files into a single matrix

    Useful for comparing multiple samples.

    Args:
        counts_files: List of paths to counts.tsv files
        output_file: Path to output merged file
        fill_missing: Value to use for missing counts (default 0)

    Output format:
        miRNA_id    sample_001    sample_002    sample_003
        hsa-miR-21-5p    1543    892    2103
        hsa-let-7a-5p    892    450    1234
        ...
    """
    logger.info(f"[MERGE] Merging {len(counts_files)} counts tables")

    # Read all counts files
    all_mirnas = set()
    sample_counts = {}  # {sample_id: {mirna_id: count}}

    for counts_file in counts_files:
        with open(counts_file, 'r') as f:
            # Skip header
            next(f)

            for line in f:
                fields = line.strip().split('\t')
                if len(fields) != 3:
                    continue

                mirna_id, sample_id, count = fields
                count = int(count)

                all_mirnas.add(mirna_id)

                if sample_id not in sample_counts:
                    sample_counts[sample_id] = {}

                sample_counts[sample_id][mirna_id] = count

    # Sort miRNAs and samples
    sorted_mirnas = sorted(all_mirnas)
    sorted_samples = sorted(sample_counts.keys())

    # Write merged table
    with open(output_file, 'w') as f:
        # Write header
        f.write("miRNA_id\t" + "\t".join(sorted_samples) + "\n")

        # Write counts for each miRNA
        for mirna_id in sorted_mirnas:
            counts = [
                str(sample_counts[sample].get(mirna_id, fill_missing))
                for sample in sorted_samples
            ]
            f.write(f"{mirna_id}\t" + "\t".join(counts) + "\n")

    logger.info(f"✓ Merged table written: {output_file}")
    logger.info(f"  {len(sorted_mirnas):,} miRNAs × {len(sorted_samples):,} samples")


# Test function
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    print("Testing miRNA Counter Module")
    print("=" * 50)

    # Check if test SAM file exists
    test_sam = Path(__file__).parent.parent.parent.parent.parent / \
        "Michael/01_Projects/2025-09-11_Contract_Omics_Platform/iterations" / \
        "Iteration_006_miRNA_Implementation/test_data/output/test_sample_aligned.sam"

    if test_sam.exists():
        print(f"\nFound test SAM file: {test_sam}")
        print("\nGenerating counts.tsv...")

        result = generate_counts_tsv(
            sam_file=str(test_sam),
            output_dir=str(test_sam.parent),
            sample_id="test_sample"
        )

        print(f"\n✓ Counts TSV: {result['counts_tsv']}")
        print(f"  Aligned reads: {result['aligned_reads']:,}")
        print(f"  Unique miRNAs: {result['unique_mirnas']:,}")

        # Show file contents
        print("\n[PREVIEW] counts.tsv:")
        with open(result['counts_tsv'], 'r') as f:
            for i, line in enumerate(f):
                print(f"  {line.rstrip()}")
                if i >= 10:  # Show first 10 lines
                    break

    else:
        print("\n⚠ Test SAM file not found. Run test_aligner.py first!")
        print("Ready for testing with real SAM data!")
