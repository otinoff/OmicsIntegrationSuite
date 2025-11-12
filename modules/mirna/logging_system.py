"""
Unified Logging System for Genomics Quality Control
Provides consistent logging with visual markers across all QC operations

Integrated from QualityControlSuite (https://github.com/otinoff/QualityControlSuite)
"""

import sys
import logging
from datetime import datetime
from typing import Optional


class QCLogger:
    """
    Unified logger with visual markers for quality control operations.

    Markers:
        [CHECK]   - Checking dependencies or conditions
        [INSTALL] - Installing packages or dependencies
        [OK]      - Successful operations
        [ERROR]   - Error conditions
        [WARNING] - Warning conditions
        [INFO]    - Informational messages
        [ANALYZE] - Starting analysis operations
        [RUNNING] - Running analysis processes
        [DEBUG]   - Debug information
        [METRICS] - Displaying metrics
        [HTML]    - HTML report generation
        [JSON]    - JSON report generation
        [SUMMARY] - Summary information
        [FAIL]    - Failed operations
    """

    def __init__(self, verbose: bool = True, use_colors: bool = True):
        """
        Initialize QC Logger.

        Args:
            verbose: Enable verbose output
            use_colors: Use ANSI color codes (disable for Windows CMD)
        """
        self.verbose = verbose
        self.use_colors = use_colors and sys.platform != 'win32'

        # ANSI color codes
        self.colors = {
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'BLUE': '\033[94m',
            'CYAN': '\033[96m',
            'MAGENTA': '\033[95m',
            'RESET': '\033[0m',
            'BOLD': '\033[1m'
        } if self.use_colors else {key: '' for key in [
            'GREEN', 'YELLOW', 'RED', 'BLUE', 'CYAN', 'MAGENTA', 'RESET', 'BOLD'
        ]}

    def _format_message(self, marker: str, message: str, color: str = '') -> str:
        """Format message with marker and optional color."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if color and self.use_colors:
            return f"{color}[{marker}]{self.colors['RESET']} {message}"
        return f"[{marker}] {message}"

    def _print(self, marker: str, message: str, color: str = '', level: int = logging.INFO):
        """Print formatted message."""
        if self.verbose or level >= logging.WARNING:
            formatted = self._format_message(marker, message, color)
            print(formatted)
            sys.stdout.flush()

    def check(self, message: str):
        """Log checking operation [CHECK]"""
        self._print("CHECK", message, self.colors['CYAN'])

    def install(self, message: str):
        """Log installation operation [INSTALL]"""
        self._print("INSTALL", message, self.colors['BLUE'])

    def ok(self, message: str):
        """Log successful operation [OK]"""
        self._print("OK", message, self.colors['GREEN'])

    def error(self, message: str):
        """Log error condition [ERROR]"""
        self._print("ERROR", message, self.colors['RED'], logging.ERROR)

    def warning(self, message: str):
        """Log warning condition [WARNING]"""
        self._print("WARNING", message, self.colors['YELLOW'], logging.WARNING)

    def info(self, message: str):
        """Log informational message [INFO]"""
        self._print("INFO", message)

    def analyze(self, message: str):
        """Log analysis start [ANALYZE]"""
        self._print("ANALYZE", message, self.colors['MAGENTA'])

    def running(self, message: str):
        """Log running process [RUNNING]"""
        self._print("RUNNING", message, self.colors['CYAN'])

    def debug(self, message: str):
        """Log debug information [DEBUG]"""
        if self.verbose:
            self._print("DEBUG", message, self.colors['CYAN'])

    def metrics(self, message: str):
        """Log metrics information [METRICS]"""
        self._print("METRICS", message, self.colors['GREEN'])

    def html(self, message: str):
        """Log HTML report generation [HTML]"""
        self._print("HTML", message, self.colors['BLUE'])

    def json(self, message: str):
        """Log JSON report generation [JSON]"""
        self._print("JSON", message, self.colors['BLUE'])

    def summary(self, message: str):
        """Log summary information [SUMMARY]"""
        self._print("SUMMARY", message, self.colors['BOLD'])

    def fail(self, message: str):
        """Log failed operation [FAIL]"""
        self._print("FAIL", message, self.colors['RED'], logging.ERROR)

    def progress(self, current: int, total: int, description: str = "Progress"):
        """
        Display progress information.

        Args:
            current: Current progress value
            total: Total value
            description: Progress description
        """
        percentage = (current / total) * 100 if total > 0 else 0
        self.info(f"{description}: {current}/{total} ({percentage:.1f}%)")

    def separator(self, char: str = "=", length: int = 50):
        """Print separator line."""
        if self.verbose:
            print(char * length)
            sys.stdout.flush()

    def header(self, message: str):
        """Print header with separators."""
        if self.verbose:
            self.separator()
            print(f"{self.colors['BOLD']}{message}{self.colors['RESET']}")
            self.separator()
            sys.stdout.flush()


# Global logger instance
_global_logger: Optional[QCLogger] = None


def get_logger(verbose: bool = True, use_colors: bool = True) -> QCLogger:
    """
    Get or create global QC logger instance.

    Args:
        verbose: Enable verbose output
        use_colors: Use ANSI color codes

    Returns:
        QCLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = QCLogger(verbose=verbose, use_colors=use_colors)
    return _global_logger


def set_verbose(verbose: bool):
    """Set verbose mode for global logger."""
    global _global_logger
    if _global_logger is not None:
        _global_logger.verbose = verbose


# Convenience functions for direct use
def check(message: str):
    """Log checking operation [CHECK]"""
    get_logger().check(message)


def install(message: str):
    """Log installation operation [INSTALL]"""
    get_logger().install(message)


def ok(message: str):
    """Log successful operation [OK]"""
    get_logger().ok(message)


def error(message: str):
    """Log error condition [ERROR]"""
    get_logger().error(message)


def warning(message: str):
    """Log warning condition [WARNING]"""
    get_logger().warning(message)


def info(message: str):
    """Log informational message [INFO]"""
    get_logger().info(message)


def analyze(message: str):
    """Log analysis start [ANALYZE]"""
    get_logger().analyze(message)


def running(message: str):
    """Log running process [RUNNING]"""
    get_logger().running(message)


def debug(message: str):
    """Log debug information [DEBUG]"""
    get_logger().debug(message)


def metrics(message: str):
    """Log metrics information [METRICS]"""
    get_logger().metrics(message)


def html(message: str):
    """Log HTML report generation [HTML]"""
    get_logger().html(message)


def json_report(message: str):
    """Log JSON report generation [JSON]"""
    get_logger().json(message)


def summary(message: str):
    """Log summary information [SUMMARY]"""
    get_logger().summary(message)


def fail(message: str):
    """Log failed operation [FAIL]"""
    get_logger().fail(message)


if __name__ == "__main__":
    # Demo usage
    logger = QCLogger(verbose=True, use_colors=True)

    logger.header("QC Logging System Demo")
    logger.check("Checking dependencies...")
    logger.install("Installing Sequali...")
    logger.ok("Sequali installed successfully!")
    logger.info("Starting quality control analysis")
    logger.analyze("Analyzing sample.fastq")
    logger.running("Running Sequali engine...")
    logger.debug("Processing 10000 reads")
    logger.metrics("Q30: 85.2%")
    logger.html("Generated report.html")
    logger.json("Generated report.json")
    logger.progress(8500, 10000, "Reads processed")
    logger.warning("GC content slightly high (58%)")
    logger.error("Failed to process corrupted read")
    logger.summary("Analysis complete: 9999/10000 reads (99.99%)")
    logger.ok("Quality control complete!")
