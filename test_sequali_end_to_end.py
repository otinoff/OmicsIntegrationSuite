#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Test: Sequali QC with Real Data
Performs full QC analysis and saves all artifacts
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Configuration
INPUT_FILE = Path("data/00_incoming/genomics/Undetermined_S0_L001_R1_001.fastq.gz")
OUTPUT_DIR = Path("data/03_reports/genomics_qc/sequali_e2e_test")
LOG_FILE = OUTPUT_DIR / "sequali_execution_log.txt"
REPORT_FILE = OUTPUT_DIR / "test_report.md"

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("SEQUALI END-TO-END TEST WITH REAL DATA")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Input file: {INPUT_FILE}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Log file: {LOG_FILE}")
print("=" * 80)

# Check input file
if not INPUT_FILE.exists():
    print(f"ERROR: Input file not found: {INPUT_FILE}")
    sys.exit(1)

file_size_mb = INPUT_FILE.stat().st_size / (1024 * 1024)
print(f"\nInput file size: {file_size_mb:.2f} MB")

# Step 1: Direct Sequali execution
print("\n" + "=" * 80)
print("STEP 1: Running Sequali (C++ engine) - PRIMARY METHOD")
print("=" * 80)

# Prepare Sequali command
full_name = INPUT_FILE.name
base_name = INPUT_FILE.stem

cmd = [
    'sequali',
    '--dir', str(OUTPUT_DIR),
    '--html', full_name,
    '--json', full_name,
    str(INPUT_FILE)
]

print(f"\nCommand: {' '.join(cmd)}")
print("\nStarting Sequali analysis...")
print("(This may take several minutes for 157 MB file)")
print("-" * 80)

# Run Sequali and capture all output
start_time = datetime.now()

try:
    with open(LOG_FILE, 'w', encoding='utf-8') as log_f:
        # Write header to log
        log_f.write("=" * 80 + "\n")
        log_f.write("SEQUALI EXECUTION LOG\n")
        log_f.write("=" * 80 + "\n")
        log_f.write(f"Timestamp: {start_time.isoformat()}\n")
        log_f.write(f"Command: {' '.join(cmd)}\n")
        log_f.write(f"Input: {INPUT_FILE}\n")
        log_f.write(f"Output: {OUTPUT_DIR}\n")
        log_f.write("=" * 80 + "\n\n")
        log_f.flush()

        # Run Sequali with real-time output capture
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Read stdout and stderr in real-time
        stdout_lines = []
        stderr_lines = []

        # Wait for completion
        stdout, stderr = process.communicate(timeout=600)  # 10 min timeout

        # Save stdout
        if stdout:
            log_f.write("STDOUT:\n")
            log_f.write("-" * 80 + "\n")
            log_f.write(stdout)
            log_f.write("\n" + "-" * 80 + "\n\n")
            stdout_lines = stdout.splitlines()

            # Print to console
            print("\nSequali STDOUT:")
            for line in stdout_lines[-20:]:  # Last 20 lines
                print(f"  {line}")

        # Save stderr
        if stderr:
            log_f.write("STDERR:\n")
            log_f.write("-" * 80 + "\n")
            log_f.write(stderr)
            log_f.write("\n" + "-" * 80 + "\n\n")
            stderr_lines = stderr.splitlines()

            # Print to console
            print("\nSequali STDERR:")
            for line in stderr_lines[-20:]:  # Last 20 lines
                print(f"  {line}")

        # Save return code
        log_f.write(f"\nReturn code: {process.returncode}\n")
        log_f.write(f"Execution time: {(datetime.now() - start_time).total_seconds():.2f} seconds\n")
        log_f.flush()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'=' * 80}")
    print(f"Sequali execution completed in {duration:.2f} seconds")
    print(f"Return code: {process.returncode}")
    print(f"Log saved to: {LOG_FILE}")

    if process.returncode != 0:
        print("\nWARNING: Sequali returned non-zero exit code")
        print("Check log file for details")

