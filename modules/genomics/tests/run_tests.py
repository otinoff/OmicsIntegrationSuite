#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run all tests for genomics module
"""

import unittest
import sys
from pathlib import Path

# Add the modules directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """
    Run all tests for genomics module
    """
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)