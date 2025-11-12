# miRBase Reference Data

**Date:** 2025-11-12
**Source:** miRBase (https://mirbase.org)

---

## Files

### mature.fa (3.7 MB)
- **Description:** Complete miRBase mature sequences (all species)
- **Source:** https://mirbase.org/download/mature.fa
- **Downloaded:** 2025-11-12

### mirbase_hsa.fa (Human only)
- **Description:** Human (Homo sapiens) mature miRNA sequences only
- **Count:** ~2,718 miRNAs
- **Extracted:** `grep -A1 "^>hsa-" mature.fa > mirbase_hsa.fa`

---

## Usage

```python
from modules.mirna.quality_control import run_mirna_qc

result = run_mirna_qc(
    input_fastq='sample.fastq.gz',
    reference_fasta='reference_data/mirna/mirbase_hsa.fa',
    output_dir='results/'
)
```

---

## Update Instructions

To update to latest miRBase version:

```bash
cd reference_data/mirna

# Download latest
curl -L -o mature.fa "https://mirbase.org/download/mature.fa"

# Extract human miRNAs
grep -A1 "^>hsa-" mature.fa > mirbase_hsa.fa

# Verify
wc -l mirbase_hsa.fa
head -10 mirbase_hsa.fa
```

---

**Note:** This reference is used by the miRNA QC module for alignment and ID validation.
