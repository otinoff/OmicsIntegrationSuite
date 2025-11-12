# miRNA-seq Quality Control Module

**Version:** 1.0.0
**Date:** 2025-11-12
**Status:** ✅ Production Ready

---

## Overview

Complete miRNA-seq quality control pipeline implementing ТЗ requirements (Sections 1.2.4, 1.3.4):

- ✅ Adapter trimming and quality filtering
- ✅ Length filtering (18-25 nt per miRNA specifications)
- ✅ Alignment to miRBase reference database
- ✅ Read counting per miRNA
- ✅ ID validation against miRBase
- ✅ HTML report generation
- ✅ Metadata tracking

**Architecture:** Identical to genomics module (per user requirements)

---

## Installation

### Requirements

```bash
# Core dependencies (required)
pip install biopython jinja2 pyyaml

# Optional (for speed boost)
conda install -c bioconda cutadapt bowtie
```

**Note:** Pipeline works without optional dependencies using pure Python fallback methods.

### miRBase Reference

Download miRBase reference FASTA (mature sequences):

```bash
# Option 1: NCBI (recommended)
wget ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/miRNA/mature.fa.gz
gunzip mature.fa.gz

# Option 2: GitHub mirror
git clone https://github.com/miRBase/mirbase.git

# Extract human miRNAs only
grep -A1 "^>hsa-" mature.fa > mirbase_hsa.fa
```

---

## Quick Start

### Command Line Usage

```bash
python -m modules.mirna.quality_control \
    --fastq sample.fastq.gz \
    --reference mirbase_hsa.fa \
    --output results/ \
    --sample-id sample_001
```

### Python API Usage

```python
from modules.mirna.quality_control import run_mirna_qc

# Run complete pipeline
result = run_mirna_qc(
    input_fastq='sample.fastq.gz',
    reference_fasta='mirbase_hsa.fa',
    output_dir='results/',
    sample_id='sample_001',
    min_length=18,  # ТЗ requirement
    max_length=25,  # ТЗ requirement
    validate_ids=True
)

# Access results
print(f"Counts TSV: {result['counts_tsv']}")
print(f"Alignment rate: {result['pipeline_metadata']['stages']['alignment']['alignment_rate']:.1f}%")
```

---

## Pipeline Stages

### Stage 1: Adapter Trimming & Filtering

**Module:** `qc_core/trimmer.py`

**Methods:**
- **PRIMARY:** cutadapt (fast C tool)
- **FALLBACK:** BioPython (pure Python)

**Parameters:**
- Illumina TruSeq adapter: `AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC`
- Quality threshold: Q20
- Length filter: 18-25 nt (ТЗ requirement)

**Output:** `{sample_id}_trimmed.fastq`

```python
from modules.mirna.qc_core.trimmer import trim_adapters

result = trim_adapters(
    input_fastq='raw.fastq',
    output_dir='output/',
    min_length=18,
    max_length=25
)
# Returns: {'trimmed_fastq': path, 'total_reads': int, 'filtered_reads': int, 'percent_kept': float}
```

---

### Stage 2: Alignment to miRBase

**Module:** `qc_core/aligner.py`

**Methods:**
- **PRIMARY:** bowtie (fast C tool)
- **FALLBACK:** Pure Python exact/near-exact matching

**Parameters:**
- Mismatches allowed: 1
- Multi-threading: 4 threads
- Output format: SAM

**Output:** `{sample_id}_aligned.sam`

```python
from modules.mirna.qc_core.aligner import align_to_mirbase

result = align_to_mirbase(
    input_fastq='trimmed.fastq',
    reference_fasta='mirbase_hsa.fa',
    output_dir='output/'
)
# Returns: {'sam_file': path, 'aligned_reads': int, 'alignment_rate': float, 'method': str}
```

---

### Stage 3: Read Counting

**Module:** `qc_core/counter.py`

**Output format (ТЗ Section 1.2.4):**
```
miRNA_id	sample_id	count
hsa-miR-21-5p	sample_001	1543
hsa-let-7a-5p	sample_001	892
...
```

**Output:** `{sample_id}_counts.tsv`

```python
from modules.mirna.qc_core.counter import generate_counts_tsv

result = generate_counts_tsv(
    sam_file='aligned.sam',
    output_dir='output/',
    sample_id='sample_001'
)
# Returns: {'counts_tsv': path, 'unique_mirnas': int, 'top_mirnas': list}
```

---

### Stage 4: ID Validation

**Module:** `qc_core/validator.py`

Validates all detected miRNA IDs against miRBase reference.

**Output:** `{sample_id}_counts_validation.txt`

```python
from modules.mirna.qc_core.validator import validate_mirbase_ids

result = validate_mirbase_ids(
    counts_tsv='counts.tsv',
    reference_fasta='mirbase_hsa.fa'
)
# Returns: {'valid_mirnas': int, 'invalid_mirnas': int, 'validation_rate': float}
```

---

## Module Architecture

```
modules/mirna/
├── __init__.py
├── README.md                    # This file
├── quality_control.py           # Main pipeline integration
├── logging_system.py            # QC logger (from genomics)
├── qc_core/                     # Core QC modules
│   ├── __init__.py
│   ├── trimmer.py              # Adapter trimming (PRIMARY/FALLBACK)
│   ├── aligner.py              # miRBase alignment (PRIMARY/FALLBACK)
│   ├── counter.py              # Read counting → counts.tsv
│   └── validator.py            # ID validation
└── qc_utils/                    # Utility modules
    ├── __init__.py
    ├── io_handler.py           # FASTQ I/O (supports .gz)
    └── reporter.py             # HTML report generation
```

---

## Hybrid PRIMARY/FALLBACK Architecture

