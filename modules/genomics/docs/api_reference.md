# API Reference for Genomics Module

## Overview

The genomics module provides comprehensive tools for processing various types of genomic data including FASTQ, SAM, BAM/CRAM, and VCF files. Each component is designed to work independently or as part of a complete pipeline.

## Table of Contents

1. [FASTQ Processor](#fastq-processor)
2. [SAM Processor](#sam-processor)
3. [BAM/CRAM Processor](#bamcram-processor)
4. [VCF Processor](#vcf-processor)
5. [Filter and Validator](#filter-and-validator)
6. [Quality Control](#quality-control)

---

## FASTQ Processor

### Function: `process_fastq_files`

Processes FASTQ files with real implementation including preprocessing, alignment, and BAM file generation.

#### Parameters

- `fastq_files` (list): List of paths to FASTQ files
- `output_path` (str): Path to output directory
- `reference_genome` (str, optional): Path to reference genome

#### Returns

- `list`: List of processed BAM files

#### Example Usage

```python
from modules.genomics.fastq_processor import process_fastq_files

fastq_files = ["sample1.fastq", "sample2.fastq"]
output_path = "output/fastq_processing"
reference_genome = "reference/hg38.fa"

bam_files = process_fastq_files(fastq_files, output_path, reference_genome)
print(f"Processed {len(bam_files)} BAM files")
```

---

## SAM Processor

### Function: `process_sam_files`

Processes SAM files by converting them to BAM format, sorting, and indexing.

#### Parameters

- `sam_files` (list): List of paths to SAM files
- `output_path` (str): Path to output directory

#### Returns

- `list`: List of processed BAM files

#### Example Usage

```python
from modules.genomics.sam_processor import process_sam_files

sam_files = ["alignment1.sam", "alignment2.sam"]
output_path = "output/sam_processing"

bam_files = process_sam_files(sam_files, output_path)
print(f"Converted {len(bam_files)} SAM files to BAM")
```

---

## BAM/CRAM Processor

### Function: `process_bam_files`

Processes BAM/CRAM files by extracting variants using bcftools or GATK.

#### Parameters

- `bam_files` (list): List of paths to BAM/CRAM files
- `output_path` (str): Path to output directory
- `reference_genome` (str, optional): Path to reference genome

#### Returns

- `list`: List of processed VCF files

#### Example Usage

```python
from modules.genomics.bam_processor import process_bam_files

bam_files = ["sample1.bam", "sample2.bam"]
output_path = "output/bam_processing"
reference_genome = "reference/hg38.fa"

vcf_files = process_bam_files(bam_files, output_path, reference_genome)
print(f"Called variants for {len(vcf_files)} BAM files")
```

---

## VCF Processor

### Function: `process_vcf_files`

Processes VCF files by normalizing, compressing, indexing, and validating.

#### Parameters

- `vcf_files` (list): List of paths to VCF files
- `output_path` (str): Path to output directory
- `reference_genome` (str, optional): Path to reference genome

#### Returns

- `list`: List of processed VCF files (.vcf.gz format)

#### Example Usage

```python
from modules.genomics.vcf_processor import process_vcf_files

vcf_files = ["variants1.vcf", "variants2.vcf"]
output_path = "output/vcf_processing"
reference_genome = "reference/hg38.fa"

processed_vcf_files = process_vcf_files(vcf_files, output_path, reference_genome)
print(f"Processed {len(processed_vcf_files)} VCF files")
```

---

## Filter and Validator

### Function: `filter_and_validate_data`

Filters and validates genomic data based on quality, depth, and allele frequency.

#### Parameters

- `input_files` (list): List of paths to input files (VCF/BAM/FASTQ)
- `output_path` (str): Path to output directory
- `reference_genome` (str, optional): Path to reference genome

#### Returns

- `dict`: Dictionary with filtering results and metrics

#### Example Usage

```python
from modules.genomics.filter_validator import filter_and_validate_data

input_files = ["sample1.vcf", "sample2.bam"]
output_path = "output/filter_validation"
reference_genome = "reference/hg38.fa"

results = filter_and_validate_data(input_files, output_path, reference_genome)
print(f"Filtered and validated {len(results['filtered_files'])} files")
```

---

## Quality Control

### Function: `run_quality_control`

Runs quality control for genomic data including FastQC, coverage analysis, and GC content analysis.

#### Parameters

- `input_files` (list): List of paths to input files (FASTQ/BAM/VCF)
- `output_path` (str): Path to output directory
- `reference_genome` (str, optional): Path to reference genome

#### Returns

- `dict`: Dictionary with quality control results and reports

#### Example Usage

```python
from modules.genomics.quality_control import run_quality_control

input_files = ["sample1.fastq", "sample2.bam"]
output_path = "output/quality_control"
reference_genome = "reference/hg38.fa"

qc_results = run_quality_control(input_files, output_path, reference_genome)
print(f"Generated {len(qc_results['qc_reports'])} QC reports")
```

---

## Configuration Parameters

### General Parameters

- `input_path`: Path to input data directory
- `output_path`: Path to output data directory
- `reference_genome`: Path to reference genome file
- `threads`: Number of threads to use for parallel processing (default: 4)

### Tool-specific Parameters

#### fastp Parameters
- `min_length`: Minimum read length after trimming (default: 50)
- `quality_threshold`: Minimum quality threshold for base calling (default: 20)
- `adapter_sequence`: Adapter sequence to trim (default: auto-detect)

#### BWA-MEM2/Minimap2 Parameters
- `match_score`: Score for a match (default: 1)
- `mismatch_penalty`: Penalty for a mismatch (default: 4)
- `gap_open_penalty`: Penalty for opening a gap (default: 6)
- `gap_extension_penalty`: Penalty for extending a gap (default: 1)

#### bcftools Parameters
- `min_allele_frequency`: Minimum allele frequency for variant calling (default: 0.05)
- `min_mapping_quality`: Minimum mapping quality for variant calling (default: 30)
- `min_base_quality`: Minimum base quality for variant calling (default: 20)

---

## Data Formats and Output Files

### Input Formats Supported
- FASTQ (.fastq, .fq, .fastq.gz, .fq.gz)
- SAM (.sam)
- BAM (.bam)
- CRAM (.cram)
- VCF (.vcf, .vcf.gz)

### Output Formats Generated
- BAM (.bam)
- VCF (.vcf, .vcf.gz)
- Indexed files (.bai, .csi, .tbi)
- Quality control reports (.html, .txt, .json)
- Metrics files (.json, .txt)
- Visualization plots (.png)

### Directory Structure
```
output/
├── fastq_processing/
│   ├── sample1/
│   │   ├── sample1_clean.fastq
│   │   ├── sample1_fastp.html
│   │   ├── sample1_fastp.json
│   │   ├── sample1.bam
│   │   ├── sample1_sorted.bam
│   │   └── sample1_sorted.bam.bai
│   └── sample2/
├── sam_processing/
├── bam_processing/
├── vcf_processing/
├── filter_validation/
├── quality_control/
└── logs/