"""
Pytest configuration and fixtures for OmicsIntegrationSuite tests
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_data_dir():
    """
    Create a temporary directory for test files

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_uploaded_files_dir(temp_data_dir):
    """
    Create mock uploaded_files directory structure for proteomics

    Returns:
        Path: Path to proteomics/uploaded_files directory
    """
    proteomics_dir = temp_data_dir / "proteomics" / "uploaded_files"
    proteomics_dir.mkdir(parents=True)
    return proteomics_dir


@pytest.fixture
def mock_incoming_dir(temp_data_dir):
    """
    Create mock 00_incoming directory structure for proteomics

    Returns:
        Path: Path to 00_incoming/proteomics directory
    """
    incoming_dir = temp_data_dir / "00_incoming" / "proteomics"
    incoming_dir.mkdir(parents=True)
    return incoming_dir


@pytest.fixture
def sample_mzml_file(mock_uploaded_files_dir):
    """
    Create a sample .mzML file for testing

    Returns:
        Path: Path to created .mzML file
    """
    file_path = mock_uploaded_files_dir / "sample.mzML"
    file_path.write_text("<?xml version='1.0' encoding='UTF-8'?>\n<mzML></mzML>")
    return file_path


@pytest.fixture
def sample_raw_file(mock_uploaded_files_dir):
    """
    Create a sample .raw file for testing

    Returns:
        Path: Path to created .raw file
    """
    file_path = mock_uploaded_files_dir / "sample.raw"
    file_path.write_bytes(b'\x00\x01\x02\x03\x04\x05')  # Binary content
    return file_path


@pytest.fixture
def sample_csv_file(mock_uploaded_files_dir):
    """
    Create a sample .csv protein quantification file

    Returns:
        Path: Path to created .csv file
    """
    file_path = mock_uploaded_files_dir / "proteins.csv"
    content = "Accession,Protein,Intensity,Coverage\nP12345,ProteinA,1000.5,45.2\nP67890,ProteinB,2500.3,62.8\n"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def multiple_test_files(mock_uploaded_files_dir, mock_incoming_dir):
    """
    Create multiple test files in both directories

    Returns:
        dict: Dictionary with file paths
    """
    files = {}

    # In uploaded_files
    files['mzml'] = mock_uploaded_files_dir / "test1.mzML"
    files['mzml'].write_text("<?xml version='1.0'?><mzML></mzML>")

    files['raw'] = mock_uploaded_files_dir / "test2.raw"
    files['raw'].write_bytes(b'\x00\x01')

    files['csv'] = mock_uploaded_files_dir / "matrix.csv"
    files['csv'].write_text("protein,value\nP1,100\n")

    # In incoming
    files['incoming_mgf'] = mock_incoming_dir / "test3.mgf"
    files['incoming_mgf'].write_text("BEGIN IONS\nEND IONS\n")

    # Invalid files (should be filtered)
    files['invalid_exe'] = mock_uploaded_files_dir / "malware.exe"
    files['invalid_exe'].write_bytes(b'MZ\x90\x00')

    files['invalid_txt'] = mock_uploaded_files_dir / "notes.txt"
    files['invalid_txt'].write_text("Just notes")

    return files


@pytest.fixture
def mock_streamlit_session():
    """
    Mock Streamlit session_state for testing

    Returns:
        dict: Mock session state
    """
    return {
        'uploaded_files': None,
        'processing_complete': False,
        'selected_existing_files': [],
        'proteomics_results': None,
        'session_id': 'test_session_123'
    }
