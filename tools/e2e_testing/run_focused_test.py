#!/usr/bin/env python3
"""
Focused E2E Test Runner
CLI tool for running end-to-end tests on OmicsIntegrationSuite modules
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Optional

from .modules.proteomics import ProteomicsTest
from .modules.mirna import MiRNATest
from .modules.genomics import GenomicsTest


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    config_file = Path(__file__).parent / config_path

    if not config_file.exists():
        print(f"⚠️ Config file not found: {config_file}")
        print("Using default configuration")
        return {}

    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_proteomics_test(args, config: dict):
    """Run proteomics module test"""
    test = ProteomicsTest(headless=args.headless)

    if args.file:
        # Test single file
        results = test.run_test(args.file, timeout=args.timeout)
        return all(results.values())
    else:
        # Test all default files
        file_list = config.get('proteomics', {}).get('test_files')
        all_results = test.test_all_files(file_list=file_list, timeout=args.timeout)

        return all(
            all(results.values())
            for results in all_results.values()
        )


def run_mirna_test(args, config: dict):
    """Run miRNA module test"""
    test = MiRNATest(headless=args.headless)

    if args.file:
        # Test single file
        results = test.run_test(args.file, timeout=args.timeout)
        return all(results.values())
    else:
        # Test all default files
        file_list = config.get('mirna', {}).get('test_files')
        all_results = test.test_all_files(file_list=file_list, timeout=args.timeout)

        return all(
            all(results.values())
            for results in all_results.values()
        )


def run_genomics_test(args, config: dict):
    """Run genomics module test"""
    test = GenomicsTest(headless=args.headless)

    if args.file:
        # Test single file
        results = test.run_test(args.file, timeout=args.timeout)
        return all(results.values())
    else:
        # Test all default files
        file_list = config.get('genomics', {}).get('test_files')
        all_results = test.test_all_files(file_list=file_list, timeout=args.timeout)

        return all(
            all(results.values())
            for results in all_results.values()
        )


def run_all_modules(args, config: dict):
    """Run tests for all modules"""
    print("\n" + "=" * 70)
    print("RUNNING ALL MODULE TESTS")
    print("=" * 70)

    results = {}

    # Proteomics
    print("\n" + "=" * 70)
    print("MODULE 1/3: PROTEOMICS")
    print("=" * 70)
    results['proteomics'] = run_proteomics_test(args, config)

    # miRNA
    print("\n" + "=" * 70)
    print("MODULE 2/3: miRNA")
    print("=" * 70)
    results['mirna'] = run_mirna_test(args, config)

    # Genomics
    print("\n" + "=" * 70)
    print("MODULE 3/3: GENOMICS")
    print("=" * 70)
    results['genomics'] = run_genomics_test(args, config)

    # Print final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY - ALL MODULES")
    print("=" * 70)

    for module, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{module.upper()}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 ALL MODULE TESTS PASSED!")
    else:
        failed = [m for m, p in results.items() if not p]
        print(f"\n⚠️ FAILED MODULES: {', '.join(failed)}")

    return all_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="E2E Testing Tool for OmicsIntegrationSuite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all proteomics files
  python run_focused_test.py proteomics

  # Test specific file
  python run_focused_test.py proteomics --file tiny.pwiz.1.1.mzML

  # Test in headless mode with custom timeout
  python run_focused_test.py mirna --headless --timeout 900

  # Test all modules
  python run_focused_test.py all

  # Test all modules in headless mode
  python run_focused_test.py all --headless
        """
    )

    parser.add_argument(
        'module',
        choices=['proteomics', 'mirna', 'genomics', 'all'],
        help='Module to test (or "all" for all modules)'
    )

    parser.add_argument(
        '--file',
        type=str,
        help='Specific file to test (optional, tests all default files if not specified)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no GUI)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Maximum wait time for processing in seconds (default: 600)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Run tests based on module selection
    if args.module == 'all':
        success = run_all_modules(args, config)
    elif args.module == 'proteomics':
        success = run_proteomics_test(args, config)
    elif args.module == 'mirna':
        success = run_mirna_test(args, config)
    elif args.module == 'genomics':
        success = run_genomics_test(args, config)
    else:
        print(f"❌ Unknown module: {args.module}")
        sys.exit(1)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