except subprocess.TimeoutExpired:
    print("\nERROR: Sequali execution timed out (10 minutes)")
    sys.exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Find and verify output files
print("\n" + "=" * 80)
print("STEP 2: Verifying Sequali Output Files")
print("=" * 80)

# List all files in output directory
print("\nFiles in output directory:")
output_files = list(OUTPUT_DIR.glob("*"))
for f in sorted(output_files):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:<60} {size_kb:>10.2f} KB")

# Try to find HTML report (multiple naming patterns)
html_path = None
html_candidates = [
    OUTPUT_DIR / f"{full_name}.html",
    OUTPUT_DIR / f"{base_name}.html",
    OUTPUT_DIR / full_name,
    OUTPUT_DIR / base_name
]

print("\nSearching for HTML report...")
for candidate in html_candidates:
    print(f"  Checking: {candidate.name}")
    if candidate.exists() and candidate.stat().st_size > 10000:
        html_path = candidate
        print(f"  ✓ FOUND: {candidate.name} ({candidate.stat().st_size / 1024:.2f} KB)")
        break

# Try to find JSON metrics
json_path = None
json_candidates = [
    OUTPUT_DIR / f"{full_name}.json",
    OUTPUT_DIR / f"{base_name}.json"
]

print("\nSearching for JSON metrics...")
for candidate in json_candidates:
    print(f"  Checking: {candidate.name}")
    if candidate.exists() and candidate.stat().st_size > 0:
        json_path = candidate
        print(f"  ✓ FOUND: {candidate.name} ({candidate.stat().st_size / 1024:.2f} KB)")
        break

# Step 3: Parse and display metrics
print("\n" + "=" * 80)
print("STEP 3: Parsing Sequali Metrics")
print("=" * 80)

metrics = {}

if json_path and json_path.exists():
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Extract key metrics from Sequali JSON
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

        # Determine QC status
        if q30_pct >= 80 and n_pct < 5:
            status = "PASS"
        elif q30_pct >= 70 or n_pct < 10:
            status = "WARNING"
        else:
            status = "FAIL"

        metrics = {
            'total_reads': total_reads,
            'total_bases': total_bases,
            'avg_read_length': mean_length,
            'min_length': summary.get('min_length', 0),
            'max_length': summary.get('max_length', 0),
            'q20_percentage': q20_pct,
            'q30_percentage': q30_pct,
            'gc_content': gc_pct,
            'n_percentage': n_pct,
            'status': status
        }

        print("\nKEY METRICS:")
        print(f"  Total reads:       {total_reads:,}")
        print(f"  Total bases:       {total_bases:,}")
        print(f"  Avg read length:   {mean_length:.1f} bp")
        print(f"  Min/Max length:    {summary.get('min_length', 0)} / {summary.get('max_length', 0)} bp")
        print(f"  Q20:               {q20_pct:.2f}%")
        print(f"  Q30:               {q30_pct:.2f}%")
        print(f"  GC content:        {gc_pct:.2f}%")
        print(f"  N content:         {n_pct:.4f}%")
        print(f"  QC Status:         {status}")

    except Exception as e:
        print(f"\nERROR parsing JSON: {e}")
else:
    print("\nWARNING: JSON metrics file not found")

# Step 4: Generate test report
print("\n" + "=" * 80)
print("STEP 4: Generating Test Report")
print("=" * 80)

report_content = f"""# Sequali End-to-End Test Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Test:** Production Sequali QC with Real Data

---

## 📋 Test Configuration

- **Input File:** `{INPUT_FILE}`
- **File Size:** {file_size_mb:.2f} MB
- **Output Directory:** `{OUTPUT_DIR}`
- **Execution Time:** {duration:.2f} seconds
- **Sequali Version:** 1.0.2

---

## 🧪 Test Execution

### Command:
```bash
{' '.join(cmd)}
```

### Execution Status:
- **Return Code:** {process.returncode}
- **Duration:** {duration:.2f} seconds ({duration/60:.2f} minutes)
- **Processing Speed:** {file_size_mb / (duration / 60):.2f} MB/min

---

## 📊 Results

### Output Files:
"""

