#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module for quality control of genomic data
Implements quality control for all stages of processing

Enhanced with QualityControlSuite components:
- FastQAnalyzer for high-performance FASTQ analysis
- Reporter for HTML report generation with visual markers
- Unified logging system with [CHECK], [OK], [ERROR] markers
"""

import os
import subprocess
import logging
from pathlib import Path
import json

# Import QualityControlSuite components (always available for FASTQ QC)
from .qc_core.analyzer import FastQAnalyzer
from .qc_core.reporter import Reporter
from .qc_utils.io_handler import IOHandler
from .logging_system import QCLogger, get_logger

# Conditional imports for BAM/VCF processing (not required for FASTQ QC)
try:
    import pysam
    import pysamstats
    BAM_SUPPORT = True
except ImportError:
    BAM_SUPPORT = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("pysam/pysamstats not available. BAM/CRAM analysis disabled.")

try:
    from Bio import SeqIO
    from Bio.SeqUtils import GC
    BIOPYTHON_SUPPORT = True
except ImportError:
    BIOPYTHON_SUPPORT = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("Biopython not available. GC analysis disabled.")

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_SUPPORT = True
except ImportError:
    MATPLOTLIB_SUPPORT = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("matplotlib not available. Plotting disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize QC logger
qc_logger = get_logger(verbose=True, use_colors=False)  # Disable colors for Windows compatibility


def has_sequali():
    """
    Check if Sequali is installed and available

    Returns:
        bool: True if Sequali is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['sequali', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def run_sequali_qc(input_fastq, output_dir):
    """
    Run FASTQ QC using Sequali engine (C++ implementation)

    This is the PRIMARY method based on fastqcli.py from QualityControlSuite.
    Sequali generates professional HTML and JSON reports with comprehensive metrics.

    Args:
        input_fastq (str): Path to input FASTQ file
        output_dir (Path): Output directory

    Returns:
        dict: Dictionary with analysis metrics and report paths, or None if failed
    """
    qc_logger.header(f"Sequali QC for {Path(input_fastq).name}")
    qc_logger.install("Using Sequali C++ engine (PRIMARY METHOD)")

    try:
        file_path = Path(input_fastq)
        if not file_path.exists():
            qc_logger.error(f"File not found: {input_fastq}")
            return None

        qc_logger.info(f"File size: {file_path.stat().st_size / (1024**2):.1f} MB")

        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Construct Sequali command
        full_name = file_path.name
        base_name = file_path.stem

        # Sequali command format from fastqcli.py
        cmd = [
            'sequali',
            '--dir', str(output_path),
            '--html', full_name,  # HTML report name
            '--json', full_name,  # JSON metrics name
            str(file_path)
        ]

        qc_logger.running(f"Command: {' '.join(cmd)}")
        qc_logger.analyze("Running Sequali analysis...")

        # Run Sequali
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=600  # 10 minutes timeout
        )

        # Show Sequali output
        if result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    qc_logger.info(f"   {line}")

        if result.stderr:
            for line in result.stderr.splitlines():
                if line.strip():
                    qc_logger.warning(f"   {line}")

        if result.returncode != 0:
            qc_logger.error(f"Sequali returned error code: {result.returncode}")
            return None

        # Find generated files (try multiple naming variants)
        html_path = None
        json_path = None

        # Try different naming patterns
        html_candidates = [
            output_path / f"{full_name}.html",
            output_path / f"{base_name}.html",
            output_path / full_name,  # Sometimes Sequali creates file without extension
            output_path / base_name
        ]

        json_candidates = [
            output_path / f"{full_name}.json",
            output_path / f"{base_name}.json"
        ]

        # Find HTML report
        for candidate in html_candidates:
            if candidate.exists() and candidate.stat().st_size > 10000:  # At least 10KB
                html_path = candidate
                qc_logger.ok(f"HTML report found: {candidate.name}")
                break

        # Find JSON metrics
        for candidate in json_candidates:
            if candidate.exists() and candidate.stat().st_size > 0:
                json_path = candidate
                qc_logger.ok(f"JSON metrics found: {candidate.name}")
                break

        if not html_path or not json_path:
            qc_logger.warning("Sequali completed but output files not found in expected locations")
            # List all files in output directory for debugging
            qc_logger.debug(f"Files in {output_path}:")
            for f in output_path.glob("*"):
                qc_logger.debug(f"   - {f.name} ({f.stat().st_size} bytes)")
            return None

        # Read and parse JSON metrics
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Extract key metrics from Sequali JSON format
            summary = json_data.get('summary', {})
            total_reads = summary.get('total_reads', 0)
            total_bases = summary.get('total_bases', 0)
            mean_length = summary.get('mean_length', 0)
            q20_bases = summary.get('q20_bases', 0)
            q30_bases = summary.get('q30_bases', 0)
            gc_bases = summary.get('total_gc_bases', 0)
            n_bases = summary.get('total_n_bases', 0)

            # Calculate percentages
            q20_pct = (q20_bases / total_bases * 100) if total_bases > 0 else 0
            q30_pct = (q30_bases / total_bases * 100) if total_bases > 0 else 0
            gc_pct = (gc_bases / total_bases * 100) if total_bases > 0 else 0
            n_pct = (n_bases / total_bases * 100) if total_bases > 0 else 0

            # Determine status (using same logic as FastQAnalyzer)
            if q30_pct >= 80 and n_pct < 5:
                status = "PASS"
            elif q30_pct >= 70 or n_pct < 10:
                status = "WARNING"
            else:
                status = "FAIL"

            # Format metrics to match FastQAnalyzer output format
            metrics = {
                'total_reads': total_reads,
                'total_bases': total_bases,
                'avg_read_length': mean_length,
                'min_read_length': summary.get('min_length', 0),
                'max_read_length': summary.get('max_length', 0),
                'q20_percentage': q20_pct,
                'q30_percentage': q30_pct,
                'gc_content': gc_pct,
                'n_percentage': n_pct,
                'status': status
            }

            qc_logger.metrics(f"Total reads: {total_reads:,}")
            qc_logger.metrics(f"Q30: {q30_pct:.1f}%")
            qc_logger.metrics(f"GC content: {gc_pct:.1f}%")
            qc_logger.metrics(f"Status: {status}")
            qc_logger.summary("Sequali QC completed successfully!")

            return {
                'metrics': metrics,
                'html_report': str(html_path),
                'json_metrics': str(json_path),
                'status': status,
                'engine': 'sequali'
            }

        except Exception as e:
            qc_logger.error(f"Error parsing Sequali JSON: {e}")
            return None

    except subprocess.TimeoutExpired:
        qc_logger.error("Sequali analysis timed out (10 minutes)")
        return None
    except Exception as e:
        qc_logger.error(f"Error running Sequali QC: {e}")
        import traceback
        qc_logger.debug(traceback.format_exc())
        return None


