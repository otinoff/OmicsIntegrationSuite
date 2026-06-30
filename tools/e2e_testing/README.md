# E2E Testing Tool for OmicsIntegrationSuite

Comprehensive end-to-end testing framework for OmicsIntegrationSuite web platform using browser automation and server-side validation.

## Overview

This tool provides automated E2E testing for all OmicsIntegrationSuite modules:
- **Proteomics** - Mass spectrometry data processing (mzML format)
- **miRNA** - MicroRNA analysis (FASTA format)
- **Genomics** - Genomic variant analysis (VCF format)

Each test includes:
1. **Browser automation** - Navigating UI, selecting files, triggering processing
2. **Server validation** - Checking marker files, JSON exports, processed files

## Architecture

```
tools/e2e_testing/
├── README.md              # This file
├── config.yaml            # Configuration (test files, paths, timeouts)
├── run_focused_test.py    # Main CLI entry point
├── modules/               # Module-specific test implementations
│   ├── __init__.py
│   ├── proteomics.py      # Proteomics tests
│   ├── mirna.py           # miRNA tests
│   └── genomics.py        # Genomics tests
└── helpers/               # Reusable helper classes
    ├── __init__.py
    ├── browser.py         # Browser automation (Playwright)
    └── validation.py      # Server validation (SSH)
```

## Installation

### Dependencies

```bash
# Install Python dependencies
pip install playwright pyyaml

# Install Playwright browsers
playwright install chromium
```

### SSH Access

Ensure SSH key is configured for server access:
```bash
# SSH key location (configured in config.yaml)
C:\.ssh\id_rsa

# Test connection
ssh -i "C:\.ssh\id_rsa" root@omicsintegrationsuite.onff.ru
```

## Usage

### Basic Commands

```bash
# Test all proteomics files
python run_focused_test.py proteomics

# Test specific file
python run_focused_test.py proteomics --file tiny.pwiz.1.1.mzML

# Test in headless mode (no browser GUI)
python run_focused_test.py proteomics --headless

# Test with custom timeout (in seconds)
python run_focused_test.py mirna --timeout 900

# Test all modules
python run_focused_test.py all

# Test all modules in headless mode
python run_focused_test.py all --headless
```

### Module-Specific Tests

Each module can be run individually or as part of `run_focused_test.py`:

```bash
# Run proteomics module directly
cd modules
python proteomics.py

# Run with specific file
python proteomics.py tiny.pwiz.1.1.mzML

# Run in headless mode
python proteomics.py --headless
```

### Configuration

Edit `config.yaml` to customize:

```yaml
# Global settings
global:
  base_url: "https://omicsintegrationsuite.onff.ru"
  default_timeout: 600
  headless: false

# Proteomics test files
proteomics:
  test_files:
    - "tiny.pwiz.1.1.mzML"
    - "tiny4_LTQ-FT.mzML"
    - "demo_pride_example.mzML"
```

## Test Flow

### Phase 1: Browser Automation

Using `BrowserHelper` class:

1. Navigate to OmicsIntegrationSuite URL
2. Click module in sidebar (Протеомика, МикроРНК, Геномика)
3. Select file from uploaded files list
4. Switch to "Обработка" (Processing) tab
5. Click "Запустить обработку" (Start Processing) button
6. Wait for processing to complete (check for "завершена")

### Phase 2: Server Validation

Using `ValidationHelper` class:

1. **Check marker file** - Confirms processing started
   - Path: `/tmp/{module}_processing_started.txt`

2. **Validate JSON export** - Checks structure and content
   - Path: `/var/OmicsIntegrationSuite/data/{module}/results/{module}_results.json`
   - Validates: `module`, `timestamp`, `results` fields

3. **Check processed file** - Confirms output file exists
   - Path: `/var/OmicsIntegrationSuite/data/{module}/processed/{filename}`

## Test Output

### Successful Test

```
======================================================================
PROTEOMICS E2E TEST: tiny.pwiz.1.1.mzML
======================================================================

📍 PHASE 1: Browser Automation
🌐 Opening site: https://omicsintegrationsuite.onff.ru...
✅ Site opened

📍 Navigating to proteomics module...
✅ proteomics module opened

📂 Selecting file: tiny.pwiz.1.1.mzML...
✅ File selected: tiny.pwiz.1.1.mzML

⚙️ Switching to Обработка tab...
✅ Обработка tab opened

🚀 Clicking 'Запустить обработку' button...
✅ Button clicked!

⏳ Waiting for processing (max 600s)...
✅ Processing appears complete!

✅ Browser test completed

📍 PHASE 2: Server Validation

📁 Checking Marker file...
✅ Marker file: -rw-r--r-- 1 root root 45 Dec  4 12:30 /tmp/proteomics_processing_started.txt

📊 Reading JSON file: /var/OmicsIntegrationSuite/data/proteomics/results/proteomics_results.json...
✅ JSON parsed successfully
   Module: proteomics
   Timestamp: 2025-12-04T12:30:15
   Files processed: 1
✅ JSON validation passed

📁 Checking Processed file: tiny.pwiz.1.1.mzML...
✅ Processed file: tiny.pwiz.1.1.mzML: -rw-r--r-- 1 root root 25K Dec  4 12:30 /var/...

======================================================================
VALIDATION SUMMARY
======================================================================
browser_test: ✅ PASS
marker_file: ✅ PASS
json_export: ✅ PASS
processed_file: ✅ PASS

Result: 4/4 checks passed

🎉 ALL VALIDATION CHECKS PASSED!
```

