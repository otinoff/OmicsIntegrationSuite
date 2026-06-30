"""
Server Validation Helpers
Functions to check files and results on the production server
"""

import subprocess
from typing import Optional, Dict, Any
import json


class ValidationHelper:
    """Helper class for server-side validation via SSH"""

    def __init__(self, ssh_key: str = "C:\\.ssh\\id_rsa",
                 server: str = "root@omicsintegrationsuite.onff.ru"):
        self.ssh_key = ssh_key
        self.server = server

    def _run_ssh_command(self, command: str, timeout: int = 10) -> tuple[bool, str]:
        """
        Run SSH command on server

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success: bool, output: str)
        """
        cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-i', self.ssh_key,
               self.server, command]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return (result.returncode == 0, result.stdout.strip())
        except subprocess.TimeoutExpired:
            return (False, f"Command timed out after {timeout}s")
        except Exception as e:
            return (False, str(e))

    def check_file_exists(self, file_path: str, file_type: str = "file") -> bool:
        """
        Check if a file exists on the server

        Args:
            file_path: Path to the file on server
            file_type: Type description (for logging)

        Returns:
            True if file exists
        """
        print(f"\n📁 Checking {file_type}...")
        success, output = self._run_ssh_command(f'ls -lh {file_path} 2>&1')

        if success:
            print(f"✅ {file_type}: {output}")
            return True
        else:
            print(f"❌ {file_type} not found: {file_path}")
            return False

    def read_file_content(self, file_path: str, preview_lines: int = 20) -> Optional[str]:
        """
        Read file content from server

        Args:
            file_path: Path to file
            preview_lines: Number of lines to read

        Returns:
            File content or None if failed
        """
        print(f"\n📄 Reading file content ({preview_lines} lines)...")
        success, output = self._run_ssh_command(f'head -n {preview_lines} {file_path} 2>&1')

        if success:
            print(output)
            return output
        else:
            print(f"❌ Failed to read file: {output}")
            return None

    def read_json_file(self, file_path: str) -> Optional[Dict[Any, Any]]:
        """
        Read and parse JSON file from server

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON dict or None if failed
        """
        print(f"\n📊 Reading JSON file: {file_path}...")
        success, output = self._run_ssh_command(f'cat {file_path} 2>&1')

        if success:
            try:
                data = json.loads(output)
                print(f"✅ JSON parsed successfully")
                print(f"   Module: {data.get('module', 'N/A')}")
                print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                print(f"   Files processed: {data.get('files_processed', 'N/A')}")
                return data
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                return None
        else:
            print(f"❌ Failed to read JSON: {output}")
            return None

    def validate_marker_file(self, marker_path: str) -> bool:
        """
        Validate marker file (used to confirm processing started)

        Args:
            marker_path: Path to marker file

        Returns:
            True if marker file exists and valid
        """
        if not self.check_file_exists(marker_path, "Marker file"):
            return False

        content = self.read_file_content(marker_path, preview_lines=5)
        return content is not None

    def validate_json_export(self, json_path: str, expected_module: str) -> bool:
        """
        Validate JSON export file

        Args:
            json_path: Path to JSON file
            expected_module: Expected module name

        Returns:
            True if JSON is valid
        """
        if not self.check_file_exists(json_path, "JSON export"):
            return False

        data = self.read_json_file(json_path)
        if data is None:
            return False

        # Validate structure
        if data.get('module') != expected_module:
            print(f"⚠️ Module mismatch: expected '{expected_module}', got '{data.get('module')}'")
            return False

        if 'timestamp' not in data:
            print("⚠️ Missing timestamp")
            return False

        if 'results' not in data:
            print("⚠️ Missing results")
            return False

        print("✅ JSON validation passed")
        return True

    def print_validation_summary(self, results: Dict[str, bool]):
        """
        Print validation summary

        Args:
            results: Dict of check_name -> pass/fail
        """
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        for check_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check_name}: {status}")

        all_passed = all(results.values())
        total = len(results)
        passed_count = sum(results.values())

        print(f"\nResult: {passed_count}/{total} checks passed")

        if all_passed:
            print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        else:
            print("\n⚠️ SOME VALIDATION CHECKS FAILED")

        return all_passed
