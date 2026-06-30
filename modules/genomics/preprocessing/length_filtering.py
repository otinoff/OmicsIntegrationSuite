"""
Length Filtering Module for miRNA-seq Data

Filters reads by length to retain only mature miRNA range (18-25 nucleotides).

TZ Requirement: "Фильтрацию по длине фрагментов (18-25 нуклеотидов)"
Biological Range: Mature miRNA = 18-25 nt (most common: 21-23 nt)
"""

import gzip
from typing import Dict, Optional
from collections import defaultdict


class LengthFilter:
    """
    Length-based filtering for small RNA sequencing data
    """

    def __init__(self, min_length: int = 18, max_length: int = 25):
        """
        Initialize length filter

        Args:
            min_length: Minimum read length to keep (default: 18 nt)
            max_length: Maximum read length to keep (default: 25 nt)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.stats = {
            "total_reads": 0,
            "passed_reads": 0,
            "too_short": 0,
            "too_long": 0,
            "length_distribution": defaultdict(int),
        }

    def passes_filter(self, sequence: str) -> bool:
        """
        Check if read passes length filter

        Args:
            sequence: Read sequence

        Returns:
            True if length is in range [min_length, max_length]
        """
        length = len(sequence)
        return self.min_length <= length <= self.max_length

    def process_fastq(self, input_fastq: str, output_fastq: str) -> Dict:
        """
        Filter FASTQ file by read length

        Args:
            input_fastq: Input FASTQ file (.fastq.gz)
            output_fastq: Output FASTQ file (.fastq.gz)

        Returns:
            Statistics dictionary
        """
        # Reset stats
        self.stats = {
            "total_reads": 0,
            "passed_reads": 0,
            "too_short": 0,
            "too_long": 0,
            "length_distribution": defaultdict(int),
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
                quality = infile.readline()

                self.stats["total_reads"] += 1
                length = len(sequence)

                # Update length distribution
                self.stats["length_distribution"][length] += 1

                # Apply length filter
                if self.passes_filter(sequence):
                    # Write to output
                    outfile.write(header)
                    outfile.write(sequence + '\n')
                    outfile.write(separator)
                    outfile.write(quality)
                    self.stats["passed_reads"] += 1
                elif length < self.min_length:
                    self.stats["too_short"] += 1
                else:  # length > max_length
                    self.stats["too_long"] += 1

        # Calculate percentages
        if self.stats["total_reads"] > 0:
            self.stats["percent_passed"] = (
                self.stats["passed_reads"] / self.stats["total_reads"] * 100
            )
            self.stats["percent_too_short"] = (
                self.stats["too_short"] / self.stats["total_reads"] * 100
            )
            self.stats["percent_too_long"] = (
                self.stats["too_long"] / self.stats["total_reads"] * 100
            )
        else:
            self.stats["percent_passed"] = 0
            self.stats["percent_too_short"] = 0
            self.stats["percent_too_long"] = 0

        # Convert defaultdict to regular dict for JSON serialization
        self.stats["length_distribution"] = dict(self.stats["length_distribution"])

        return self.stats

    def get_length_distribution_summary(self) -> Dict:
        """
        Get summary statistics of length distribution

        Returns:
            Dictionary with min, max, median, mode, percentiles
        """
        if not self.stats["length_distribution"]:
            return {}

        lengths = []
        for length, count in self.stats["length_distribution"].items():
            lengths.extend([length] * count)

        lengths.sort()

        summary = {
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "median_length": lengths[len(lengths) // 2] if lengths else 0,
            "mode_length": max(self.stats["length_distribution"],
                             key=self.stats["length_distribution"].get),
            "total_reads": len(lengths),
        }

        # Calculate percentiles
        if lengths:
            summary["p10"] = lengths[int(len(lengths) * 0.1)]
            summary["p25"] = lengths[int(len(lengths) * 0.25)]
            summary["p50"] = lengths[int(len(lengths) * 0.50)]
            summary["p75"] = lengths[int(len(lengths) * 0.75)]
            summary["p90"] = lengths[int(len(lengths) * 0.90)]

        # miRNA-specific statistics
        # Count reads in mature miRNA range (21-23 nt peak)
        mirna_range_count = sum(
            count for length, count in self.stats["length_distribution"].items()
            if 21 <= length <= 23
        )
        summary["reads_in_peak_range_21_23"] = mirna_range_count
        summary["percent_in_peak_range"] = (
            mirna_range_count / len(lengths) * 100 if lengths else 0
        )

        return summary


def filter_by_length_mirna(input_fastq: str,
                           output_fastq: str,
                           min_length: int = 18,
                           max_length: int = 25) -> Dict:
    """
    Main function for length filtering

    Args:
        input_fastq: Input FASTQ file (.fastq.gz)
        output_fastq: Output FASTQ file (.fastq.gz)
        min_length: Minimum read length to keep (default: 18)
        max_length: Maximum read length to keep (default: 25)

    Returns:
        Statistics dictionary with filtering results
    """
    filter_obj = LengthFilter(min_length=min_length, max_length=max_length)
    stats = filter_obj.process_fastq(input_fastq, output_fastq)

    # Add filter parameters to stats
    stats["min_length_filter"] = min_length
    stats["max_length_filter"] = max_length
    stats["input_file"] = input_fastq
    stats["output_file"] = output_fastq

    # Add length distribution summary
    stats["length_summary"] = filter_obj.get_length_distribution_summary()

    return stats


def main_cli():
    """
    Command-line interface for length filtering
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Filter FASTQ reads by length (for miRNA-seq data)"
    )
    parser.add_argument("input", help="Input FASTQ file (.fastq.gz)")
    parser.add_argument("output", help="Output FASTQ file (.fastq.gz)")
    parser.add_argument("--min", type=int, default=18,
                       help="Minimum read length (default: 18)")
    parser.add_argument("--max", type=int, default=25,
                       help="Maximum read length (default: 25)")

    args = parser.parse_args()

    print(f"Filtering reads by length ({args.min}-{args.max} nt)...")
    stats = filter_by_length_mirna(
        args.input,
        args.output,
        min_length=args.min,
        max_length=args.max
    )

    # Print statistics
    print("\n=== Length Filtering Statistics ===")
    print(f"Filter range: {stats['min_length_filter']}-{stats['max_length_filter']} nt")
    print(f"\nTotal reads: {stats['total_reads']:,}")
    print(f"Passed filter: {stats['passed_reads']:,} ({stats['percent_passed']:.1f}%)")
    print(f"Too short (<{args.min} nt): {stats['too_short']:,} ({stats['percent_too_short']:.1f}%)")
    print(f"Too long (>{args.max} nt): {stats['too_long']:,} ({stats['percent_too_long']:.1f}%)")

    # Length distribution summary
    summary = stats["length_summary"]
    print(f"\n=== Length Distribution ===")
    print(f"Min length: {summary['min_length']} nt")
    print(f"Max length: {summary['max_length']} nt")
    print(f"Median length: {summary['median_length']} nt")
    print(f"Mode (most common): {summary['mode_length']} nt")
    print(f"Reads in peak miRNA range (21-23 nt): {summary['reads_in_peak_range_21_23']:,} ({summary['percent_in_peak_range']:.1f}%)")

    print(f"\nOutput saved to: {stats['output_file']}")


if __name__ == "__main__":
    main_cli()
