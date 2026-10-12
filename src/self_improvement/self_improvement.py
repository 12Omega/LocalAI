"""Self-improvement engine for Local AI Development Environment.

This module provides the SelfImprovementEngine class that enables the system
to analyze, propose, implement, test, and revert improvements to its own code.
It maintains safety mechanisms including backups, metric tracking, and automatic
rollback if improvements degrade effectiveness.

Requirements implemented:
- 4.1: Analyze the system's own codebase to identify improvement opportunities
- 4.2: Propose specific changes when improvement opportunities are identified
- 4.3: Implement approved improvements to system capabilities
- 4.4: Test improvements before finalizing them
- 4.5: Revert changes that reduce system effectiveness
- 4.6: Maintain a log of all self-modifications
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..core.models import (
    ImprovementOpportunity,
    ImprovementProposal,
    TestMetrics,
    SelfModificationLog,
    ImplementationResult
)
from ..agents.file_operations import FileOperations, OperationResult
from ..agents.command_executor import CommandExecutor


class SelfImprovementEngine:
    """Enables the system to improve its own capabilities autonomously.
    
    This class provides methods for analyzing system code, proposing improvements,
    implementing changes, testing them, and rolling back if effectiveness degrades.
    All self-modifications are logged for transparency and auditability.
    """
    
    def __init__(
        self,
        system_root: str,
        file_ops: Optional[FileOperations] = None,
        command_executor: Optional[CommandExecutor] = None,
        log_path: Optional[str] = None
    ):
        """Initialize SelfImprovementEngine.
        
        Args:
            system_root: Root directory of the system codebase
            file_ops: FileOperations instance (creates new if None)
            command_executor: CommandExecutor instance (creates new if None)
            log_path: Path to self-modification log file (default: system_root/.self_improvement_log.json)
        """
        self.system_root = Path(system_root)
        self.file_ops = file_ops or FileOperations(system_root)
        self.command_executor = command_executor or CommandExecutor()
        self.log_path = Path(log_path) if log_path else self.system_root / ".self_improvement_log.json"
        self.backup_dir = self.system_root / ".self_improvement_backups"
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load or initialize modification log
        self._modification_log: List[SelfModificationLog] = self._load_log()
    
    def analyze_system(self) -> List[ImprovementOpportunity]:
        """Analyze the system's own codebase to identify improvement opportunities.
        
        This method scans the system codebase looking for potential improvements
        in categories: code_quality, new_capability, performance, and reliability.
        
        Returns:
            List of identified improvement opportunities
            
        Requirements: 4.1
        """
        opportunities = []
        
        # Scan all Python files in src directory
        src_dir = self.system_root / "src"
        if not src_dir.exists():
            return opportunities
        
        for py_file in src_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            # Read file content
            content_result = self.file_ops.read_file(str(py_file))
            if not content_result[1].success:
                continue
            
            content = content_result[0]
            if not content:
                continue
            
            # Analyze for improvement opportunities
            opportunities.extend(self._analyze_code_quality(str(py_file), content))
            opportunities.extend(self._analyze_performance(str(py_file), content))
            opportunities.extend(self._analyze_reliability(str(py_file), content))
        
        return opportunities
    
    def propose_improvement(self, opportunity: ImprovementOpportunity) -> ImprovementProposal:
        """Generate specific code changes for an improvement opportunity.
        
        Args:
            opportunity: The improvement opportunity to address
            
        Returns:
            Detailed proposal with specific code changes
            
        Requirements: 4.2
        """
        # For now, create a proposal structure that would be filled by LLM integration
        # This is a placeholder that demonstrates the interface
        
        changes = {}
        for file_path in opportunity.affected_files:
            # In a full implementation, this would use the LLM to generate
            # the improved code. For now, we prepare the structure.
            content_result = self.file_ops.read_file(file_path)
            if content_result[1].success and content_result[0]:
                # Placeholder: actual improvement would be LLM-generated
                changes[file_path] = content_result[0]
        
        rationale = f"Addressing {opportunity.category} issue: {opportunity.description}"
        
        test_plan = "Run full test suite (pytest) to ensure no regressions"
        
        rollback_plan = "Restore from backup if metrics degrade"
        
        return ImprovementProposal(
            opportunity=opportunity,
            changes=changes,
            rationale=rationale,
            test_plan=test_plan,
            rollback_plan=rollback_plan
        )
    
    def implement_improvement(self, proposal: ImprovementProposal) -> ImplementationResult:
        """Apply proposed changes to system code with backup.
        
        This method creates a backup of all affected files before applying changes,
        ensuring safe rollback if needed.
        
        Args:
            proposal: The improvement proposal to implement
            
        Returns:
            Result indicating success/failure and backup location
            
        Requirements: 4.3
        """
        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        files_modified = []
        
        try:
            # Step 1: Create backups
            for file_path in proposal.changes.keys():
                source = Path(file_path)
                if not source.exists():
                    continue
                
                # Create backup preserving directory structure
                relative_path = source.relative_to(self.system_root)
                backup_file = backup_path / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(source, backup_file)
            
            # Step 2: Apply changes
            for file_path, new_content in proposal.changes.items():
                result = self.file_ops.update_file(file_path, new_content)
                if not result.success:
                    # Rollback on first failure
                    self._restore_from_backup(backup_path, files_modified)
                    return ImplementationResult(
                        success=False,
                        files_modified=[],
                        backup_path=str(backup_path),
                        error_message=f"Failed to update {file_path}: {result.message}"
                    )
                files_modified.append(file_path)
            
            return ImplementationResult(
                success=True,
                files_modified=files_modified,
                backup_path=str(backup_path)
            )
            
        except Exception as e:
            # Rollback on any exception
            self._restore_from_backup(backup_path, files_modified)
            return ImplementationResult(
                success=False,
                files_modified=[],
                backup_path=str(backup_path),
                error_message=f"Exception during implementation: {str(e)}"
            )
    
    def test_improvement(self) -> TestMetrics:
        """Run tests to verify improvement works correctly.
        
        Executes the system's test suite and measures effectiveness metrics.
        
        Returns:
            Test metrics including success rate and error rate
            
        Requirements: 4.4
        """
        # Run pytest on the tests directory
        test_dir = self.system_root / "tests"
        if not test_dir.exists():
            return TestMetrics(
                total_tests=0,
                tests_passed=0,
                tests_failed=0,
                success_rate=0.0,
                error_rate=0.0,
                execution_time=0.0
            )
        
        # Execute pytest with JSON report
        start_time = datetime.now()
        result = self.command_executor.execute(
            "pytest --tb=short -v",
            cwd=str(self.system_root),
            timeout=300  # 5 minute timeout for tests
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Parse pytest output to extract metrics
        metrics = self._parse_test_results(result.stdout)
        metrics.execution_time = execution_time
        
        return metrics
    
    def revert_improvement(self, proposal: ImprovementProposal, backup_path: str) -> OperationResult:
        """Rollback an improvement that reduced effectiveness.
        
        Restores all modified files from the backup created during implementation.
        
        Args:
            proposal: The proposal to revert
            backup_path: Path to backup directory
            
        Returns:
            Result indicating success/failure of rollback
            
        Requirements: 4.5
        """
        backup = Path(backup_path)
        if not backup.exists():
            return OperationResult(
                success=False,
                message=f"Backup not found at {backup_path}",
                error_type="not_found"
            )
        
        try:
            restored_count = self._restore_from_backup(backup, proposal.changes.keys())
            
            return OperationResult(
                success=True,
                message=f"Successfully reverted {restored_count} files from backup",
                data={"restored_count": restored_count}
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to revert improvement: {str(e)}",
                error_type="revert_failed"
            )
    
    def log_modification(
        self,
        proposal: ImprovementProposal,
        files_modified: List[str],
        metrics_before: TestMetrics,
        metrics_after: TestMetrics,
        reverted: bool = False,
        revert_reason: Optional[str] = None
    ) -> None:
        """Record a self-modification in the audit log.
        
        Args:
            proposal: The improvement proposal that was implemented
            files_modified: List of files that were modified
            metrics_before: Test metrics before the change
            metrics_after: Test metrics after the change
            reverted: Whether the change was reverted
            revert_reason: Reason for reversion if applicable
            
        Requirements: 4.6
        """
        log_entry = SelfModificationLog(
            timestamp=datetime.now(),
            category=proposal.opportunity.category,
            description=proposal.opportunity.description,
            files_modified=files_modified,
            test_results_before=metrics_before,
            test_results_after=metrics_after,
            reverted=reverted,
            revert_reason=revert_reason
        )
        
        self._modification_log.append(log_entry)
        self._save_log()
    
    def get_modification_history(self) -> List[SelfModificationLog]:
        """Get the complete history of self-modifications.
        
        Returns:
            List of all self-modification log entries
        """
        return self._modification_log.copy()
    
    def should_rollback(self, metrics_before: TestMetrics, metrics_after: TestMetrics) -> tuple[bool, Optional[str]]:
        """Determine if an improvement should be rolled back based on metrics.
        
        Args:
            metrics_before: Test metrics before the improvement
            metrics_after: Test metrics after the improvement
            
        Returns:
            Tuple of (should_rollback, reason)
        """
        # Rollback if new test failures introduced (and none existed before)
        # Check this first as it's more specific than general success rate decrease
        if metrics_before.tests_failed == 0 and metrics_after.tests_failed > 0:
            reason = f"Introduced {metrics_after.tests_failed} new test failures"
            return True, reason
        
        # Rollback if success rate decreased
        if metrics_after.success_rate < metrics_before.success_rate:
            reason = (
                f"Success rate decreased from {metrics_before.success_rate:.1f}% "
                f"to {metrics_after.success_rate:.1f}%"
            )
            return True, reason
        
        # Rollback if error rate increased significantly (>5% increase)
        if metrics_after.error_rate > metrics_before.error_rate + 5.0:
            reason = (
                f"Error rate increased significantly from {metrics_before.error_rate:.1f}% "
                f"to {metrics_after.error_rate:.1f}%"
            )
            return True, reason
        
        return False, None
    
    # Private helper methods
    
    def _analyze_code_quality(self, file_path: str, content: str) -> List[ImprovementOpportunity]:
        """Analyze code for quality improvement opportunities."""
        opportunities = []
        
        lines = content.split('\n')
        
        # Check for functions/methods missing docstrings
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def '):
                # Check if next non-empty line is a docstring
                next_line_idx = i + 1
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1
                
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        # Function missing docstring
                        func_name = stripped.split('(')[0].replace('def ', '').strip()
                        opportunities.append(ImprovementOpportunity(
                            category="code_quality",
                            description=f"Function '{func_name}' missing docstring in {file_path}",
                            affected_files=[file_path],
                            severity="low",
                            potential_impact="Improved code documentation and maintainability"
                        ))
        
        # Check for long functions (>100 lines)
        function_starts = [i for i, line in enumerate(lines) if line.strip().startswith('def ')]
        for start in function_starts:
            # Find next function or end of file
            next_starts = [s for s in function_starts if s > start]
            end = next_starts[0] if next_starts else len(lines)
            if end - start > 100:
                opportunities.append(ImprovementOpportunity(
                    category="code_quality",
                    description=f"Long function in {file_path} at line {start + 1}",
                    affected_files=[file_path],
                    severity="medium",
                    potential_impact="Better code organization and readability"
                ))
        
        # Check for bare except clauses
        if 'except:' in content:
            opportunities.append(ImprovementOpportunity(
                category="code_quality",
                description=f"Bare except clause in {file_path}",
                affected_files=[file_path],
                severity="medium",
                potential_impact="Better error handling specificity"
            ))
        
        return opportunities
    
    def _analyze_performance(self, file_path: str, content: str) -> List[ImprovementOpportunity]:
        """Analyze code for performance improvement opportunities."""
        opportunities = []
        
        # Check for repeated file reads in loops
        if 'for ' in content and 'read_file' in content:
            # Simple heuristic: if both appear, might be reading in loop
            opportunities.append(ImprovementOpportunity(
                category="performance",
                description=f"Potential repeated file reads in {file_path}",
                affected_files=[file_path],
                severity="low",
                potential_impact="Reduced I/O operations and better performance"
            ))
        
        return opportunities
    
    def _analyze_reliability(self, file_path: str, content: str) -> List[ImprovementOpportunity]:
        """Analyze code for reliability improvement opportunities."""
        opportunities = []
        
        # Check for missing error handling
        if 'def ' in content and 'try:' not in content:
            # Functions without any try/except might need error handling
            opportunities.append(ImprovementOpportunity(
                category="reliability",
                description=f"Missing error handling in {file_path}",
                affected_files=[file_path],
                severity="medium",
                potential_impact="Better error recovery and system stability"
            ))
        
        return opportunities
    
    def _restore_from_backup(self, backup_path: Path, files_to_restore) -> int:
        """Restore files from backup directory.
        
        Args:
            backup_path: Path to backup directory
            files_to_restore: Iterable of file paths to restore
            
        Returns:
            Number of files successfully restored
        """
        restored_count = 0
        
        for file_path in files_to_restore:
            source = Path(file_path)
            relative_path = source.relative_to(self.system_root)
            backup_file = backup_path / relative_path
            
            if backup_file.exists():
                shutil.copy2(backup_file, source)
                restored_count += 1
        
        return restored_count
    
    def _parse_test_results(self, pytest_output: str) -> TestMetrics:
        """Parse pytest output to extract test metrics.
        
        Args:
            pytest_output: Standard output from pytest execution
            
        Returns:
            TestMetrics with parsed values
        """
        # Default metrics
        total_tests = 0
        tests_passed = 0
        tests_failed = 0
        
        # Parse pytest summary line (e.g., "13 passed, 2 failed in 2.45s")
        for line in pytest_output.split('\n'):
            line = line.strip()
            
            # Look for the summary line with "passed" or "failed"
            if ('passed' in line or 'failed' in line) and ' in ' in line:
                # This is likely the summary line
                parts = line.split()
                
                i = 0
                while i < len(parts):
                    try:
                        # Try to parse number followed by status word
                        num = int(parts[i])
                        if i + 1 < len(parts):
                            if parts[i + 1].startswith('passed'):
                                tests_passed = num
                            elif parts[i + 1].startswith('failed'):
                                tests_failed = num
                        i += 1
                    except ValueError:
                        i += 1
        
        total_tests = tests_passed + tests_failed
        success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0.0
        error_rate = (tests_failed / total_tests * 100) if total_tests > 0 else 0.0
        
        return TestMetrics(
            total_tests=total_tests,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            success_rate=success_rate,
            error_rate=error_rate,
            execution_time=0.0  # Will be set by caller
        )
    
    def _load_log(self) -> List[SelfModificationLog]:
        """Load modification log from disk."""
        if not self.log_path.exists():
            return []
        
        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)
                return [self._dict_to_log_entry(entry) for entry in data]
        except Exception:
            return []
    
    def _save_log(self) -> None:
        """Save modification log to disk."""
        try:
            with open(self.log_path, 'w') as f:
                data = [self._log_entry_to_dict(entry) for entry in self._modification_log]
                json.dump(data, f, indent=2)
        except Exception:
            # If we can't save the log, continue anyway
            pass
    
    def _log_entry_to_dict(self, entry: SelfModificationLog) -> dict:
        """Convert log entry to dictionary for JSON serialization."""
        return {
            "timestamp": entry.timestamp.isoformat(),
            "category": entry.category,
            "description": entry.description,
            "files_modified": entry.files_modified,
            "test_results_before": {
                "total_tests": entry.test_results_before.total_tests,
                "tests_passed": entry.test_results_before.tests_passed,
                "tests_failed": entry.test_results_before.tests_failed,
                "success_rate": entry.test_results_before.success_rate,
                "error_rate": entry.test_results_before.error_rate,
                "execution_time": entry.test_results_before.execution_time
            },
            "test_results_after": {
                "total_tests": entry.test_results_after.total_tests,
                "tests_passed": entry.test_results_after.tests_passed,
                "tests_failed": entry.test_results_after.tests_failed,
                "success_rate": entry.test_results_after.success_rate,
                "error_rate": entry.test_results_after.error_rate,
                "execution_time": entry.test_results_after.execution_time
            },
            "reverted": entry.reverted,
            "revert_reason": entry.revert_reason
        }
    
    def _dict_to_log_entry(self, data: dict) -> SelfModificationLog:
        """Convert dictionary to log entry from JSON deserialization."""
        return SelfModificationLog(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            category=data["category"],
            description=data["description"],
            files_modified=data["files_modified"],
            test_results_before=TestMetrics(**data["test_results_before"]),
            test_results_after=TestMetrics(**data["test_results_after"]),
            reverted=data["reverted"],
            revert_reason=data.get("revert_reason")
        )
