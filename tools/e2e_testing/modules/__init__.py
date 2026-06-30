"""
E2E Testing Modules
Module-specific test implementations for OmicsIntegrationSuite
"""

from .proteomics import ProteomicsTest
from .mirna import MiRNATest
from .genomics import GenomicsTest

__all__ = ['ProteomicsTest', 'MiRNATest', 'GenomicsTest']