**Design Philosophy:**
- Try fast external tools first (cutadapt, bowtie)
- Fall back to pure Python if tools unavailable
- Identical output format regardless of method
- No Docker/conda required (per ТЗ requirements)

**Example:**

```python
# Trimming
if has_cutadapt():
    result = trim_with_cutadapt(...)  # Fast C tool
else:
    result = trim_with_biopython(...) # Pure Python

# Both return same format:
# {'trimmed_fastq': path, 'total_reads': int, ...}
```

---

## Output Files

For sample `sample_001`:

```
output/
├── sample_001_trimmed.fastq            # Stage 1: Filtered reads (18-25 nt)
├── sample_001_aligned.sam              # Stage 2: SAM alignments
├── sample_001_counts.tsv               # Stage 3: ТЗ-compliant counts
├── sample_001_counts_validation.txt    # Stage 4: Validation report
├── sample_001_metadata.json            # Pipeline metadata
└── sample_001_report.html              # HTML report
```

---

## Batch Processing

Process multiple samples:

```python
from modules.mirna.quality_control import run_mirna_qc_batch

fastq_files = [
    'sample_001.fastq.gz',
    'sample_002.fastq.gz',
    'sample_003.fastq.gz'
]

results = run_mirna_qc_batch(
    fastq_files=fastq_files,
    reference_fasta='mirbase_hsa.fa',
    output_dir='batch_results/'
)

print(f"Completed: {results['completed']} / {results['total_samples']}")
```

---

## ТЗ Compliance

### Section 1.2.4: Output Format ✅

**Requirement:**
> Таблица в формате TSV с колонками: miRNA_id, sample_id, count

**Implementation:**
```python
# modules/mirna/qc_core/counter.py
def write_counts_tsv(counts_dict, output_file, sample_id):
    with open(output_file, 'w') as f:
        f.write("miRNA_id\tsample_id\tcount\n")
        for mirna_id, count in sorted_counts:
            f.write(f"{mirna_id}\t{sample_id}\t{count}\n")
```

**Output example:**
```
miRNA_id	sample_id	count
hsa-miR-21-5p	sample_001	1543
hsa-let-7a-5p	sample_001	892
```

### Section 1.3.4: QC Requirements ✅

| Requirement | Module | Status |
|------------|--------|--------|
| Adapter trimming | `trimmer.py` | ✅ |
| Quality control | `trimmer.py` | ✅ |
| Length filtering (18-25 nt) | `trimmer.py` | ✅ |
| Alignment to miRBase | `aligner.py` | ✅ |
| ID validation | `validator.py` | ✅ |

---

## Performance

### Test Data (10 reads):
- Trimming: <1 second
- Alignment: <1 second
- Counting: <1 second
- **Total:** <3 seconds

### Large File (775 MB, ~15M reads):
- Trimming: ~5-10 minutes (cutadapt) / ~30-60 minutes (BioPython)
- Alignment: ~10-20 minutes (bowtie) / ~2-4 hours (Python)
- Counting: ~1-2 minutes
- **Total:** ~15-30 minutes (with tools) / 2-5 hours (pure Python)

**Recommendation:** Install cutadapt and bowtie for production use.

---

## Testing

### Unit Tests

```bash
# Run unit tests
pytest modules/mirna/tests/ -v

# With coverage
pytest modules/mirna/tests/ --cov=modules.mirna --cov-report=html
```

### Integration Test

```bash
# End-to-end pipeline test
python test_full_pipeline.py
```

---

## Troubleshooting

### Issue: "cutadapt not found"
**Solution:** Install cutadapt or use BioPython fallback (automatically activated)

### Issue: "bowtie not found"
**Solution:** Install bowtie or use Python fallback (automatically activated)

### Issue: "BioPython not available"
**Solution:** `pip install biopython`

### Issue: "Invalid miRNA IDs detected"
**Solution:** Check miRBase reference version matches expected IDs

### Issue: "Low alignment rate (<50%)"
**Possible causes:**
- Wrong reference species (e.g., mouse data aligned to human miRBase)
- Poor quality reads
- Contamination with non-miRNA sequences

---

## API Reference

### Main Pipeline Function

```python
run_mirna_qc(
    input_fastq: str,           # Raw FASTQ file path
    reference_fasta: str,       # miRBase reference path
    output_dir: str,            # Output directory
    sample_id: str = None,      # Sample ID (auto-generated if None)
    min_length: int = 18,       # Minimum read length (ТЗ)
    max_length: int = 25,       # Maximum read length (ТЗ)
    index_dir: str = None,      # Bowtie index directory
    validate_ids: bool = True   # Run ID validation
) -> Dict
```

**Returns:**
```python
{
    'status': 'completed',
    'sample_id': 'sample_001',
    'counts_tsv': 'path/to/counts.tsv',
    'sam_file': 'path/to/aligned.sam',
    'trimmed_fastq': 'path/to/trimmed.fastq',
    'metadata_file': 'path/to/metadata.json',
    'pipeline_metadata': {...}
}
```

---

## Version History

### Version 1.0.0 (2025-11-12)
- ✅ Initial release
- ✅ Complete ТЗ compliance (Sections 1.2.4, 1.3.4)
- ✅ Hybrid PRIMARY/FALLBACK architecture
- ✅ Full integration testing
- ✅ HTML report generation
- ✅ Metadata tracking system

---

## Support

**Documentation:** This file
**Issues:** Report to project maintainer
**Testing:** See `test_full_pipeline.py` for examples

---

## License

Part of OmicsIntegrationSuite
Developed for НИИ им. Н.И. Пирогова

---

**Generated:** 2025-11-12
**Status:** ✅ Ready for production use