### Failed Test

```
======================================================================
VALIDATION SUMMARY
======================================================================
browser_test: ✅ PASS
marker_file: ❌ FAIL
json_export: ✅ PASS
processed_file: ❌ FAIL

Result: 2/4 checks passed

⚠️ SOME VALIDATION CHECKS FAILED
```

## Helper Classes

### BrowserHelper

Browser automation using Playwright:

```python
from helpers.browser import BrowserHelper

with BrowserHelper(headless=False) as browser:
    browser.navigate_to_site()
    browser.select_module("proteomics")
    browser.select_file("test.mzML")
    browser.switch_to_tab("Обработка")
    browser.click_button("Запустить обработку")
    browser.wait_for_processing(max_wait=600)
```

**Methods:**
- `navigate_to_site()` - Open base URL
- `select_module(module_name)` - Click module in sidebar
- `select_file(file_name)` - Click file radio button
- `switch_to_tab(tab_name)` - Switch between tabs
- `click_button(button_text)` - Click button by text
- `wait_for_processing(max_wait, check_interval)` - Wait for completion

### ValidationHelper

Server-side validation using SSH:

```python
from helpers.validation import ValidationHelper

validator = ValidationHelper()

# Check file exists
validator.check_file_exists("/tmp/marker.txt", "Marker file")

# Read JSON and validate
validator.validate_json_export(
    "/var/OmicsIntegrationSuite/data/proteomics/results/proteomics_results.json",
    expected_module="proteomics"
)

# Print summary
results = {
    "marker_file": True,
    "json_export": True,
    "processed_file": False
}
validator.print_validation_summary(results)
```

**Methods:**
- `check_file_exists(file_path, file_type)` - Verify file exists on server
- `read_file_content(file_path, preview_lines)` - Read file via SSH
- `read_json_file(file_path)` - Parse JSON file from server
- `validate_marker_file(marker_path)` - Check marker file
- `validate_json_export(json_path, expected_module)` - Validate JSON structure
- `print_validation_summary(results)` - Pretty-print test results

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed

Use exit codes for CI/CD integration:

```bash
python run_focused_test.py all --headless
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

## Troubleshooting

### Browser not found

```bash
# Install Playwright browsers
playwright install chromium
```

### SSH connection failed

```bash
# Check SSH key permissions
chmod 600 "C:\.ssh\id_rsa"

# Test connection
ssh -i "C:\.ssh\id_rsa" root@omicsintegrationsuite.onff.ru "echo OK"
```

### Processing timeout

Increase timeout in command or config:

```bash
# Command line
python run_focused_test.py proteomics --timeout 1200

# Or edit config.yaml
global:
  default_timeout: 1200
```

### Button not found

Check button text in `browser.py`:
- "Запустить обработку" (Start Processing)
- "Обработка" (Processing tab)

UI text may have changed - update accordingly.

## Development

### Adding New Module Test

1. Create `modules/new_module.py`:

```python
from ..helpers.browser import BrowserHelper
from ..helpers.validation import ValidationHelper

class NewModuleTest:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.module_name = "new_module"

    def run_test(self, file_name: str, timeout: int = 600):
        # Browser automation
        with BrowserHelper(headless=self.headless) as browser:
            browser.navigate_to_site()
            browser.select_module("new_module")
            # ... test logic

        # Server validation
        validator = ValidationHelper()
        results = {
            "marker_file": validator.validate_marker_file("/tmp/new_module_marker.txt"),
            "json_export": validator.validate_json_export("/path/to/results.json", "new_module")
        }

        return results
```

2. Add to `modules/__init__.py`:

```python
from .new_module import NewModuleTest
__all__ = ['ProteomicsTest', 'MiRNATest', 'GenomicsTest', 'NewModuleTest']
```

3. Update `run_focused_test.py` to include new module

4. Add configuration to `config.yaml`

## Test Files

### Proteomics (mzML)

Official HUPO-PSI test files from https://github.com/HUPO-PSI/mzML:

- **tiny.pwiz.1.1.mzML** (25KB) - mzML v1.1 standard test file
- **tiny4_LTQ-FT.mzML** (39KB) - Real LTQ-FT instrument data
- **demo_pride_example.mzML** (43KB) - PRIDE repository example

Located on server: `/var/OmicsIntegrationSuite/data/proteomics/uploaded_files/`

### miRNA

To be populated with official test files.

### Genomics

To be populated with official test files.

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install playwright pyyaml
          playwright install chromium

      - name: Run E2E tests
        env:
          SSH_KEY: ${{ secrets.SSH_KEY }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          cd tools/e2e_testing
          python run_focused_test.py all --headless
```

## License

Part of OmicsIntegrationSuite project.

## Contact

For issues or questions, contact the development team.
