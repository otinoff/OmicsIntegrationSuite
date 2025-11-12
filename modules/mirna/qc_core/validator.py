#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA ID Validation Module
Validate miRNA IDs against miRBase reference per ТЗ requirements
"""

import os
import logging
from pathlib import Path
from typing import Dict, Set, List, Optional

try:
    from Bio import SeqIO
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("BioPython not available for FASTA parsing.")

# Configure logging
logger = logging.getLogger(__name__)


def load_mirbase_ids(reference_fasta: str) -> Set[str]:
    """
    Load valid miRNA IDs from miRBase reference FASTA

    Args:
        reference_fasta: Path to miRBase FASTA file

    Returns:
        set: Set of valid miRNA IDs
    """
    logger.info(f"[CHECK] Loading miRBase IDs from: {reference_fasta}")

    if not os.path.exists(reference_fasta):
        raise FileNotFoundError(f"Reference FASTA not found: {reference_fasta}")

    valid_ids = set()

    if BIOPYTHON_AVAILABLE:
        # Use BioPython to parse FASTA
        for record in SeqIO.parse(reference_fasta, "fasta"):
            valid_ids.add(record.id)
    else:
        # Fallback: manual FASTA parsing
        with open(reference_fasta, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    # Extract ID from header: >hsa-miR-21-5p MIMAT0000076 ...
                    mirna_id = line[1:].split()[0]
                    valid_ids.add(mirna_id)

    logger.info(f"✓ Loaded {len(valid_ids):,} valid miRNA IDs from miRBase")
    return valid_ids


def validate_counts_file(
    counts_tsv: str,
    reference_fasta: str
) -> Dict:
    """
    Validate miRNA IDs in counts.tsv against miRBase reference

    Args:
        counts_tsv: Path to counts.tsv file
        reference_fasta: Path to miRBase reference FASTA

    Returns:
        dict: {
            'total_mirnas': int,
            'valid_mirnas': int,
            'invalid_mirnas': int,
            'invalid_ids': list of invalid IDs,
            'validation_rate': float (percentage)
        }
    """
    logger.info(f"[VALIDATOR] Validating counts file: {counts_tsv}")

    # Load valid IDs from miRBase
    valid_ids = load_mirbase_ids(reference_fasta)

    # Read miRNA IDs from counts.tsv
    found_ids = []
    with open(counts_tsv, 'r') as f:
        # Skip header
        next(f)

        for line in f:
            fields = line.strip().split('\t')
            if len(fields) >= 1:
                mirna_id = fields[0]
                found_ids.append(mirna_id)

    # Validate each ID
    invalid_ids = []
    for mirna_id in found_ids:
        if mirna_id not in valid_ids:
            invalid_ids.append(mirna_id)

    total_mirnas = len(found_ids)
    valid_mirnas = total_mirnas - len(invalid_ids)
    validation_rate = (valid_mirnas / total_mirnas * 100) if total_mirnas > 0 else 0.0

    # Log results
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total miRNAs in counts: {total_mirnas:,}")
    logger.info(f"Valid miRNAs: {valid_mirnas:,}")
    logger.info(f"Invalid miRNAs: {len(invalid_ids):,}")
    logger.info(f"Validation rate: {validation_rate:.1f}%")

    if invalid_ids:
        logger.warning("\n⚠ Invalid miRNA IDs found:")
        for invalid_id in invalid_ids[:10]:  # Show first 10
            logger.warning(f"  - {invalid_id}")
        if len(invalid_ids) > 10:
            logger.warning(f"  ... and {len(invalid_ids) - 10} more")
    else:
        logger.info("\n✓ All miRNA IDs are valid!")

    logger.info("=" * 60)

    return {
        'total_mirnas': total_mirnas,
        'valid_mirnas': valid_mirnas,
        'invalid_mirnas': len(invalid_ids),
        'invalid_ids': invalid_ids,
        'validation_rate': validation_rate
    }


def validate_mirbase_ids(
    counts_tsv: str,
    reference_fasta: str,
    output_dir: Optional[str] = None
) -> Dict:
    """
    Validate miRNA IDs and optionally generate validation report

    This is the MAIN FUNCTION for miRNA ID validation.

    Args:
        counts_tsv: Path to counts.tsv file
        reference_fasta: Path to miRBase reference FASTA
        output_dir: Optional directory to save validation report

    Returns:
        dict: Validation results with metrics
    """
    # Validate counts file
    results = validate_counts_file(counts_tsv, reference_fasta)

    # Generate validation report if output_dir specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate report filename
        counts_name = Path(counts_tsv).stem
        report_file = output_path / f"{counts_name}_validation.txt"

        # Write report
        with open(report_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("miRNA ID Validation Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Input file: {counts_tsv}\n")
            f.write(f"Reference: {reference_fasta}\n\n")
            f.write(f"Total miRNAs: {results['total_mirnas']:,}\n")
            f.write(f"Valid miRNAs: {results['valid_mirnas']:,}\n")
            f.write(f"Invalid miRNAs: {results['invalid_mirnas']:,}\n")
            f.write(f"Validation rate: {results['validation_rate']:.1f}%\n\n")

            if results['invalid_ids']:
                f.write("Invalid miRNA IDs:\n")
                f.write("-" * 60 + "\n")
                for invalid_id in results['invalid_ids']:
                    f.write(f"  - {invalid_id}\n")
            else:
                f.write("✓ All miRNA IDs are valid!\n")

            f.write("\n" + "=" * 60 + "\n")

        logger.info(f"✓ Validation report saved: {report_file}")
        results['report_file'] = str(report_file)

    return results


def check_mirbase_version(reference_fasta: str) -> Dict:
    """
    Extract miRBase version information from reference FASTA

    Args:
        reference_fasta: Path to miRBase reference FASTA

    Returns:
        dict: {
            'version': version string (if found),
            'total_sequences': number of sequences,
            'species': set of species codes (e.g., 'hsa', 'mmu')
        }
    """
    logger.info(f"[CHECK] Checking miRBase version: {reference_fasta}")

    total_sequences = 0
    species_codes = set()
    version = "Unknown"

    with open(reference_fasta, 'r') as f:
        for line in f:
            if line.startswith('>'):
                total_sequences += 1

                # Extract species code (e.g., 'hsa' from 'hsa-miR-21-5p')
                parts = line[1:].split('-', 1)
                if len(parts) > 0:
                    species_codes.add(parts[0].split()[0])

    logger.info(f"✓ Reference contains {total_sequences:,} sequences")
    logger.info(f"✓ Species found: {', '.join(sorted(species_codes))}")

    return {
        'version': version,
        'total_sequences': total_sequences,
        'species': list(sorted(species_codes))
    }


def filter_valid_mirnas(
    counts_tsv: str,
    reference_fasta: str,
    output_tsv: str
) -> Dict:
    """
    Filter counts.tsv to keep only valid miRNA IDs

    Args:
        counts_tsv: Path to input counts.tsv
        reference_fasta: Path to miRBase reference
        output_tsv: Path to output filtered counts.tsv

    Returns:
        dict: Filtering metrics
    """
    logger.info(f"[FILTER] Filtering counts to keep only valid miRNAs")

    # Load valid IDs
    valid_ids = load_mirbase_ids(reference_fasta)

    # Filter counts file
    total_mirnas = 0
    kept_mirnas = 0

    with open(counts_tsv, 'r') as f_in, open(output_tsv, 'w') as f_out:
        # Copy header
        header = f_in.readline()
        f_out.write(header)

        # Filter data lines
        for line in f_in:
            total_mirnas += 1
            fields = line.strip().split('\t')

            if len(fields) >= 1:
                mirna_id = fields[0]

                if mirna_id in valid_ids:
                    f_out.write(line)
                    kept_mirnas += 1

    removed_mirnas = total_mirnas - kept_mirnas
    kept_percent = (kept_mirnas / total_mirnas * 100) if total_mirnas > 0 else 0.0

    logger.info(f"✓ Filtered: {kept_mirnas:,} / {total_mirnas:,} kept ({kept_percent:.1f}%)")
    logger.info(f"  Removed {removed_mirnas:,} invalid IDs")

    return {
        'total_mirnas': total_mirnas,
        'kept_mirnas': kept_mirnas,
        'removed_mirnas': removed_mirnas,
        'kept_percent': kept_percent,
        'output_file': output_tsv
    }


# Test function
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    print("Testing miRNA Validator Module")
    print("=" * 50)

    # Check if test files exist
    test_counts = Path(__file__).parent.parent.parent.parent.parent / \
        "Michael/01_Projects/2025-09-11_Contract_Omics_Platform/iterations" / \
        "Iteration_006_miRNA_Implementation/test_data/output/test_sample_counts.tsv"

    test_reference = Path(__file__).parent.parent.parent.parent.parent / \
        "Michael/01_Projects/2025-09-11_Contract_Omics_Platform/iterations" / \
        "Iteration_006_miRNA_Implementation/reference_data/mirbase_hsa_sample.fa"

    if test_counts.exists() and test_reference.exists():
        print(f"\n✓ Found test files")
        print(f"  Counts: {test_counts}")
        print(f"  Reference: {test_reference}")

        print("\n" + "=" * 50)
        print("Running validation...")
        print("=" * 50)

        # Validate
        result = validate_mirbase_ids(
            counts_tsv=str(test_counts),
            reference_fasta=str(test_reference),
            output_dir=str(test_counts.parent)
        )

        print("\n" + "=" * 50)
        print("VALIDATION COMPLETE")
        print("=" * 50)
        print(f"Total miRNAs: {result['total_mirnas']:,}")
        print(f"Valid miRNAs: {result['valid_mirnas']:,}")
        print(f"Invalid miRNAs: {result['invalid_mirnas']:,}")
        print(f"Validation rate: {result['validation_rate']:.1f}%")

        if result['invalid_mirnas'] == 0:
            print("\n✅ ALL miRNA IDs ARE VALID!")
        else:
            print(f"\n⚠ Found {result['invalid_mirnas']} invalid IDs")

        if 'report_file' in result:
            print(f"\n✓ Report saved: {result['report_file']}")

        # Check miRBase version
        print("\n" + "=" * 50)
        print("miRBase Reference Info")
        print("=" * 50)
        version_info = check_mirbase_version(str(test_reference))
        print(f"Total sequences: {version_info['total_sequences']:,}")
        print(f"Species: {', '.join(version_info['species'])}")

    else:
        print("\n⚠ Test files not found. Run previous tests first!")
        print("Ready for validation with real data!")
