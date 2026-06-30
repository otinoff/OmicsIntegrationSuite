#!/usr/bin/env python3
"""
Master Test Runner for OmicsIntegrationSuite E2E Tests
Runs all module E2E tests and generates comprehensive report

Inspired by GrantService E2E testing approach
Author: Claude Code
Date: 2025-11-13
Iteration: 009 - E2E Testing & Knowledge Corpus
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


# ==================== CONFIGURATION ====================

# Test suite configuration
TESTS = [
    {
        'name': 'scRNA-seq QC',
        'script': 'test_scrnaseq_qc_e2e.py',
        'timeout': 600,  # 10 minutes
        'status': 'active',
        'description': 'Single-cell RNA-seq quality control with PBMC 3K benchmark'
    },
    {
        'name': 'Genomics QC',
        'script': 'test_genomics_qc_e2e.py',
        'timeout': 600,
        'status': 'pending',
        'description': 'FASTQ quality control with real sequencing data'
    },
    {
        'name': 'miRNA QC (Customer)',
        'script': 'test_mirna_qc_e2e.py',
        'timeout': 600,
        'status': 'active',
        'description': 'miRNA-seq QC with 158MB customer FASTQ (Quality: 96.3/100)'
    },
    {
        'name': 'miRNA QC (Public)',
        'script': 'test_mirna_public_e2e.py',
        'timeout': 600,
        'status': 'active',
        'description': 'miRNA-seq QC with 220MB public NCBI dataset SRR35945551 (Quality: 100.0/100)'
    }
]

# Reporting
REPORT_DIR = Path(__file__).parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)


# ==================== HELPER FUNCTIONS ====================

def print_header():
    """Print test suite header"""
    print("\n" + "=" * 70)
    print("OMICS INTEGRATION SUITE - E2E TEST RUNNER")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tests: {len([t for t in TESTS if t['status'] == 'active'])}/{len(TESTS)} active")
    print("=" * 70 + "\n")


def run_test(test_config: Dict) -> Tuple[bool, float, str]:
    """
    Run a single E2E test

    Args:
        test_config: Test configuration dictionary

    Returns:
        (success, duration, output): Test results
    """
    script_path = Path(__file__).parent / test_config['script']

    if not script_path.exists():
        return False, 0.0, f"ERROR: Test script not found: {script_path}"

    start_time = time.time()

    try:
        # Run test with timeout
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=test_config['timeout']
        )

        duration = time.time() - start_time
        success = result.returncode == 0

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\n\nSTDERR:\n" + result.stderr

        return success, duration, output

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, duration, f"ERROR: Test timed out after {test_config['timeout']}s"

    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"ERROR: {str(e)}"


def extract_quality_score(output: str) -> float:
    """Extract quality score from test output"""
    try:
        for line in output.split('\n'):
            if 'Quality Score:' in line:
                # Extract number between "Quality Score: " and "/100"
                score_str = line.split('Quality Score:')[1].split('/100')[0].strip()
                return float(score_str)
    except:
        pass
    return 0.0


def print_test_summary(results: List[Dict]):
    """Print comprehensive test summary"""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    total_duration = sum(r['duration'] for r in results)
    avg_quality = sum(r['quality_score'] for r in results) / total_tests if total_tests > 0 else 0

    # Individual results
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        quality_display = f"Quality: {result['quality_score']:.1f}/100" if result['quality_score'] > 0 else "N/A"

        print(f"[{i}/{total_tests}] {result['name']:20} {status} ({result['duration']:.1f}s) {quality_display}")

    # Overall statistics
    print("\n" + "-" * 70)
    print(f"\n📊 Statistics:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Pass rate: {passed_tests/total_tests*100:.1f}%")
    print(f"   Total time: {total_duration/60:.1f} minutes")
    print(f"   Average quality score: {avg_quality:.1f}/100")

    # Final verdict
    print("\n" + "=" * 70)
    if passed_tests == total_tests and avg_quality >= 85:
        print("✅ ALL TESTS PASSED - PRODUCTION READY")
    elif passed_tests == total_tests:
        print("⚠️  ALL TESTS PASSED - Quality needs improvement")
    elif passed_tests / total_tests >= 0.95:
        print("⚠️  MOSTLY PASSING - Some tests failed")
    else:
        print("❌ CRITICAL FAILURES - Not ready for production")
    print("=" * 70 + "\n")


def save_detailed_report(results: List[Dict], report_path: Path):
    """Save detailed HTML report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_path / f"e2e_test_report_{timestamp}.html"

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Omics E2E Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #333; }}
        .summary {{ background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .test {{ background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
        .pass {{ border-left: 5px solid #4CAF50; }}
        .fail {{ border-left: 5px solid #f44336; }}
        .metric {{ display: inline-block; margin-right: 30px; }}
        pre {{ background-color: #f9f9f9; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Omics Integration Suite - E2E Test Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metric"><strong>Total Tests:</strong> {len(results)}</div>
        <div class="metric"><strong>Passed:</strong> {sum(1 for r in results if r['success'])}</div>
        <div class="metric"><strong>Failed:</strong> {sum(1 for r in results if not r['success'])}</div>
        <div class="metric"><strong>Pass Rate:</strong> {sum(1 for r in results if r['success'])/len(results)*100:.1f}%</div>
        <div class="metric"><strong>Avg Quality:</strong> {sum(r['quality_score'] for r in results)/len(results):.1f}/100</div>
    </div>
"""

    for result in results:
        test_class = "pass" if result['success'] else "fail"
        html_content += f"""
    <div class="test {test_class}">
        <h3>{result['name']} - {'✅ PASS' if result['success'] else '❌ FAIL'}</h3>
        <p><strong>Duration:</strong> {result['duration']:.1f}s</p>
        <p><strong>Quality Score:</strong> {result['quality_score']:.1f}/100</p>
        <details>
            <summary>View Output</summary>
            <pre>{result['output'][:5000]}</pre>
        </details>
    </div>
"""

    html_content += """
</body>
</html>
"""

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n📄 Detailed report saved: {report_file}")


# ==================== MAIN ====================

def run_all_tests() -> int:
    """
    Run all E2E tests and generate reports

    Returns:
        0 if all tests pass, 1 if any fail
    """
    print_header()

    # Filter active tests
    active_tests = [t for t in TESTS if t['status'] == 'active']

    if not active_tests:
        print("⚠️  No active tests found!")
        return 1

    print(f"Running {len(active_tests)} active test(s)...\n")

    # Run each test
    results = []

    for i, test_config in enumerate(active_tests, 1):
        print(f"[{i}/{len(active_tests)}] Running: {test_config['name']}")
        print(f"    {test_config['description']}")
        print(f"    Timeout: {test_config['timeout']}s")
        print()

        success, duration, output = run_test(test_config)
        quality_score = extract_quality_score(output)

        results.append({
            'name': test_config['name'],
            'success': success,
            'duration': duration,
            'quality_score': quality_score,
            'output': output
        })

        # Print immediate result
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"    Result: {status} ({duration:.1f}s, Quality: {quality_score:.1f}/100)")
        print()

    # Print summary
    print_test_summary(results)

    # Save detailed report
    save_detailed_report(results, REPORT_DIR)

    # Return exit code
    all_passed = all(r['success'] for r in results)
    return 0 if all_passed else 1


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
