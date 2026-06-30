"""
Unified miRNA-seq Preprocessing Pipeline

Combines adapter trimming and length filtering into a single pipeline.

Pipeline:
    Raw FASTQ → Adapter Trimming → Length Filtering → Processed FASTQ

TZ Requirements:
    - "Контроль качества и обрезку адаптеров" (adapter trimming)
    - "Фильтрацию по длине фрагментов (18-25 нуклеотидов)" (length filtering)
"""

import os
from pathlib import Path
from typing import Dict, Optional
import json

from .adapter_trimming import trim_adapters_mirna, STANDARD_ADAPTERS
from .length_filtering import filter_by_length_mirna


class MiRNAPreprocessor:
    """
    Unified preprocessing pipeline for miRNA-seq data
    """

    def __init__(self,
                 output_dir: str,
                 adapter: Optional[str] = None,
                 min_length: int = 18,
                 max_length: int = 25,
                 adapter_error_rate: float = 0.1,
                 keep_intermediate: bool = True):
        """
        Initialize preprocessing pipeline

        Args:
            output_dir: Output directory for processed files
            adapter: Adapter sequence (None = auto-detect)
            min_length: Minimum read length after filtering
            max_length: Maximum read length after filtering
            adapter_error_rate: Error rate for adapter matching
            keep_intermediate: Keep intermediate files (trimmed.fastq.gz)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.adapter = adapter
        self.min_length = min_length
        self.max_length = max_length
        self.adapter_error_rate = adapter_error_rate
        self.keep_intermediate = keep_intermediate

        self.pipeline_stats = {}

    def process(self, input_fastq: str, sample_name: Optional[str] = None) -> Dict:
        """
        Run complete preprocessing pipeline

        Args:
            input_fastq: Input FASTQ file (.fastq.gz)
            sample_name: Sample name (if None, use filename)

        Returns:
            Dictionary with pipeline statistics and output files
        """
        input_path = Path(input_fastq)

        if sample_name is None:
            sample_name = input_path.stem.replace('.fastq', '').replace('.fq', '')

        print(f"\n{'='*60}")
        print(f"miRNA-seq Preprocessing Pipeline")
        print(f"Sample: {sample_name}")
        print(f"Input: {input_fastq}")
        print(f"{'='*60}\n")

        # Define intermediate and final output files
        trimmed_fastq = self.output_dir / f"{sample_name}_trimmed.fastq.gz"
        filtered_fastq = self.output_dir / f"{sample_name}_filtered.fastq.gz"

        # Step 1: Adapter Trimming
        print("Step 1/2: Adapter Trimming...")
        trimming_stats = trim_adapters_mirna(
            input_fastq=str(input_fastq),
            output_fastq=str(trimmed_fastq),
            adapter=self.adapter,
            min_length=self.min_length,  # Pre-filter very short reads
            error_rate=self.adapter_error_rate,
            auto_detect=(self.adapter is None)
        )
        print(f"  ✓ Reads processed: {trimming_stats['reads_processed']:,}")
        print(f"  ✓ Reads with adapters: {trimming_stats['reads_with_adapters']:,} ({trimming_stats['percent_with_adapters']:.1f}%)")
        print(f"  ✓ Bases removed: {trimming_stats['bases_removed']:,}")
        print(f"  ✓ Reads kept: {trimming_stats['reads_kept']:,}")

        # Step 2: Length Filtering
        print("\nStep 2/2: Length Filtering (18-25 nt)...")
        filtering_stats = filter_by_length_mirna(
            input_fastq=str(trimmed_fastq),
            output_fastq=str(filtered_fastq),
            min_length=self.min_length,
            max_length=self.max_length
        )
        print(f"  ✓ Reads processed: {filtering_stats['total_reads']:,}")
        print(f"  ✓ Passed filter: {filtering_stats['passed_reads']:,} ({filtering_stats['percent_passed']:.1f}%)")
        print(f"  ✓ Too short: {filtering_stats['too_short']:,}")
        print(f"  ✓ Too long: {filtering_stats['too_long']:,}")

        # Remove intermediate file if not needed
        if not self.keep_intermediate:
            trimmed_fastq.unlink()
            print(f"\n  ✓ Removed intermediate file: {trimmed_fastq}")

        # Compile pipeline summary
        pipeline_summary = {
            "sample_name": sample_name,
            "input_file": str(input_fastq),
            "output_file": str(filtered_fastq),
            "intermediate_file": str(trimmed_fastq) if self.keep_intermediate else None,
            "pipeline_steps": ["adapter_trimming", "length_filtering"],
            "adapter_trimming": trimming_stats,
            "length_filtering": filtering_stats,
            "final_stats": {
                "input_reads": trimming_stats["reads_processed"],
                "output_reads": filtering_stats["passed_reads"],
                "percent_reads_kept": (
                    filtering_stats["passed_reads"] / trimming_stats["reads_processed"] * 100
                    if trimming_stats["reads_processed"] > 0 else 0
                ),
                "adapter_detected": trimming_stats["adapter_sequence"],
                "length_range": f"{self.min_length}-{self.max_length}",
            }
        }

        # Save statistics to JSON
        stats_file = self.output_dir / f"{sample_name}_preprocessing_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(pipeline_summary, f, indent=2)
        print(f"\n  ✓ Statistics saved to: {stats_file}")

        # Print final summary
        print(f"\n{'='*60}")
        print("Pipeline Summary:")
        print(f"  Input reads: {pipeline_summary['final_stats']['input_reads']:,}")
        print(f"  Output reads: {pipeline_summary['final_stats']['output_reads']:,}")
        print(f"  Retention rate: {pipeline_summary['final_stats']['percent_reads_kept']:.1f}%")
        print(f"  Adapter detected: {pipeline_summary['final_stats']['adapter_detected'][:20]}...")
        print(f"  Length filter: {pipeline_summary['final_stats']['length_range']} nt")
        print(f"\n  Output file: {filtered_fastq}")
        print(f"{'='*60}\n")

        self.pipeline_stats = pipeline_summary
        return pipeline_summary


def preprocess_mirna_fastq(input_fastq: str,
                           output_dir: str,
                           sample_name: Optional[str] = None,
                           adapter: Optional[str] = None,
                           min_length: int = 18,
                           max_length: int = 25,
                           keep_intermediate: bool = False) -> Dict:
    """
    Convenience function for miRNA-seq preprocessing

    Args:
        input_fastq: Input FASTQ file
        output_dir: Output directory
        sample_name: Sample name (optional)
        adapter: Adapter sequence (None = auto-detect)
        min_length: Minimum read length
        max_length: Maximum read length
        keep_intermediate: Keep intermediate files

    Returns:
        Pipeline statistics dictionary
    """
    preprocessor = MiRNAPreprocessor(
        output_dir=output_dir,
        adapter=adapter,
        min_length=min_length,
        max_length=max_length,
        keep_intermediate=keep_intermediate
    )

    return preprocessor.process(input_fastq, sample_name)


def main_cli():
    """
    Command-line interface for miRNA preprocessing pipeline
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="miRNA-seq preprocessing pipeline (adapter trimming + length filtering)"
    )
    parser.add_argument("input", help="Input FASTQ file (.fastq.gz)")
    parser.add_argument("-o", "--output-dir", required=True,
                       help="Output directory")
    parser.add_argument("-n", "--name", help="Sample name (default: from filename)")
    parser.add_argument("-a", "--adapter", help="Adapter sequence (auto-detect if not provided)")
    parser.add_argument("--min", type=int, default=18,
                       help="Minimum read length (default: 18)")
    parser.add_argument("--max", type=int, default=25,
                       help="Maximum read length (default: 25)")
    parser.add_argument("--keep-intermediate", action="store_true",
                       help="Keep intermediate files (trimmed.fastq.gz)")

    args = parser.parse_args()

    # Run pipeline
    stats = preprocess_mirna_fastq(
        input_fastq=args.input,
        output_dir=args.output_dir,
        sample_name=args.name,
        adapter=args.adapter,
        min_length=args.min,
        max_length=args.max,
        keep_intermediate=args.keep_intermediate
    )

    print("\n✓ Pipeline completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main_cli())
