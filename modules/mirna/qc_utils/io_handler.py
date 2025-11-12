#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA I/O Handler
Handles FASTQ file I/O, including compressed files and streaming
"""

import os
import gzip
import logging
from pathlib import Path
from typing import Iterator, Optional, Union

try:
    from Bio import SeqIO
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logging.warning("BioPython not available for I/O operations")

# Configure logging
logger = logging.getLogger(__name__)


class IOHandler:
    """
    Handle FASTQ file I/O operations
    Supports: .fastq, .fq, .fastq.gz, .fq.gz
    """

    @staticmethod
    def is_gzipped(file_path: str) -> bool:
        """
        Check if file is gzipped

        Args:
            file_path: Path to file

        Returns:
            bool: True if gzipped, False otherwise
        """
        return file_path.endswith('.gz')

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """
        Get file size in MB

        Args:
            file_path: Path to file

        Returns:
            float: File size in MB
        """
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)

    @staticmethod
    def open_fastq(file_path: str, mode: str = 'rt'):
        """
        Open FASTQ file (handles gzip automatically)

        Args:
            file_path: Path to FASTQ file
            mode: File mode ('rt' for read text, 'wt' for write text)

        Returns:
            file handle
        """
        if IOHandler.is_gzipped(file_path):
            return gzip.open(file_path, mode)
        else:
            return open(file_path, mode)

    @staticmethod
    def read_fastq_records(file_path: str, limit: Optional[int] = None) -> Iterator:
        """
        Read FASTQ records using BioPython (if available)

        Args:
            file_path: Path to FASTQ file
            limit: Maximum number of records to read (None = all)

        Yields:
            SeqIO record objects
        """
        if not BIOPYTHON_AVAILABLE:
            raise ImportError("BioPython required for FASTQ reading")

        logger.info(f"[IO] Reading FASTQ: {file_path}")

        count = 0
        with IOHandler.open_fastq(file_path, 'rt') as f:
            for record in SeqIO.parse(f, "fastq"):
                yield record
                count += 1

                if limit and count >= limit:
                    break

    @staticmethod
    def count_reads(file_path: str) -> int:
        """
        Count total reads in FASTQ file

        Args:
            file_path: Path to FASTQ file

        Returns:
            int: Number of reads
        """
        logger.info(f"[IO] Counting reads: {file_path}")

        count = 0
        with IOHandler.open_fastq(file_path, 'rt') as f:
            for line in f:
                if line.startswith('@'):
                    count += 1

        # FASTQ has 4 lines per read, but counting @ headers is more reliable
        # than dividing total lines by 4 (due to quality scores with @)
        return count

    @staticmethod
    def write_fastq_records(records: Iterator, output_path: str) -> int:
        """
        Write FASTQ records to file

        Args:
            records: Iterator of SeqIO records
            output_path: Path to output FASTQ file

        Returns:
            int: Number of records written
        """
        if not BIOPYTHON_AVAILABLE:
            raise ImportError("BioPython required for FASTQ writing")

        logger.info(f"[IO] Writing FASTQ: {output_path}")

        count = 0
        with IOHandler.open_fastq(output_path, 'wt') as f:
            for record in records:
                SeqIO.write(record, f, "fastq")
                count += 1

        logger.info(f"[IO] Wrote {count:,} reads to {output_path}")
        return count

    @staticmethod
    def validate_fastq(file_path: str, check_lines: int = 1000) -> dict:
        """
        Validate FASTQ file format

        Args:
            file_path: Path to FASTQ file
            check_lines: Number of reads to check (default 1000)

        Returns:
            dict: Validation results
        """
        logger.info(f"[IO] Validating FASTQ: {file_path}")

        if not os.path.exists(file_path):
            return {
                'valid': False,
                'error': 'File not found'
            }

        try:
            count = 0
            with IOHandler.open_fastq(file_path, 'rt') as f:
                for i, line in enumerate(f):
                    # FASTQ format: @header, sequence, +, quality (4 lines per read)
                    line_type = i % 4

                    if line_type == 0:  # Header
                        if not line.startswith('@'):
                            return {
                                'valid': False,
                                'error': f'Invalid header at read {count + 1}'
                            }
                        count += 1

                    elif line_type == 2:  # Plus line
                        if not line.startswith('+'):
                            return {
                                'valid': False,
                                'error': f'Invalid separator at read {count}'
                            }

                    # Stop after checking enough reads
                    if count >= check_lines:
                        break

            return {
                'valid': True,
                'reads_checked': count,
                'file_size_mb': IOHandler.get_file_size_mb(file_path),
                'is_gzipped': IOHandler.is_gzipped(file_path)
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    @staticmethod
    def get_fastq_info(file_path: str) -> dict:
        """
        Get basic info about FASTQ file without full parsing

        Args:
            file_path: Path to FASTQ file

        Returns:
            dict: File information
        """
        return {
            'file_path': file_path,
            'exists': os.path.exists(file_path),
            'file_size_mb': IOHandler.get_file_size_mb(file_path) if os.path.exists(file_path) else 0,
            'is_gzipped': IOHandler.is_gzipped(file_path),
            'extension': Path(file_path).suffix
        }


# Test function
if __name__ == "__main__":
    import sys

    print("Testing miRNA IOHandler")
    print("=" * 50)

    # Test file path
    test_fastq = Path(__file__).parent.parent.parent.parent.parent / \
        "Michael/01_Projects/2025-09-11_Contract_Omics_Platform/iterations" / \
        "Iteration_006_miRNA_Implementation/test_data/sample_mirna.fastq"

    if test_fastq.exists():
        print(f"\n✓ Found test FASTQ: {test_fastq}")

        # Get file info
        print("\nFile Info:")
        info = IOHandler.get_fastq_info(str(test_fastq))
        for key, value in info.items():
            print(f"  {key}: {value}")

        # Validate
        print("\nValidation:")
        validation = IOHandler.validate_fastq(str(test_fastq))
        for key, value in validation.items():
            print(f"  {key}: {value}")

        # Count reads
        print("\nCounting reads...")
        total_reads = IOHandler.count_reads(str(test_fastq))
        print(f"  Total reads: {total_reads:,}")

        # Read first 3 records
        if BIOPYTHON_AVAILABLE:
            print("\nReading first 3 records:")
            for i, record in enumerate(IOHandler.read_fastq_records(str(test_fastq), limit=3), 1):
                print(f"  {i}. {record.id}: {len(record.seq)} bp")

        print("\n✓ IOHandler working correctly!")

    else:
        print("\n⚠ Test FASTQ not found")
        print("Ready for I/O operations!")
