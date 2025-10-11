"""
FASTQ Analyzer - validation and metrics calculation in one pass
Efficient streaming processing without loading entire file into memory
"""

import gzip
from pathlib import Path
from typing import Dict, Any, Iterator, Tuple, Optional
import sys

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class FastQAnalyzer:
    """Efficient FASTQ analyzer with streaming processing."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize FASTQ analyzer.
        
        Args:
            verbose: Enable verbose output with progress bars
        """
        self.verbose = verbose
        self.reset_metrics()
    
    def reset_metrics(self):
        """Reset all metrics to initial state."""
        self.metrics = {
            'total_reads': 0,
            'total_bases': 0,
            'avg_read_length': 0.0,
            'min_read_length': float('inf'),
            'max_read_length': 0,
            'avg_quality_score': 0.0,
            'q20_percentage': 0.0,
            'q30_percentage': 0.0,
            'gc_content': 0.0,
            'n_percentage': 0.0,
            'status': 'UNKNOWN'
        }
        self._accumulators = {
            'total_quality': 0,
            'q20_bases': 0,
            'q30_bases': 0,
            'gc_bases': 0,
            'n_bases': 0
        }
    
    def analyze(self, filepath: str, sample_size: int = 10000) -> Dict[str, Any]:
        """
        Analyze FASTQ file and return metrics.
        
        Args:
            filepath: Path to FASTQ file
            sample_size: Number of reads to sample for analysis
            
        Returns:
            Dictionary containing calculated metrics
        """
        self.reset_metrics()
        
        # Get file info
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_size = path.stat().st_size
        is_gzipped = filepath.endswith('.gz')
        
        # Process file
        with self._open_file(filepath, is_gzipped) as f:
            # Setup progress bar if verbose
            pbar = None
            if self.verbose and HAS_TQDM:
                pbar = tqdm(total=sample_size, desc="Analyzing", unit="reads")
            
            # Process reads
            for i, (seq, qual) in enumerate(self._read_fastq(f)):
                if i >= sample_size:
                    break
                
                self._process_record(seq, qual)
                
                if pbar:
                    pbar.update(1)
            
            if pbar:
                pbar.close()
        
        # Finalize metrics
        self._finalize_metrics()
        self.metrics['file_size_mb'] = file_size / (1024 * 1024)
        self.metrics['filename'] = path.name
        
        return self.metrics
    
    def validate(self, filepath: str, max_records: int = 1000) -> Tuple[bool, Optional[str]]:
        """
        Quick validation of FASTQ format.
        
        Args:
            filepath: Path to FASTQ file
            max_records: Maximum number of records to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return False, "File not found"
            
            is_gzipped = filepath.endswith('.gz')
            records_checked = 0
            
            with self._open_file(filepath, is_gzipped) as f:
                for i, (seq, qual) in enumerate(self._read_fastq(f)):
                    if i >= max_records:
                        break
                    
                    # Check sequence and quality lengths match
                    if len(seq) != len(qual):
                        return False, f"Sequence and quality lengths don't match at record {i+1}"
                    
                    # Check for valid nucleotides (allow N)
                    valid_chars = set('ACGTNacgtn')
                    if not set(seq).issubset(valid_chars):
                        invalid = set(seq) - valid_chars
                        return False, f"Invalid nucleotides at record {i+1}: {invalid}"
                    
                    records_checked += 1
            
            if records_checked == 0:
                return False, "No valid FASTQ records found"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _open_file(self, filepath: str, is_gzipped: bool):
        """Open file with proper handling for gzipped files."""
        if is_gzipped:
            return gzip.open(filepath, 'rt', encoding='utf-8', errors='replace')
        return open(filepath, 'r', encoding='utf-8', errors='replace')
    
    def _read_fastq(self, file_handle) -> Iterator[Tuple[str, str]]:
        """
        Generator for reading FASTQ records.
        
        Yields:
            Tuple of (sequence, quality) strings
        """
        while True:
            try:
                # Read 4 lines for a FASTQ record
                header = file_handle.readline()
                if not header:
                    break
                
                # Check header format
                if not header.startswith('@'):
                    if self.verbose:
                        print(f"Warning: Invalid header (doesn't start with @): {header.strip()}", file=sys.stderr)
                    continue
                
                sequence = file_handle.readline().strip()
                separator = file_handle.readline()
                quality = file_handle.readline().strip()
                
                # Check separator
                if not separator.startswith('+'):
                    if self.verbose:
                        print(f"Warning: Invalid separator (doesn't start with +)", file=sys.stderr)
                    continue
                
                if not all([sequence, quality]):
                    break
                
                yield sequence, quality
                
            except Exception as e:
                if self.verbose:
                    print(f"Error reading record: {e}", file=sys.stderr)
                break
    
    def _process_record(self, sequence: str, quality: str):
        """
        Process single FASTQ record and update metrics.
        
        Args:
            sequence: DNA sequence string
            quality: Quality string (Phred33 encoded)
        """
        self.metrics['total_reads'] += 1
        read_length = len(sequence)
        self.metrics['total_bases'] += read_length
        
        # Update length metrics
        self.metrics['min_read_length'] = min(self.metrics['min_read_length'], read_length)
        self.metrics['max_read_length'] = max(self.metrics['max_read_length'], read_length)
        
        # Count bases
        seq_upper = sequence.upper()
        self._accumulators['n_bases'] += seq_upper.count('N')
        self._accumulators['gc_bases'] += seq_upper.count('G') + seq_upper.count('C')
        
        # Process quality scores (Phred33: ASCII-33)
        for qual_char in quality:
            qual_score = ord(qual_char) - 33
            self._accumulators['total_quality'] += qual_score
            
            if qual_score >= 20:
                self._accumulators['q20_bases'] += 1
            if qual_score >= 30:
                self._accumulators['q30_bases'] += 1
    
    def _finalize_metrics(self):
        """Calculate final metrics from accumulators."""
        if self.metrics['total_reads'] == 0:
            self.metrics['status'] = 'FAIL'
            return
        
        total_bases = self.metrics['total_bases']
        
        # Calculate averages
        self.metrics['avg_read_length'] = total_bases / self.metrics['total_reads']
        self.metrics['avg_quality_score'] = self._accumulators['total_quality'] / total_bases if total_bases > 0 else 0
        
        # Calculate percentages
        if total_bases > 0:
            self.metrics['q20_percentage'] = (self._accumulators['q20_bases'] / total_bases) * 100
            self.metrics['q30_percentage'] = (self._accumulators['q30_bases'] / total_bases) * 100
            self.metrics['gc_content'] = (self._accumulators['gc_bases'] / total_bases) * 100
            self.metrics['n_percentage'] = (self._accumulators['n_bases'] / total_bases) * 100
        
        # Fix infinity value
        if self.metrics['min_read_length'] == float('inf'):
            self.metrics['min_read_length'] = 0
        
        # Determine quality status based on Q30 percentage
        q30 = self.metrics['q30_percentage']
        if q30 >= 80:
            self.metrics['status'] = 'PASS'
        elif q30 >= 50:
            self.metrics['status'] = 'WARNING'
        else:
            self.metrics['status'] = 'FAIL'