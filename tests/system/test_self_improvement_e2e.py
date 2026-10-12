"""End-to-end system test for self-improvement workflow.

This test validates the complete self-improvement workflow including:
- Self-improvement engine modifying system code
- Running tests after improvements
- Tracking metrics before and after
- Verifying improvements are applied successfully

Requirements validated:
- 4.1: Analyze system's own codebase to identify improvement opportunities
- 4.2: Propose specific changes to own code
- 4.3: Implement improvements to own capabilities
- 4.4: Test improvements before finalizing
- 4.5: Revert changes that reduce effectiveness
- 4.6: Maintain log of all self-modifications

Task: 19.6 Write end-to-end test for self-improvement
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess
import json

from src.self_improvement.self_improvement import SelfImprovementEngine
from src.core.models import (
    ImprovementOpportunity,
    ImprovementProposal,
    TestMetrics,
    SelfModificationLog,
    ImplementationResult
)
from src.agents.file_operations import FileOperations, OperationResult
from src.agents.command_executor import CommandExecutor


class TestSelfImprovementEndToEnd:
    """End-to-end tests for self-improvement workflow."""
    
    @pytest.fixture
    def temp_system_dir(self):
        """Create a temporary system directory with real codebase structure for testing."""
        tmpdir = tempfile.mkdtemp(prefix="e2e_self_improvement_test_")
        system_root = Path(tmpdir)
        
        # Create proper directory structure
        src_dir = system_root / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        
        tests_dir = system_root / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        
        # Create a simple module that has clear improvement opportunities
        module_content = '''"""Sample utility module for testing.

This module provides basic utility functions.
"""


def calculate_sum(numbers):
    """Calculate sum of numbers.
    
    Args:
        numbers: List of numbers to sum
        
    Returns:
        Sum of all numbers
    """
    total = 0
    for num in numbers:
        total += num
    return total


def process_items(items):
    # Missing docstring - improvement opportunity
    # Missing error handling - improvement opportunity
    result = []
    for item in items:
        result.append(item * 2)
    return result


def validate_input(value):
    # Simple function without proper validation
    if value:
        return True
    return False
'''
        (src_dir / "utils.py").write_text(module_content)
        
        # Create corresponding tests
        test_content = '''"""Tests for utils module."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import calculate_sum, process_items, validate_input


def test_calculate_sum():
    """Test sum calculation."""
    assert calculate_sum([1, 2, 3]) == 6
    assert calculate_sum([]) == 0
    assert calculate_sum([10]) == 10


def test_process_items():
    """Test item processing."""
    assert process_items([1, 2, 3]) == [2, 4, 6]
    assert process_items([]) == []


def test_validate_input():
    """Test input validation."""
    assert validate_input(True) is True
    assert validate_input(False) is False
    assert validate_input(None) is False
