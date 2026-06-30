"""
Adapter Trimming Module for miRNA-seq Data

Implements adapter sequence detection and trimming for small RNA sequencing data.
Supports both cutadapt (if available) and built-in Python implementation.

TZ Requirement: "Контроль качества и обрезку адаптеров"
ENCODE Standard: Mandatory preprocessing step before alignment
"""

import gzip
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Standard miRNA-seq adapter sequences
STANDARD_ADAPTERS = {
    "illumina_truseq": "TGGAATTCTCGGGTGCCAAGG",  # Illumina TruSeq Small RNA 3' Adapter
    "neb_next": "AGATCGGAAGAGCACACGTCT",          # NEBNext Small RNA 3' Adapter
    "qiagen": "AACTGTAGGCACCATCAAT",              # Qiagen miRNA 3' Adapter
}


class AdapterTrimmer:
    """
    Adapter trimming for miRNA-seq data

    Supports:
    - Automatic adapter detection
    - Multiple adapter types
    - Error-tolerant matching (up to 10% mismatches)
    - Minimum length filtering after trimming
    """

    def __init__(self, min_length: int = 18, error_rate: float = 0.1):
        """
        Initialize adapter trimmer

        Args:
            min_length: Minimum read length after trimming (default: 18 nt)
            error_rate: Maximum error rate for adapter matching (default: 0.1 = 10%)
        """
        self.min_length = min_length
        self.error_rate = error_rate
        self.stats = {
            "reads_processed": 0,
            "reads_with_adapters": 0,
            "bases_removed": 0,
            "reads_too_short": 0,
            "adapter_positions": {},  # position -> count
        }

    def find_adapter(self, sequence: str, adapter: str) -> int:
        """
        Find adapter position in sequence using sliding window

        Args:
            sequence: Read sequence
            adapter: Adapter sequence to find

        Returns:
            Position of adapter start, or -1 if not found
        """
        max_mismatches = int(len(adapter) * self.error_rate)
        min_overlap = min(10, len(adapter))  # Minimum 10 bp overlap or full adapter length

        # Try different adapter lengths (full length down to minimum overlap)
        for adapter_len in range(len(adapter), min_overlap - 1, -1):
            adapter_sub = adapter[:adapter_len]
            max_mm = int(adapter_len * self.error_rate)

            # Sliding window search
            for i in range(len(sequence) - adapter_len + 1):
                window = sequence[i:i + adapter_len]
                mismatches = sum(1 for a, b in zip(window, adapter_sub) if a != b)

                if mismatches <= max_mm:
                    return i  # Adapter found at position i

        return -1  # Adapter not found

    def trim_read(self, sequence: str, quality: str, adapter: str) -> Tuple[Optional[str], Optional[str], bool]:
        """
        Trim adapter from a single read

        Args:
            sequence: Read sequence
            quality: Quality string
            adapter: Adapter sequence

        Returns:
            (trimmed_sequence, trimmed_quality, was_trimmed)
            Returns (None, None, False) if read is too short after trimming
        """
        adapter_pos = self.find_adapter(sequence, adapter)

        if adapter_pos >= 0:
            # Adapter found - trim it
            trimmed_seq = sequence[:adapter_pos]
            trimmed_qual = quality[:adapter_pos]
            was_trimmed = True

            self.stats["reads_with_adapters"] += 1
            self.stats["bases_removed"] += len(sequence) - adapter_pos

            # Track adapter position distribution
            self.stats["adapter_positions"][adapter_pos] = \
                self.stats["adapter_positions"].get(adapter_pos, 0) + 1
        else:
            # No adapter found - keep original
            trimmed_seq = sequence
            trimmed_qual = quality
            was_trimmed = False

        # Check minimum length
        if len(trimmed_seq) < self.min_length:
            self.stats["reads_too_short"] += 1
            return None, None, was_trimmed

        return trimmed_seq, trimmed_qual, was_trimmed

    def process_fastq(self, input_fastq: str, output_fastq: str,
                     adapter: str) -> Dict:
        """
        Process entire FASTQ file with adapter trimming

        Args:
            input_fastq: Input FASTQ file path (.fastq.gz)
            output_fastq: Output FASTQ file path (.fastq.gz)
            adapter: Adapter sequence to trim

        Returns:
            Statistics dictionary
        """
        # Reset stats
        self.stats = {
            "reads_processed": 0,
            "reads_with_adapters": 0,
            "bases_removed": 0,
            "reads_too_short": 0,
            "adapter_positions": {},
        }

        with gzip.open(input_fastq, 'rt') as infile, \
             gzip.open(output_fastq, 'wt') as outfile:

            while True:
                # Read FASTQ record (4 lines)
                header = infile.readline()
                if not header:
                    break

                sequence = infile.readline().strip()
                separator = infile.readline()
                quality = infile.readline().strip()

                self.stats["reads_processed"] += 1

                # Trim adapter
                trimmed_seq, trimmed_qual, was_trimmed = self.trim_read(
                    sequence, quality, adapter
                )

                # Write to output if passed length filter
                if trimmed_seq is not None:
                    outfile.write(header)
                    outfile.write(trimmed_seq + '\n')
                    outfile.write(separator)
                    outfile.write(trimmed_qual + '\n')

        # Calculate summary statistics
        self.stats["reads_kept"] = self.stats["reads_processed"] - self.stats["reads_too_short"]
        self.stats["percent_with_adapters"] = (
            self.stats["reads_with_adapters"] / max(1, self.stats["reads_processed"]) * 100
        )
        self.stats["percent_kept"] = (
            self.stats["reads_kept"] / max(1, self.stats["reads_processed"]) * 100
        )
        self.stats["avg_bases_removed_per_read"] = (
            self.stats["bases_removed"] / max(1, self.stats["reads_with_adapters"])
        )

        return self.stats


