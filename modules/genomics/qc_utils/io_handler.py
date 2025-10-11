"""
IO Handler - File operations and validation for FASTQ files
"""

import gzip
import os
from pathlib import Path
from typing import Iterator, Tuple, Optional, TextIO, Union
import io


class IOHandler:
    """Handle file operations for FASTQ files."""
    
    SUPPORTED_EXTENSIONS = {'.fastq', '.fq', '.fastq.gz', '.fq.gz'}
    
    @staticmethod
    def validate_input(file_path: str) -> bool:
        """
        Validate input file exists and has correct extension.
        
        Args:
            file_path: Path to FASTQ file
            
        Returns:
            True if valid, False otherwise
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            print(f"Error: File not found: {file_path}")
            return False
        
        # Check if it's a file (not directory)
        if not path.is_file():
            print(f"Error: Path is not a file: {file_path}")
            return False
        
        # Check extension
        if path.suffix == '.gz':
            # For gzipped files, check double extension
            if path.suffixes[-2:] not in [['.fastq', '.gz'], ['.fq', '.gz']]:
                print(f"Error: Unsupported file format. Expected FASTQ file.")
                return False
        elif path.suffix not in {'.fastq', '.fq'}:
            print(f"Error: Unsupported file format. Expected FASTQ file.")
            return False
        
        return True
    
    @staticmethod
    def open_file(file_path: str) -> TextIO:
        """
        Open FASTQ file (gzipped or plain text).
        
        Args:
            file_path: Path to FASTQ file
            
        Returns:
            File handle for reading
        """
        path = Path(file_path)
        
        if path.suffix == '.gz':
            # Open gzipped file
            return io.TextIOWrapper(
                gzip.open(file_path, 'rb'),
                encoding='utf-8',
                errors='replace'
            )
        else:
            # Open plain text file
            return open(file_path, 'r', encoding='utf-8', errors='replace')
    
    @staticmethod
    def read_fastq_records(file_handle: TextIO) -> Iterator[Tuple[str, str, str]]:
        """
        Generator to read FASTQ records.
        
        Args:
            file_handle: Open file handle
            
        Yields:
            Tuples of (header, sequence, quality)
        """
        while True:
            try:
                # Read 4 lines that make up a FASTQ record
                header = file_handle.readline().strip()
                if not header:
                    break  # End of file
                
                sequence = file_handle.readline().strip()
                plus_line = file_handle.readline().strip()
                quality = file_handle.readline().strip()
                
                # Basic validation
                if not header.startswith('@'):
                    continue  # Skip malformed records
                
                if not plus_line.startswith('+'):
                    continue  # Skip malformed records
                
                if len(sequence) != len(quality):
                    continue  # Skip malformed records
                
                yield (header, sequence, quality)
                
            except Exception as e:
                # Skip corrupted records
                continue
    
    @staticmethod
    def get_file_size(file_path: str) -> float:
        """
        Get file size in MB.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in megabytes
        """
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except:
            return 0.0
    
    @staticmethod
    def create_output_path(input_path: str, suffix: str = "_report", 
                          extension: str = ".html") -> str:
        """
        Create output file path based on input file.
        
        Args:
            input_path: Input file path
            suffix: Suffix to add before extension
            extension: New file extension
            
        Returns:
            Output file path
        """
        path = Path(input_path)
        
        # Remove .gz extension if present
        if path.suffix == '.gz':
            stem = path.stem
        else:
            stem = path.stem
        
        # Create output path in same directory
        output_path = path.parent / f"{stem}{suffix}{extension}"
        
        return str(output_path)