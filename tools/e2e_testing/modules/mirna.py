"""
miRNA Module E2E Test
End-to-end testing for miRNA module using browser automation and server validation
"""

from typing import Dict, List, Optional
import time
from ..helpers.browser import BrowserHelper
from ..helpers.validation import ValidationHelper


class MiRNATest:
    """End-to-end test for miRNA module"""

    def __init__(self, headless: bool = False):
        """
        Initialize miRNA test

        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.module_name = "mirna"
        self.results = {}

    def run_test(self, file_name: str, timeout: int = 600) -> Dict[str, bool]:
        """
        Run complete E2E test for miRNA module

        Args:
            file_name: Name of the miRNA file to test (FASTA or other format)
            timeout: Maximum wait time for processing (seconds)

        Returns:
            Dictionary of test results {check_name: passed}
        """
        print("\n" + "=" * 70)
        print(f"miRNA E2E TEST: {file_name}")
        print("=" * 70)

        # Phase 1: Browser automation
        print("\n📍 PHASE 1: Browser Automation")
        browser_success = self._run_browser_test(file_name, timeout)

        if not browser_success:
            print("\n❌ Browser test failed, skipping validation")
            return {"browser_test": False}

        # Phase 2: Server-side validation
        print("\n📍 PHASE 2: Server Validation")
        validation_results = self._run_validation(file_name)

        # Combine results
        all_results = {
            "browser_test": browser_success,
            **validation_results
        }

        # Print summary
        validator = ValidationHelper()
        validator.print_validation_summary(all_results)

        return all_results

    def _run_browser_test(self, file_name: str, timeout: int) -> bool:
        """
        Run browser automation test

        Args:
            file_name: Name of file to select
            timeout: Maximum wait time

        Returns:
            True if browser test passed
        """
        try:
            with BrowserHelper(headless=self.headless) as browser:
                # Navigate to site
                browser.navigate_to_site()

                # Select miRNA module
                browser.select_module("mirna")

                # Select file
                if not browser.select_file(file_name):
                    print("❌ Failed to select file")
                    return False

                # Switch to processing tab
                if not browser.switch_to_tab("⚙️ Обработка"):
                    print("❌ Failed to switch to processing tab")
                    return False

                # Click processing button
                if not browser.click_button("🚀 Начать обработку"):
                    print("❌ Failed to click processing button")
                    return False

                # Wait for processing to complete
                print(f"\n⏳ Waiting for processing (max {timeout}s)...")
                if not browser.wait_for_processing(max_wait=timeout):
                    print("⚠️ Processing timeout - continuing to validation")

                # Give server time to write files
                time.sleep(5)

                print("\n✅ Browser test completed")
                return True

        except Exception as e:
            print(f"\n❌ Browser test error: {e}")
            return False

    def _run_validation(self, file_name: str) -> Dict[str, bool]:
        """
        Run server-side validation

        Args:
            file_name: Name of file that was processed

        Returns:
            Dictionary of validation results
        """
        validator = ValidationHelper()
        results = {}

        # Check marker file
        marker_path = "/tmp/mirna_processing_started.txt"
        results["marker_file"] = validator.validate_marker_file(marker_path)

        # Check JSON export
        json_path = "/var/OmicsIntegrationSuite/data/validation_json/mirna_latest_results.json"
        results["json_export"] = validator.validate_json_export(json_path, "mirna")

        # Check processed file exists
        processed_file = f"/var/OmicsIntegrationSuite/data/mirna/processed/{file_name}"
        results["processed_file"] = validator.check_file_exists(
            processed_file,
            f"Processed file: {file_name}"
        )

        return results

    def test_all_files(self, file_list: Optional[List[str]] = None, timeout: int = 600) -> Dict[str, Dict[str, bool]]:
        """
        Test multiple files sequentially

        Args:
            file_list: List of file names to test. If None, use default test files
            timeout: Maximum wait time per file

        Returns:
            Dictionary mapping file_name -> test_results
        """
        if file_list is None:
            # Default miRNA test files (update with actual test files)
            file_list = [
                "test_mirna_sample.fasta",
            ]

        all_results = {}

        for file_name in file_list:
            print(f"\n{'=' * 70}")
            print(f"Testing file {len(all_results) + 1}/{len(file_list)}: {file_name}")
            print('=' * 70)

            results = self.run_test(file_name, timeout)
            all_results[file_name] = results

            # Brief pause between tests
            if file_name != file_list[-1]:
                print("\n⏸️ Pausing 10 seconds before next test...")
                time.sleep(10)

        # Print overall summary
        self._print_overall_summary(all_results)

        return all_results

    def _print_overall_summary(self, all_results: Dict[str, Dict[str, bool]]):
        """Print summary of all tests"""
        print("\n" + "=" * 70)
        print("OVERALL TEST SUMMARY - miRNA MODULE")
        print("=" * 70)

        total_files = len(all_results)
        total_checks = sum(len(results) for results in all_results.values())
        passed_checks = sum(sum(results.values()) for results in all_results.values())

        print(f"\nFiles tested: {total_files}")
        print(f"Total checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")

        for file_name, results in all_results.items():
            file_passed = all(results.values())
            status = "✅ PASS" if file_passed else "❌ FAIL"
            print(f"\n{file_name}: {status}")
            for check, passed in results.items():
                check_status = "✅" if passed else "❌"
                print(f"  {check_status} {check}")

        all_passed = passed_checks == total_checks
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️ {total_checks - passed_checks} CHECKS FAILED")


if __name__ == "__main__":
    """Run miRNA test when executed directly"""
    import sys

    # Parse command line arguments
    headless = "--headless" in sys.argv
    file_name = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None

    test = MiRNATest(headless=headless)

    if file_name:
        # Test single file
        results = test.run_test(file_name)
        sys.exit(0 if all(results.values()) else 1)
    else:
        # Test all default files
        all_results = test.test_all_files()

        # Exit with error if any test failed
        all_passed = all(
            all(results.values())
            for results in all_results.values()
        )
        sys.exit(0 if all_passed else 1)