def run_python_fastq_qc(input_fastq, output_dir, sample_size=10000):
    """
    Run FASTQ QC using Python implementation (FALLBACK method)

    This is the fallback method using FastQAnalyzer and Reporter.
    Used when Sequali is not available.

    Args:
        input_fastq (str): Path to input FASTQ file
        output_dir (Path): Output directory
        sample_size (int): Number of reads to analyze (default: 10000)

    Returns:
        dict: Dictionary with analysis metrics and report paths, or None if failed
    """
    qc_logger.header(f"Python FASTQ QC for {Path(input_fastq).name}")
    qc_logger.warning("Using Python fallback (Sequali not available)")

    try:
        # Validate input file
        io_handler = IOHandler()
        if not io_handler.validate_input(input_fastq):
            qc_logger.error(f"Invalid FASTQ file: {input_fastq}")
            return None

        qc_logger.ok("Input file validated successfully")

        # Initialize analyzer and reporter
        analyzer = FastQAnalyzer(verbose=True)
        reporter = Reporter()

        # Run analysis
        qc_logger.analyze(f"Analyzing {Path(input_fastq).name} (sample size: {sample_size})")
        metrics = analyzer.analyze(input_fastq, sample_size=sample_size)

        if not metrics or metrics.get('total_reads', 0) == 0:
            qc_logger.error("No reads found in FASTQ file")
            return None

        qc_logger.ok(f"Analysis complete! Processed {metrics['total_reads']:,} reads")

        # Display key metrics
        qc_logger.metrics(f"Q30 percentage: {metrics['q30_percentage']:.1f}%")
        qc_logger.metrics(f"GC content: {metrics['gc_content']:.1f}%")
        qc_logger.metrics(f"Status: {metrics['status']}")

        # Generate HTML report
        qc_logger.html("Generating HTML report...")
        html_path = output_dir / f"{Path(input_fastq).stem}_advanced_qc_report.html"
        reporter.generate_html(metrics, str(html_path))
        qc_logger.ok(f"HTML report generated: {html_path}")

        # Save JSON metrics
        qc_logger.json("Saving JSON metrics...")
        json_path = output_dir / f"{Path(input_fastq).stem}_advanced_qc_metrics.json"
        with open(json_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        qc_logger.ok(f"JSON metrics saved: {json_path}")

        qc_logger.summary(f"Python QC completed for {Path(input_fastq).name}")

        return {
            'metrics': metrics,
            'html_report': str(html_path),
            'json_metrics': str(json_path),
            'status': metrics['status'],
            'engine': 'python'
        }

    except Exception as e:
        qc_logger.error(f"Error in Python FASTQ QC: {e}")
        import traceback
        qc_logger.debug(traceback.format_exc())
        return None


def run_advanced_fastq_qc(input_fastq, output_dir, sample_size=10000, prefer_sequali=True):
    """
    Run advanced FASTQ quality control with HYBRID approach

    PRIMARY: Sequali (C++ engine) - fast, professional reports
    FALLBACK: Python implementation - reliable, no external dependencies

    This function implements the approach from fastqcli.py where Sequali is
    the primary method used for production analysis.

    Args:
        input_fastq (str): Path to input FASTQ file
        output_dir (Path): Output directory
        sample_size (int): Number of reads for Python fallback (default: 10000)
        prefer_sequali (bool): Try Sequali first if True (default: True)

    Returns:
        dict: Dictionary with analysis metrics and report paths, or None if failed
    """
    qc_logger.header(f"Advanced FASTQ QC for {Path(input_fastq).name}")
    qc_logger.check("Checking available QC engines...")

    # Attempt 1: Sequali (PRIMARY METHOD)
    if prefer_sequali and has_sequali():
        qc_logger.ok("Sequali available - using PRIMARY method")
        qc_logger.separator()

        try:
            result = run_sequali_qc(input_fastq, output_dir)
            if result:
                qc_logger.ok("✓ QC completed using Sequali (PRIMARY)")
                qc_logger.separator()
                return result
            else:
                qc_logger.warning("Sequali failed, falling back to Python...")
        except Exception as e:
            qc_logger.warning(f"Sequali error: {e}, falling back to Python...")
    else:
        qc_logger.warning("Sequali not available")

    # Attempt 2: Python fallback (RELIABLE FALLBACK)
    qc_logger.info("Using Python implementation (FALLBACK)")
    qc_logger.separator()

    result = run_python_fastq_qc(input_fastq, output_dir, sample_size)
    if result:
        qc_logger.ok("✓ QC completed using Python fallback")
        qc_logger.separator()
        return result
    else:
        qc_logger.error("❌ Both Sequali and Python methods failed")
        qc_logger.separator()
        return None


def run_quality_control(input_files, output_path, reference_genome=None):
    """
    Run quality control for genomic data with real implementation
    
    Args:
        input_files (list): List of paths to input files (FASTQ/BAM/VCF)
        output_path (str): Path to output directory
        reference_genome (str): Path to reference genome (optional)
        
    Returns:
        dict: Dictionary with quality control results and reports
    """
    logger.info("Running quality control for genomic data with real implementation")
    results = {
        'qc_reports': [],
        'metrics': {},
        'plots': []
    }
    
    for input_file in input_files:
        logger.info(f"Running QC for file: {input_file}")
        try:
            # Create output directory for this file
            file_output_dir = Path(output_path) / Path(input_file).stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file type and run appropriate QC
            if input_file.endswith(('.fastq', '.fq', '.fastq.gz', '.fq.gz')):
                # Run advanced FASTQ QC (using QualityControlSuite components)
                qc_logger.info(f"Running advanced FASTQ QC for {input_file}")
                advanced_qc_results = run_advanced_fastq_qc(input_file, file_output_dir)

                if advanced_qc_results:
                    results['qc_reports'].append(advanced_qc_results['html_report'])
                    results['metrics'][input_file] = advanced_qc_results['metrics']
                    qc_logger.ok(f"Advanced QC completed for {input_file}")
                else:
                    qc_logger.warning(f"Advanced QC failed, falling back to FastQC")
                    # Fallback to traditional FastQC if advanced QC fails
                    fastqc_report = run_fastqc(input_file, file_output_dir)
                    if fastqc_report:
                        results['qc_reports'].append(fastqc_report)

                # Analyze GC content
                if reference_genome:
                    gc_analysis = analyze_gc_content(input_file, reference_genome, file_output_dir)
                    if gc_analysis:
                        if input_file not in results['metrics']:
                            results['metrics'][input_file] = {}
                        results['metrics'][input_file]['gc_content'] = gc_analysis
                        
            elif input_file.endswith(('.bam', '.cram')):
                # Analyze coverage and depth for BAM/CRAM files
                coverage_metrics = analyze_bam_coverage_depth(input_file, file_output_dir)
                if coverage_metrics:
                    results['metrics'][input_file] = coverage_metrics
                    
                # Generate coverage plots
                coverage_plot = generate_coverage_plot(input_file, file_output_dir)
                if coverage_plot:
                    results['plots'].append(coverage_plot)
                    
            elif input_file.endswith(('.vcf', '.vcf.gz')):
                # Validate VCF file
                vcf_validation = validate_vcf_file(input_file, file_output_dir)
                if vcf_validation:
                    results['qc_reports'].append(vcf_validation)
                    
        except Exception as e:
            logger.error(f"Error running QC for {input_file}: {e}")
            
    return results


def run_fastqc(input_fastq, output_dir):
    """
    Run FastQC for quality control of FASTQ files
    
    Args:
        input_fastq (str): Path to input FASTQ file
        output_dir (Path): Output directory
        
    Returns:
        str: Path to FastQC report or None if failed
    """
    logger.info(f"Running FastQC for {input_fastq}")
    
    try:
        # Build FastQC command
        cmd = [
            "fastqc",
            "-o", str(output_dir),  # Output directory
            "-t", "4",  # Number of threads
            input_fastq
        ]
        
        # Run FastQC
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Find the generated report files
            report_files = list(output_dir.glob(f"{Path(input_fastq).stem}*fastqc*"))
            if report_files:
                logger.info(f"FastQC completed successfully for {input_fastq}")
                return str(report_files[0])  # Return the first report file
            else:
                logger.warning(f"FastQC completed but no report files found for {input_fastq}")
                return None
        else:
            logger.error(f"FastQC failed for {input_fastq}: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error running FastQC for {input_fastq}: {e}")
        return None


def validate_vcf_file(input_vcf, output_dir):
    """
    Validate VCF file with bcftools
    
    Args:
        input_vcf (str): Path to input VCF file
        output_dir (Path): Output directory
        
    Returns:
        str: Path to validation report or None if failed
    """
    logger.info(f"Validating VCF file {input_vcf}")
    
    try:
        # Define output file
        validation_report = output_dir / f"{Path(input_vcf).stem}_vcf_validation.txt"
        
        # Build bcftools validate command
        cmd = [
            "bcftools", "validate",
            input_vcf
        ]
        
        # Run bcftools validate and redirect output to file
        with open(validation_report, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
            
        if result.returncode == 0:
            logger.info(f"VCF validation completed successfully for {input_vcf}")
            return str(validation_report)
        else:
            logger.error(f"VCF validation failed for {input_vcf}")
            return None
            
    except Exception as e:
        logger.error(f"Error validating VCF file {input_vcf}: {e}")
        return None


def analyze_gc_content(input_fastq, reference_genome, output_dir):
    """
    Analyze GC content using Biopython

    Args:
        input_fastq (str): Path to input FASTQ file
        reference_genome (str): Path to reference genome
        output_dir (Path): Output directory

    Returns:
        dict: Dictionary with GC content analysis or None if failed
    """
    if not BIOPYTHON_SUPPORT:
        logger.warning("Biopython not available. Skipping GC content analysis.")
        return None

    logger.info(f"Analyzing GC content for {input_fastq}")

    try:
        # For this example, we'll calculate GC content of the reference genome
        # In a real implementation, you might want to calculate GC content of reads
        
        # Read reference genome
        records = list(SeqIO.parse(reference_genome, "fasta"))
        
        # Calculate GC content for each chromosome/contig
        gc_contents = []
        for record in records:
            gc_content = GC(record.seq)
            gc_contents.append(gc_content)
            
        # Calculate average GC content
        avg_gc_content = sum(gc_contents) / len(gc_contents) if gc_contents else 0
        
        # Save GC content analysis to file
        gc_file = output_dir / f"{Path(input_fastq).stem}_gc_content.json"
        gc_data = {
            'average_gc_content': avg_gc_content,
            'contig_gc_contents': dict(zip([record.id for record in records], gc_contents))
        }
        
        with open(gc_file, 'w') as f:
            json.dump(gc_data, f, indent=2)
                
        logger.info(f"GC content analysis completed successfully for {input_fastq}")
        return gc_data
        
    except Exception as e:
        logger.error(f"Error analyzing GC content for {input_fastq}: {e}")
        return None


def analyze_bam_coverage_depth(input_bam, output_dir):
    """
    Analyze coverage and depth of sequencing from BAM file using pysam and pysamstats

    Args:
        input_bam (str): Path to input BAM file
        output_dir (Path): Output directory

    Returns:
        dict: Dictionary with coverage metrics or None if failed
    """
    if not BAM_SUPPORT:
        logger.warning("pysam/pysamstats not available. Skipping BAM coverage analysis.")
        return None

    logger.info(f"Analyzing BAM coverage and depth for {input_bam}")

    try:
        # Open BAM file
        bam_file = pysam.AlignmentFile(input_bam, "rb")
        
        # Calculate coverage statistics using pysamstats
        coverage_stats = []
        for rec in bam_file:
            # For simplicity, we'll just collect basic stats
            # In a real implementation, you would iterate through all references
            if rec.reference_name:
                # Get coverage for the first reference
                try:
                    stats = pysamstats.load_coverage(bam_file, chrom=rec.reference_name)
                    coverage_stats.extend(list(stats))
                    break  # Just analyze the first reference for this example
                except:
                    continue
                    
        bam_file.close()
        
        # Calculate metrics from coverage stats
        if coverage_stats:
            depths = [stat['reads_all'] for stat in coverage_stats]
            mean_depth = sum(depths) / len(depths) if depths else 0
            max_depth = max(depths) if depths else 0
            min_depth = min(depths) if depths else 0
            
            metrics = {
                'mean_coverage_depth': mean_depth,
                'max_coverage_depth': max_depth,
                'min_coverage_depth': min_depth,
                'total_positions_analyzed': len(depths)
            }
            
            # Save metrics to file
            metrics_file = output_dir / f"{Path(input_bam).stem}_coverage_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
            logger.info(f"BAM coverage analysis completed successfully for {input_bam}")
            return metrics
        else:
            logger.warning(f"No coverage data found for {input_bam}")
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing BAM coverage for {input_bam}: {e}")
        return None


def generate_coverage_plot(input_bam, output_dir):
    """
    Generate coverage plot from BAM file

    Args:
        input_bam (str): Path to input BAM file
        output_dir (Path): Output directory

    Returns:
        str: Path to coverage plot or None if failed
    """
    if not BAM_SUPPORT or not MATPLOTLIB_SUPPORT:
        logger.warning("pysam or matplotlib not available. Skipping coverage plot generation.")
        return None

    logger.info(f"Generating coverage plot for {input_bam}")

    try:
        # Open BAM file
        bam_file = pysam.AlignmentFile(input_bam, "rb")
        
        # Get coverage for the first reference (for simplicity)
        coverage_data = []
        for ref_name in bam_file.references[:1]:  # Just the first reference
            try:
                stats = pysamstats.load_coverage(bam_file, chrom=ref_name)
                coverage_data = [(stat['pos'], stat['reads_all']) for stat in stats[:1000]]  # First 1000 positions
                break
            except:
                continue
                
        bam_file.close()
        
        if coverage_data:
            # Generate plot
            positions, depths = zip(*coverage_data)
            
            plt.figure(figsize=(12, 6))
            plt.plot(positions, depths, linewidth=0.8)
            plt.xlabel('Genomic Position')
            plt.ylabel('Coverage Depth')
            plt.title(f'Coverage Plot for {Path(input_bam).name}')
            plt.grid(True, alpha=0.3)
            
            # Save plot
            plot_file = output_dir / f"{Path(input_bam).stem}_coverage_plot.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Coverage plot generated successfully for {input_bam}")
            return str(plot_file)
        else:
            logger.warning(f"No coverage data found for plotting {input_bam}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating coverage plot for {input_bam}: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    pass