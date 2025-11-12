#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA Quality Control Pipeline
Main integration module that orchestrates the complete miRNA-seq QC workflow

Per ТЗ requirements (Sections 1.2.4, 1.3.4):
1. Adapter trimming and quality filtering
2. Length filtering (18-25 nt)
3. Alignment to miRBase reference
4. ID validation
5. Generation of counts.tsv

Architecture: Identical to genomics module
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional
import json
from datetime import datetime

# Import core QC modules
from .qc_core.trimmer import trim_adapters
from .qc_core.aligner import align_to_mirbase
from .qc_core.counter import generate_counts_tsv
from .qc_core.validator import validate_mirbase_ids

# Import logging system
from .logging_system import QCLogger, get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize QC logger (from genomics module pattern)
qc_logger = get_logger(verbose=True, use_colors=False)


def run_mirna_qc(
    input_fastq: str,
    reference_fasta: str,
    output_dir: str,
    sample_id: Optional[str] = None,
    min_length: int = 18,
    max_length: int = 25,
    index_dir: Optional[str] = None,
    validate_ids: bool = True
) -> Dict:
    """
    Run complete miRNA-seq quality control pipeline

    This is the MAIN FUNCTION that integrates all QC modules per ТЗ requirements.

    Pipeline stages:
    1. Adapter trimming + length/quality filtering (18-25 nt)
    2. Alignment to miRBase reference
    3. Read counting per miRNA
    4. ID validation against miRBase
    5. Metadata generation

    Args:
        input_fastq: Path to raw FASTQ file
        reference_fasta: Path to miRBase reference FASTA
        output_dir: Output directory for results
        sample_id: Sample identifier (auto-generated if None)
        min_length: Minimum read length (default 18 from ТЗ)
        max_length: Maximum read length (default 25 from ТЗ)
        index_dir: Directory for bowtie index (default: same as reference)
        validate_ids: Run ID validation (default True)

    Returns:
        dict: Complete pipeline results with all metrics and file paths
    """
    # Initialize
    qc_logger.header("miRNA Quality Control Pipeline")
    qc_logger.info(f"Sample: {sample_id or Path(input_fastq).stem}")
    qc_logger.info(f"Input FASTQ: {input_fastq}")
    qc_logger.info(f"Reference: {reference_fasta}")

    # Validate inputs
    if not os.path.exists(input_fastq):
        qc_logger.error(f"Input FASTQ not found: {input_fastq}")
        raise FileNotFoundError(f"Input FASTQ not found: {input_fastq}")

    if not os.path.exists(reference_fasta):
        qc_logger.error(f"Reference FASTA not found: {reference_fasta}")
        raise FileNotFoundError(f"Reference FASTA not found: {reference_fasta}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate sample ID if not provided
    if sample_id is None:
        sample_id = Path(input_fastq).stem
        if sample_id.endswith('.fastq'):
            sample_id = sample_id[:-6]

    # Store pipeline metadata
    pipeline_metadata = {
        'sample_id': sample_id,
        'input_fastq': input_fastq,
        'reference_fasta': reference_fasta,
        'output_dir': output_dir,
        'min_length': min_length,
        'max_length': max_length,
        'start_time': datetime.now().isoformat(),
        'stages': {}
    }

    try:
        # ===================================================================
        # STAGE 1: Adapter Trimming + Length/Quality Filtering
        # ===================================================================
        qc_logger.header("STAGE 1: Adapter Trimming & Filtering")
        qc_logger.check(f"Length filter: {min_length}-{max_length} nt (ТЗ requirement)")

        trim_result = trim_adapters(
            input_fastq=input_fastq,
            output_dir=output_dir,
            min_length=min_length,
            max_length=max_length,
            sample_id=sample_id
        )

        qc_logger.ok(f"Trimming complete: {trim_result['method']} method")
        qc_logger.info(
            f"  Filtered: {trim_result['filtered_reads']:,} / {trim_result['total_reads']:,} "
            f"({trim_result['percent_kept']:.1f}%)"
        )

        pipeline_metadata['stages']['trimming'] = {
            'method': trim_result['method'],
            'total_reads': trim_result['total_reads'],
            'filtered_reads': trim_result['filtered_reads'],
            'percent_kept': trim_result['percent_kept'],
            'output_file': trim_result['trimmed_fastq']
        }

        # ===================================================================
        # STAGE 2: Alignment to miRBase
        # ===================================================================
        qc_logger.header("STAGE 2: Alignment to miRBase")

        align_result = align_to_mirbase(
            input_fastq=trim_result['trimmed_fastq'],
            reference_fasta=reference_fasta,
            output_dir=output_dir,
            sample_id=sample_id,
            index_dir=index_dir
        )

        qc_logger.ok(f"Alignment complete: {align_result['method']} method")
        qc_logger.info(
            f"  Aligned: {align_result['aligned_reads']:,} / {align_result['total_reads']:,} "
            f"({align_result['alignment_rate']:.1f}%)"
        )

        pipeline_metadata['stages']['alignment'] = {
            'method': align_result['method'],
            'total_reads': align_result['total_reads'],
            'aligned_reads': align_result['aligned_reads'],
            'alignment_rate': align_result['alignment_rate'],
            'output_file': align_result['sam_file']
        }

        # ===================================================================
        # STAGE 3: Read Counting per miRNA
        # ===================================================================
        qc_logger.header("STAGE 3: miRNA Counting")

        count_result = generate_counts_tsv(
            sam_file=align_result['sam_file'],
            output_dir=output_dir,
            sample_id=sample_id
        )

        qc_logger.ok(f"Counting complete: {count_result['unique_mirnas']:,} unique miRNAs")
        qc_logger.info(f"  Output: {count_result['counts_tsv']}")

        # Show top miRNAs
        if count_result['top_mirnas']:
            qc_logger.info("  Top 5 abundant miRNAs:")
            for i, (mirna_id, count) in enumerate(count_result['top_mirnas'][:5], 1):
                pct = (count / count_result['aligned_reads'] * 100) if count_result['aligned_reads'] > 0 else 0
                qc_logger.info(f"    {i}. {mirna_id}: {count:,} ({pct:.1f}%)")

        pipeline_metadata['stages']['counting'] = {
            'aligned_reads': count_result['aligned_reads'],
            'unique_mirnas': count_result['unique_mirnas'],
            'top_mirnas': count_result['top_mirnas'][:10],  # Store top 10
            'output_file': count_result['counts_tsv']
        }

        # ===================================================================
        # STAGE 4: ID Validation (if requested)
        # ===================================================================
        if validate_ids:
            qc_logger.header("STAGE 4: ID Validation")

            validation_result = validate_mirbase_ids(
                counts_tsv=count_result['counts_tsv'],
                reference_fasta=reference_fasta,
                output_dir=output_dir
            )

            qc_logger.ok(f"Validation complete: {validation_result['validation_rate']:.1f}% valid")

            if validation_result['invalid_mirnas'] > 0:
                qc_logger.warning(
                    f"  Found {validation_result['invalid_mirnas']} invalid IDs (see validation report)"
                )
            else:
                qc_logger.info("  All miRNA IDs are valid!")

            pipeline_metadata['stages']['validation'] = {
                'total_mirnas': validation_result['total_mirnas'],
                'valid_mirnas': validation_result['valid_mirnas'],
                'invalid_mirnas': validation_result['invalid_mirnas'],
                'validation_rate': validation_result['validation_rate']
            }

            if 'report_file' in validation_result:
                pipeline_metadata['stages']['validation']['report_file'] = validation_result['report_file']

        # ===================================================================
        # FINALIZE: Save Pipeline Metadata
        # ===================================================================
        pipeline_metadata['end_time'] = datetime.now().isoformat()
        pipeline_metadata['status'] = 'completed'

        metadata_file = output_path / f"{sample_id}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(pipeline_metadata, f, indent=2)

        qc_logger.info(f"Metadata saved: {metadata_file}")

        # ===================================================================
        # SUMMARY
        # ===================================================================
        qc_logger.header("PIPELINE SUMMARY")
        qc_logger.ok(f"Sample: {sample_id}")
        qc_logger.info(f"  Input reads: {pipeline_metadata['stages']['trimming']['total_reads']:,}")
        qc_logger.info(
            f"  After filtering: {pipeline_metadata['stages']['trimming']['filtered_reads']:,} "
            f"({pipeline_metadata['stages']['trimming']['percent_kept']:.1f}%)"
        )
        qc_logger.info(
            f"  Aligned reads: {pipeline_metadata['stages']['alignment']['aligned_reads']:,} "
            f"({pipeline_metadata['stages']['alignment']['alignment_rate']:.1f}%)"
        )
        qc_logger.info(f"  Unique miRNAs: {pipeline_metadata['stages']['counting']['unique_mirnas']:,}")

        if validate_ids:
            qc_logger.info(
                f"  Valid IDs: {pipeline_metadata['stages']['validation']['valid_mirnas']:,} / "
                f"{pipeline_metadata['stages']['validation']['total_mirnas']:,} "
                f"({pipeline_metadata['stages']['validation']['validation_rate']:.1f}%)"
            )

        qc_logger.ok("✓ Pipeline completed successfully!")

        # Return complete results
        return {
            'status': 'completed',
            'sample_id': sample_id,
            'metadata_file': str(metadata_file),
            'counts_tsv': count_result['counts_tsv'],
            'sam_file': align_result['sam_file'],
            'trimmed_fastq': trim_result['trimmed_fastq'],
            'pipeline_metadata': pipeline_metadata
        }

    except Exception as e:
        qc_logger.error(f"Pipeline failed: {e}")
        pipeline_metadata['end_time'] = datetime.now().isoformat()
        pipeline_metadata['status'] = 'failed'
        pipeline_metadata['error'] = str(e)

        # Save metadata even on failure
        metadata_file = output_path / f"{sample_id}_metadata_FAILED.json"
        with open(metadata_file, 'w') as f:
            json.dump(pipeline_metadata, f, indent=2)

        raise


def run_mirna_qc_batch(
    fastq_files: list,
    reference_fasta: str,
    output_dir: str,
    **kwargs
) -> Dict:
    """
    Run miRNA QC pipeline on multiple FASTQ files

    Args:
        fastq_files: List of FASTQ file paths
        reference_fasta: Path to miRBase reference
        output_dir: Output directory for all results
        **kwargs: Additional arguments passed to run_mirna_qc()

    Returns:
        dict: Batch processing results
    """
    qc_logger.header(f"Batch Processing: {len(fastq_files)} samples")

    results = {
        'total_samples': len(fastq_files),
        'completed': 0,
        'failed': 0,
        'samples': {}
    }

    for fastq_file in fastq_files:
        sample_id = Path(fastq_file).stem
        qc_logger.info(f"\nProcessing: {sample_id}")

        try:
            sample_output = Path(output_dir) / sample_id
            sample_result = run_mirna_qc(
                input_fastq=fastq_file,
                reference_fasta=reference_fasta,
                output_dir=str(sample_output),
                sample_id=sample_id,
                **kwargs
            )

            results['samples'][sample_id] = {
                'status': 'completed',
                'counts_tsv': sample_result['counts_tsv']
            }
            results['completed'] += 1

        except Exception as e:
            qc_logger.error(f"Failed: {sample_id} - {e}")
            results['samples'][sample_id] = {
                'status': 'failed',
                'error': str(e)
            }
            results['failed'] += 1

    qc_logger.header("BATCH SUMMARY")
    qc_logger.ok(f"Completed: {results['completed']} / {results['total_samples']}")
    if results['failed'] > 0:
        qc_logger.warning(f"Failed: {results['failed']} / {results['total_samples']}")

    return results


# Test function
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="miRNA Quality Control Pipeline")
    parser.add_argument('--fastq', required=True, help='Input FASTQ file')
    parser.add_argument('--reference', required=True, help='miRBase reference FASTA')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--sample-id', help='Sample identifier')
    parser.add_argument('--min-length', type=int, default=18, help='Minimum length (default: 18)')
    parser.add_argument('--max-length', type=int, default=25, help='Maximum length (default: 25)')

    args = parser.parse_args()

    try:
        result = run_mirna_qc(
            input_fastq=args.fastq,
            reference_fasta=args.reference,
            output_dir=args.output,
            sample_id=args.sample_id,
            min_length=args.min_length,
            max_length=args.max_length
        )

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Counts TSV: {result['counts_tsv']}")
        print(f"SAM file: {result['sam_file']}")
        print(f"Metadata: {result['metadata_file']}")

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