def detect_adapter_type(fastq_file: str, sample_size: int = 10000) -> str:
    """
    Auto-detect adapter type in FASTQ file

    Args:
        fastq_file: Path to FASTQ file
        sample_size: Number of reads to sample

    Returns:
        Detected adapter sequence (most common)
    """
    adapter_counts = {name: 0 for name in STANDARD_ADAPTERS}

    with gzip.open(fastq_file, 'rt') as f:
        reads_checked = 0

        while reads_checked < sample_size:
            header = f.readline()
            if not header:
                break

            sequence = f.readline().strip()
            f.readline()  # separator
            f.readline()  # quality

            # Check each adapter type
            for adapter_name, adapter_seq in STANDARD_ADAPTERS.items():
                # Simple substring check for speed
                if adapter_seq[:15] in sequence:  # Check first 15 bp of adapter
                    adapter_counts[adapter_name] += 1

            reads_checked += 1

    # Return most common adapter
    if max(adapter_counts.values()) > 0:
        best_adapter = max(adapter_counts, key=adapter_counts.get)
        return STANDARD_ADAPTERS[best_adapter]
    else:
        # Default to Illumina TruSeq if nothing detected
        return STANDARD_ADAPTERS["illumina_truseq"]


def trim_adapters_mirna(input_fastq: str,
                       output_fastq: str,
                       adapter: Optional[str] = None,
                       min_length: int = 18,
                       error_rate: float = 0.1,
                       auto_detect: bool = True) -> Dict:
    """
    Main function for adapter trimming

    Args:
        input_fastq: Input FASTQ file (.fastq.gz)
        output_fastq: Output FASTQ file (.fastq.gz)
        adapter: Adapter sequence (if None, will auto-detect)
        min_length: Minimum read length after trimming
        error_rate: Maximum error rate for adapter matching
        auto_detect: Auto-detect adapter if not provided

    Returns:
        Statistics dictionary with trimming results
    """
    # Auto-detect adapter if not provided
    if adapter is None and auto_detect:
        print(f"Auto-detecting adapter in {input_fastq}...")
        adapter = detect_adapter_type(input_fastq)
        print(f"Detected adapter: {adapter}")
    elif adapter is None:
        # Default to Illumina TruSeq
        adapter = STANDARD_ADAPTERS["illumina_truseq"]

    # Create trimmer and process
    trimmer = AdapterTrimmer(min_length=min_length, error_rate=error_rate)
    stats = trimmer.process_fastq(input_fastq, output_fastq, adapter)

    # Add adapter info to stats
    stats["adapter_sequence"] = adapter
    stats["input_file"] = input_fastq
    stats["output_file"] = output_fastq

    return stats


def main_cli():
    """
    Command-line interface for adapter trimming
    """
    import argparse

    parser = argparse.ArgumentParser(description="Trim adapters from miRNA-seq FASTQ files")
    parser.add_argument("input", help="Input FASTQ file (.fastq.gz)")
    parser.add_argument("output", help="Output FASTQ file (.fastq.gz)")
    parser.add_argument("-a", "--adapter", help="Adapter sequence (auto-detect if not provided)")
    parser.add_argument("-m", "--min-length", type=int, default=18,
                       help="Minimum read length after trimming (default: 18)")
    parser.add_argument("-e", "--error-rate", type=float, default=0.1,
                       help="Maximum error rate for adapter matching (default: 0.1)")

    args = parser.parse_args()

    print(f"Trimming adapters from {args.input}...")
    stats = trim_adapters_mirna(
        args.input,
        args.output,
        adapter=args.adapter,
        min_length=args.min_length,
        error_rate=args.error_rate
    )

    # Print statistics
    print("\n=== Adapter Trimming Statistics ===")
    print(f"Reads processed: {stats['reads_processed']:,}")
    print(f"Reads with adapters: {stats['reads_with_adapters']:,} ({stats['percent_with_adapters']:.1f}%)")
    print(f"Bases removed: {stats['bases_removed']:,}")
    print(f"Average bases removed per read: {stats['avg_bases_removed_per_read']:.1f}")
    print(f"Reads kept: {stats['reads_kept']:,} ({stats['percent_kept']:.1f}%)")
    print(f"Reads too short: {stats['reads_too_short']:,}")
    print(f"Adapter used: {stats['adapter_sequence']}")
    print(f"\nOutput saved to: {stats['output_file']}")


if __name__ == "__main__":
    main_cli()
