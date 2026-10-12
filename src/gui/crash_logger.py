"""
Crash Logger Module

Implements crash logging functionality to capture and save unhandled exceptions
before the application exits.

Requirements implemented:
- 10.6: Log error details to file before exit on unexpected crash
"""

import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from .platform_paths import PlatformPaths


class CrashLogger:
    """
    Handles logging of critical errors and crashes.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize crash logger.
        
        Args:
            log_dir: Directory to store crash logs (default: platform-appropriate log directory)
        
        Requirements: 15.7
        """
        if log_dir is None:
            # Use platform-appropriate log directory
            log_dir = PlatformPaths.get_log_dir()
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('crash_logger')
        self.logger.setLevel(logging.ERROR)
        
        # Setup crash log file handler
        self.crash_log_path = self.log_dir / 'crash.log'
        handler = logging.FileHandler(self.crash_log_path, encoding='utf-8')
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_crash(self, exc_type, exc_value, exc_traceback):
        """
        Log a crash with full traceback.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if exc_type is KeyboardInterrupt:
            # Don't log keyboard interrupts as crashes
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        timestamp = datetime.now().isoformat()
        
        # Format crash report
        crash_report = []
        crash_report.append("="*80)
        crash_report.append(f"CRASH REPORT - {timestamp}")
        crash_report.append("="*80)
        crash_report.append("")
        crash_report.append(f"Exception Type: {exc_type.__name__}")
        crash_report.append(f"Exception Message: {exc_value}")
        crash_report.append("")
        crash_report.append("Traceback:")
        crash_report.append("-"*80)
        
        # Add formatted traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        crash_report.extend(tb_lines)
        
        crash_report.append("-"*80)
        crash_report.append("")
        crash_report.append("System Information:")
        crash_report.append(f"  Platform: {sys.platform}")
        crash_report.append(f"  Python Version: {sys.version}")
        crash_report.append("")
        crash_report.append("="*80)
        crash_report.append("")
        
        # Write to crash log file
        crash_text = '\n'.join(crash_report)
        
        try:
            with open(self.crash_log_path, 'a', encoding='utf-8') as f:
                f.write(crash_text)
            
            # Also write to individual crash file
            crash_file = self.log_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(crash_text)
            
            self.logger.error(f"Crash logged to: {crash_file}")
            
            # Print to stderr
            print(f"\n{'='*80}", file=sys.stderr)
            print("CRITICAL ERROR: Application crashed", file=sys.stderr)
            print(f"Crash log saved to: {crash_file}", file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)
            
        except Exception as e:
            # Last resort: print to stderr
            print(f"Failed to write crash log: {e}", file=sys.stderr)
            print(crash_text, file=sys.stderr)
        
        # Call original excepthook
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def install(self):
        """
        Install this crash logger as the global exception hook.
        """
        sys.excepthook = self.log_crash
        self.logger.info(f"Crash logger installed. Logs will be saved to: {self.log_dir}")
    
    def get_recent_crashes(self, limit: int = 10):
        """
        Get list of recent crash log files.
        
        Args:
            limit: Maximum number of crash files to return
            
        Returns:
            List of crash log file paths, sorted by most recent first
        """
        crash_files = sorted(
            self.log_dir.glob('crash_*.log'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return crash_files[:limit]
    
    def clear_old_crashes(self, keep_days: int = 30):
        """
        Remove crash logs older than specified days.
        
        Args:
            keep_days: Number of days to keep crash logs
        """
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        removed_count = 0
        for crash_file in self.log_dir.glob('crash_*.log'):
            if crash_file.stat().st_mtime < cutoff_time:
                try:
                    crash_file.unlink()
                    removed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to remove old crash log {crash_file}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} old crash logs")


# Global crash logger instance
_crash_logger: Optional[CrashLogger] = None


def install_crash_logger(log_dir: Optional[Path] = None) -> CrashLogger:
    """
    Install global crash logger.
    
    Args:
        log_dir: Optional custom log directory
        
    Returns:
        CrashLogger instance
    """
    global _crash_logger
    
    if _crash_logger is None:
        _crash_logger = CrashLogger(log_dir)
        _crash_logger.install()
    
    return _crash_logger


def get_crash_logger() -> Optional[CrashLogger]:
    """
    Get the global crash logger instance.
    
    Returns:
        CrashLogger instance or None if not installed
    """
    return _crash_logger