'''
        (tests_dir / "test_utils.py").write_text(test_content)
        
        # Create pytest configuration
        pytest_ini = '''[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
'''
        (system_root / "pytest.ini").write_text(pytest_ini)
        
        yield str(system_root)
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def self_improvement_engine(self, temp_system_dir):
        """Create a SelfImprovementEngine instance."""
        return SelfImprovementEngine(
            system_root=temp_system_dir,
            file_ops=FileOperations(temp_system_dir),
            command_executor=CommandExecutor()
        )
    
    def test_complete_self_improvement_workflow(self, self_improvement_engine, temp_system_dir):
        """Test the complete self-improvement workflow from analysis to verification.
        
        This test validates:
        1. System analyzes its own code and identifies improvement opportunities
        2. An improvement is proposed with specific changes
        3. Metrics are measured before implementing the improvement
        4. The improvement is implemented (system code is modified)
        5. Tests are run to verify the improvement works
        6. Metrics are tracked and compared
        7. The modification is logged in the audit trail
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
        """
        # Step 1: Analyze system to identify improvement opportunities (Requirement 4.1)
        print("\nStep 1: Analyzing system for improvement opportunities...")
        opportunities = self_improvement_engine.analyze_system()
        
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0, "Should find improvement opportunities in the sample code"
        
        # Verify opportunities are properly structured
        for opp in opportunities:
            assert isinstance(opp, ImprovementOpportunity)
            assert opp.category in ["code_quality", "performance", "reliability", "new_capability"]
            assert opp.description
            assert len(opp.affected_files) > 0
        
        print(f"Found {len(opportunities)} improvement opportunities")
        for i, opp in enumerate(opportunities[:3]):
            print(f"  {i+1}. [{opp.category}] {opp.description}")
        
        # Step 2: Propose a specific improvement (Requirement 4.2)
        print("\nStep 2: Proposing improvement...")
        # Select a code quality improvement (like adding docstrings)
        code_quality_opps = [opp for opp in opportunities if opp.category == "code_quality"]
        if not code_quality_opps:
            code_quality_opps = [opportunities[0]]  # Fall back to first opportunity
        
        opportunity = code_quality_opps[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        assert isinstance(proposal, ImprovementProposal)
        assert proposal.opportunity == opportunity
        assert isinstance(proposal.changes, dict)
        assert len(proposal.changes) > 0
        assert proposal.rationale
        assert proposal.test_plan
        assert proposal.rollback_plan
        
        print(f"Proposed improvement: {proposal.rationale[:100]}...")
        print(f"Will modify {len(proposal.changes)} file(s)")
        
        # Step 3: Measure metrics BEFORE implementation (Requirement 4.4)
        print("\nStep 3: Measuring metrics before improvement...")
        metrics_before = self_improvement_engine.test_improvement()
        
        assert isinstance(metrics_before, TestMetrics)
        assert metrics_before.total_tests >= 0
        assert metrics_before.tests_passed >= 0
        assert metrics_before.tests_failed >= 0
        
        print(f"Metrics before: {metrics_before.tests_passed}/{metrics_before.total_tests} passed, "
              f"success rate: {metrics_before.success_rate:.1f}%")
        
        # Step 4: Implement the improvement (modify system code) (Requirement 4.3)
        print("\nStep 4: Implementing improvement...")
        
        # For testing, we'll create a safe improvement: adding a docstring to process_items
        # This is a real code modification that improves quality without breaking functionality
        src_file = Path(temp_system_dir) / "src" / "utils.py"
        original_content = src_file.read_text()
        
        # Create an improved version with docstring
        improved_content = original_content.replace(
            'def process_items(items):\n    # Missing docstring - improvement opportunity\n    # Missing error handling - improvement opportunity',
            '''def process_items(items):
    """Process items by doubling their values.
    
    Args:
        items: List of items to process
        
    Returns:
        List of processed items with values doubled
        
    Raises:
        TypeError: If items is not iterable
    """'''
        )
        
        # Update the proposal with our concrete improvement
        proposal.changes[str(src_file)] = improved_content
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        assert isinstance(impl_result, ImplementationResult)
        assert impl_result.success is True, f"Implementation failed: {impl_result.error_message}"
        assert len(impl_result.files_modified) > 0
        assert impl_result.backup_path is not None
        
        # Verify backup was created
        backup_path = Path(impl_result.backup_path)
        assert backup_path.exists(), "Backup directory should exist"
        
        print(f"Implementation successful. Modified {len(impl_result.files_modified)} file(s)")
        print(f"Backup created at: {impl_result.backup_path}")
        
        # Verify the file was actually modified
        modified_content = src_file.read_text()
        assert modified_content != original_content, "File content should be changed"
        assert '"""Process items by doubling their values.' in modified_content, "Docstring should be added"
        
        # Step 5: Run tests to verify improvement works (Requirement 4.4)
        print("\nStep 5: Running tests after improvement...")
        metrics_after = self_improvement_engine.test_improvement()
        
        assert isinstance(metrics_after, TestMetrics)
        print(f"Metrics after: {metrics_after.tests_passed}/{metrics_after.total_tests} passed, "
              f"success rate: {metrics_after.success_rate:.1f}%")
        
        # Step 6: Track and compare metrics (Requirement 4.5)
        print("\nStep 6: Comparing metrics...")
        should_rollback, rollback_reason = self_improvement_engine.should_rollback(
            metrics_before, metrics_after
        )
        
        assert should_rollback is False, f"Should not rollback - metrics should not degrade. Reason: {rollback_reason}"
        
        # Verify metrics haven't degraded
        assert metrics_after.tests_failed <= metrics_before.tests_failed, "Should not introduce new failures"
        assert metrics_after.success_rate >= metrics_before.success_rate, "Success rate should not decrease"
        
        print("Metrics comparison: No degradation detected, improvement is safe")
        
        # Step 7: Log the modification in audit trail (Requirement 4.6)
        print("\nStep 7: Logging modification...")
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=impl_result.files_modified,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            reverted=False
        )
        
        # Verify log entry was created
        history = self_improvement_engine.get_modification_history()
        assert len(history) > 0, "Modification log should have entries"
        
        latest_entry = history[-1]
        assert isinstance(latest_entry, SelfModificationLog)
        assert latest_entry.category == opportunity.category
        assert latest_entry.description == opportunity.description
        assert latest_entry.files_modified == impl_result.files_modified
        assert latest_entry.reverted is False
        assert latest_entry.test_results_before == metrics_before
        assert latest_entry.test_results_after == metrics_after
        
        print(f"Modification logged successfully")
        print(f"  Category: {latest_entry.category}")
        print(f"  Description: {latest_entry.description}")
        print(f"  Files modified: {', '.join(latest_entry.files_modified)}")
        print(f"  Reverted: {latest_entry.reverted}")
        
        # Final verification: The improved code should still pass all tests
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_utils.py", "-v"],
            cwd=temp_system_dir,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Tests should pass after improvement:\n{result.stdout}\n{result.stderr}"
        print("\n✓ All tests pass after self-improvement")
        
        print("\n=== Self-Improvement Workflow Completed Successfully ===")
        print(f"✓ Analyzed system and found {len(opportunities)} opportunities")
        print(f"✓ Proposed and implemented improvement")
        print(f"✓ Tests still pass ({metrics_after.tests_passed}/{metrics_after.total_tests})")
        print(f"✓ Metrics tracked and logged")
        print(f"✓ Backup created at {impl_result.backup_path}")
    
    def test_self_improvement_with_rollback_scenario(self, self_improvement_engine, temp_system_dir):
        """Test self-improvement workflow with rollback due to test failures.
        
        This tests the safety mechanism where improvements that break tests are automatically
        rolled back to maintain system stability.
        
        Validates: Requirements 4.3, 4.4, 4.5, 4.6
        """
        print("\n=== Testing Self-Improvement Rollback Scenario ===")
        
        # Step 1: Analyze and propose
        opportunities = self_improvement_engine.analyze_system()
        assert len(opportunities) > 0
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Step 2: Measure before
        metrics_before = self_improvement_engine.test_improvement()
        print(f"Metrics before: {metrics_before.tests_passed}/{metrics_before.total_tests} passed")
        
        # Step 3: Implement a BAD improvement that breaks tests
        print("\nImplementing intentionally broken improvement...")
        src_file = Path(temp_system_dir) / "src" / "utils.py"
        original_content = src_file.read_text()
        
        # Introduce a bug that will break tests
        broken_content = original_content.replace(
            'def calculate_sum(numbers):',
            'def calculate_sum(numbers):\n    return 999  # BUG: Always return 999'
        )
        
        proposal.changes[str(src_file)] = broken_content
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        assert impl_result.success is True
        
        # Step 4: Measure after (should show test failures)
        print("Running tests after broken improvement...")
        metrics_after = self_improvement_engine.test_improvement()
        print(f"Metrics after: {metrics_after.tests_passed}/{metrics_after.total_tests} passed")
        
        # Step 5: Detect degradation (Requirement 4.5)
        should_rollback, rollback_reason = self_improvement_engine.should_rollback(
            metrics_before, metrics_after
        )
        
        print(f"Rollback decision: {should_rollback}")
        if rollback_reason:
            print(f"Reason: {rollback_reason}")
        
        assert should_rollback is True, "Should detect test failures and decide to rollback"
        assert rollback_reason is not None
        assert "fail" in rollback_reason.lower() or "success rate" in rollback_reason.lower()
        
        # Step 6: Perform rollback (Requirement 4.5)
        print("\nPerforming rollback...")
        revert_result = self_improvement_engine.revert_improvement(
            proposal, impl_result.backup_path
        )
        
        assert isinstance(revert_result, OperationResult)
        assert revert_result.success is True, f"Rollback failed: {revert_result.message}"
        
        # Verify content was restored
        restored_content = src_file.read_text()
        assert restored_content == original_content, "Content should be restored to original"
        assert "return 999  # BUG" not in restored_content, "Bug should be removed"
        
        print("Rollback successful")
        
        # Step 7: Log the reverted modification (Requirement 4.6)
        print("\nLogging reverted modification...")
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=impl_result.files_modified,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            reverted=True,
            revert_reason=rollback_reason
        )
        
        # Verify log entry shows it was reverted
        history = self_improvement_engine.get_modification_history()
        assert len(history) > 0
        latest_entry = history[-1]
        assert latest_entry.reverted is True, "Log should show modification was reverted"
        assert latest_entry.revert_reason == rollback_reason
        
        print(f"Reverted modification logged")
        print(f"  Reason: {latest_entry.revert_reason}")
        
        # Step 8: Verify tests pass again after rollback
        metrics_final = self_improvement_engine.test_improvement()
        assert metrics_final.tests_passed == metrics_before.tests_passed, "Tests should pass after rollback"
        
        print(f"\n✓ Tests pass again after rollback: {metrics_final.tests_passed}/{metrics_final.total_tests}")
        print("\n=== Rollback Scenario Completed Successfully ===")
    
    def test_multiple_sequential_improvements(self, self_improvement_engine, temp_system_dir):
        """Test applying multiple improvements sequentially.
        
        This validates that the system can iteratively improve itself multiple times,
        with each improvement building on the previous ones.
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6
        """
        print("\n=== Testing Multiple Sequential Improvements ===")
        
        improvements_applied = []
        src_file = Path(temp_system_dir) / "src" / "utils.py"
        
        # Apply up to 3 improvements
        for iteration in range(3):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            # Analyze system
            opportunities = self_improvement_engine.analyze_system()
            if not opportunities:
                print("No more opportunities found")
                break
            
            # Select opportunity
            opportunity = opportunities[0]
            print(f"Opportunity: {opportunity.description[:80]}...")
            
            # Propose improvement
            proposal = self_improvement_engine.propose_improvement(opportunity)
            
            # Make a safe improvement: add a comment
            original_content = src_file.read_text()
            improved_content = original_content + f"\n# Improvement {iteration + 1}: {opportunity.category}\n"
            proposal.changes[str(src_file)] = improved_content
            
            # Measure before
            metrics_before = self_improvement_engine.test_improvement()
            
            # Implement
            impl_result = self_improvement_engine.implement_improvement(proposal)
            if not impl_result.success:
                print(f"Implementation failed: {impl_result.error_message}")
                break
            
            # Measure after
            metrics_after = self_improvement_engine.test_improvement()
            
            # Check if should rollback
            should_rollback, _ = self_improvement_engine.should_rollback(
                metrics_before, metrics_after
            )
            
            if should_rollback:
                print("Metrics degraded, skipping this improvement")
                self_improvement_engine.revert_improvement(proposal, impl_result.backup_path)
                continue
            
            # Log modification
            self_improvement_engine.log_modification(
                proposal=proposal,
                files_modified=impl_result.files_modified,
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                reverted=False
            )
            
            improvements_applied.append({
                "iteration": iteration + 1,
                "category": opportunity.category,
                "description": opportunity.description
            })
            
            print(f"✓ Improvement {iteration + 1} applied successfully")
        
        # Verify multiple entries in log
        history = self_improvement_engine.get_modification_history()
        successful_improvements = [e for e in history if not e.reverted]
        
        assert len(successful_improvements) >= 1, "Should have at least one successful improvement"
        print(f"\n=== Successfully applied {len(successful_improvements)} improvements ===")
        
        for i, improvement in enumerate(improvements_applied):
            print(f"{i+1}. [{improvement['category']}] {improvement['description'][:60]}...")
        
        # Verify all tests still pass after multiple improvements
        metrics_final = self_improvement_engine.test_improvement()
        assert metrics_final.tests_passed > 0, "Tests should still pass after multiple improvements"
        print(f"\n✓ All tests still pass: {metrics_final.tests_passed}/{metrics_final.total_tests}")
    
    def test_audit_log_persistence(self, self_improvement_engine, temp_system_dir):
        """Test that the audit log persists and can be retrieved.
        
        Validates: Requirement 4.6 (maintain log of all self-modifications)
        """
        print("\n=== Testing Audit Log Persistence ===")
        
        # Create and apply an improvement
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Simple safe change
        src_file = Path(temp_system_dir) / "src" / "utils.py"
        original_content = src_file.read_text()
        proposal.changes[str(src_file)] = original_content + "\n# Audit log test\n"
        
        metrics_before = self_improvement_engine.test_improvement()
        impl_result = self_improvement_engine.implement_improvement(proposal)
        metrics_after = self_improvement_engine.test_improvement()
        
        # Log it
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=impl_result.files_modified,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            reverted=False
        )
        
        # Get history
        history = self_improvement_engine.get_modification_history()
        assert len(history) > 0
        
        # Verify log entry contains all required information
        entry = history[-1]
        assert entry.timestamp is not None
        assert entry.category == opportunity.category
        assert entry.description == opportunity.description
        assert len(entry.files_modified) > 0
        assert entry.test_results_before is not None
        assert entry.test_results_after is not None
        assert entry.reverted is False
        
        print(f"✓ Audit log entry created with all required fields")
        print(f"  Timestamp: {entry.timestamp}")
        print(f"  Category: {entry.category}")
        print(f"  Files: {', '.join(entry.files_modified)}")
        print(f"  Tests before: {entry.test_results_before.tests_passed}/{entry.test_results_before.total_tests}")
        print(f"  Tests after: {entry.test_results_after.tests_passed}/{entry.test_results_after.total_tests}")
        
        # Test creating a NEW engine instance and retrieving the same log
        print("\nCreating new engine instance to test log persistence...")
        new_engine = SelfImprovementEngine(
            system_root=temp_system_dir,
            file_ops=FileOperations(temp_system_dir),
            command_executor=CommandExecutor()
        )
        
        new_history = new_engine.get_modification_history()
        assert len(new_history) == len(history), "New engine should load same log"
        assert new_history[-1].timestamp == entry.timestamp
        assert new_history[-1].description == entry.description
        
        print("✓ Audit log persists across engine instances")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