if html_path:
    report_content += f"- ✅ **HTML Report:** `{html_path.name}` ({html_path.stat().st_size / 1024:.2f} KB)\n"
else:
    report_content += "- ❌ **HTML Report:** NOT FOUND\n"

if json_path:
    report_content += f"- ✅ **JSON Metrics:** `{json_path.name}` ({json_path.stat().st_size / 1024:.2f} KB)\n"
else:
    report_content += "- ❌ **JSON Metrics:** NOT FOUND\n"

report_content += f"- ✅ **Execution Log:** `{LOG_FILE.name}` ({LOG_FILE.stat().st_size / 1024:.2f} KB)\n"

if metrics:
    report_content += f"""
### Key Metrics:

| Metric | Value |
|--------|-------|
| **Total Reads** | {metrics['total_reads']:,} |
| **Total Bases** | {metrics['total_bases']:,} |
| **Average Read Length** | {metrics['avg_read_length']:.1f} bp |
| **Read Length Range** | {metrics['min_length']} - {metrics['max_length']} bp |
| **Q20 Percentage** | {metrics['q20_percentage']:.2f}% |
| **Q30 Percentage** | {metrics['q30_percentage']:.2f}% |
| **GC Content** | {metrics['gc_content']:.2f}% |
| **N Content** | {metrics['n_percentage']:.4f}% |
| **QC Status** | **{metrics['status']}** |

---

## ✅ Test Summary

### Quality Assessment:
"""

    if metrics['status'] == "PASS":
        report_content += "✅ **PASS** - High quality sequencing data\n"
    elif metrics['status'] == "WARNING":
        report_content += "⚠️ **WARNING** - Acceptable quality but some concerns\n"
    else:
        report_content += "❌ **FAIL** - Low quality sequencing data\n"

    report_content += f"""
### Observations:
- Q30 percentage: {metrics['q30_percentage']:.2f}% (threshold: 80% for PASS)
- N content: {metrics['n_percentage']:.4f}% (threshold: <5% for PASS)
- GC content: {metrics['gc_content']:.2f}% (typical range: 40-60%)
"""

report_content += """
---

## 🎯 Conclusion

"""

if process.returncode == 0 and html_path and json_path:
    report_content += """✅ **Sequali execution SUCCESSFUL**

All artifacts generated:
1. ✅ HTML report (visual QC)
2. ✅ JSON metrics (structured data)
3. ✅ Execution log (troubleshooting)

**Status:** Production ready! Sequali PRIMARY method working correctly.
"""
else:
    report_content += """⚠️ **Sequali execution completed with issues**

Check execution log for details:
```bash
cat {LOG_FILE}
```

**Recommendation:** Investigate errors in log file.
"""

report_content += f"""
---

## 📁 Artifact Locations

All artifacts saved to: `{OUTPUT_DIR}`

### Files:
"""

for f in sorted(OUTPUT_DIR.glob("*")):
    if f.is_file():
        report_content += f"- `{f.name}`\n"

report_content += f"""
---

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Sequali Version:** 1.0.2
**Test Status:** {'✅ SUCCESS' if process.returncode == 0 else '⚠️ WITH WARNINGS'}
"""

# Save report
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write(report_content)

print(f"\nTest report saved to: {REPORT_FILE}")

# Final summary
print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print(f"\n📁 All artifacts saved to: {OUTPUT_DIR}")
print(f"\n📄 Generated files:")
print(f"   - Test Report:     {REPORT_FILE.name}")
print(f"   - Execution Log:   {LOG_FILE.name}")
if html_path:
    print(f"   - HTML Report:     {html_path.name}")
if json_path:
    print(f"   - JSON Metrics:    {json_path.name}")

print(f"\n🎯 Test Status: {'✅ SUCCESS' if process.returncode == 0 and html_path and json_path else '⚠️ CHECK LOGS'}")
print("\n" + "=" * 80)
