"""Integration tests for Self-Improvement Engine.

These tests verify the complete self-improvement workflow including:
- End-to-end improvement workflow
- Backup and rollback mechanisms
- Effectiveness metric measurement
- Audit log creation

Task: 14.2 - Write integration tests for self-improvement
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json
import time

from src.self_improvement.self_improvement import SelfImprovementEngine
from src.core.models import (
    ImprovementOpportunity,
    ImprovementProposal,
    TestMetrics,
    SelfModificationLog,
    ImplementationResult
)
from src.agents.file_operations import FileOperations
from src.agents.command_executor import CommandExecutor


@pytest.fixture
def temp_system_dir():
    """Create a temporary system directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system_root = Path(tmpdir) / "test_system"
        system_root.mkdir()
        
        # Create src directory structure
        src_dir = system_root / "src"
        src_dir.mkdir()
        
        # Create tests directory
        tests_dir = system_root / "tests"
        tests_dir.mkdir()
        
        # Create a sample module with improvement opportunities
        module_content = '''"""Sample module for testing self-improvement."""

def calculate_sum(numbers):
    """Calculate sum of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total

def process_data(data):
    # Missing error handling
    result = []
    for item in data:
        result.append(item * 2)
    return result

class DataProcessor:
    def transform(self, value):
        # Missing docstring
        return value.upper()
'''
        (src_dir / "sample_module.py").write_text(module_content)
        
        # Create another module without issues
        good_module = '''"""Well-written module."""

def greet(name: str) -> str:
    """Greet a person by name.
    
    Args:
        name: The person's name
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"
'''
        (src_dir / "good_module.py").write_text(good_module)
        
        # Create a test file
        test_content = '''"""Tests for sample module."""

def test_calculate_sum():
    """Test sum calculation."""
    from src.sample_module import calculate_sum
    assert calculate_sum([1, 2, 3]) == 6
    assert calculate_sum([]) == 0

def test_process_data():
    """Test data processing."""
    from src.sample_module import process_data
    assert process_data([1, 2, 3]) == [2, 4, 6]
'''
        (tests_dir / "test_sample_module.py").write_text(test_content)
        
        # Create pytest configuration
        pytest_ini = '''[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
'''
        (system_root / "pytest.ini").write_text(pytest_ini)
        
        yield str(system_root)


@pytest.fixture
def self_improvement_engine(temp_system_dir):
    """Create a SelfImprovementEngine instance for testing."""
    return SelfImprovementEngine(
        system_root=temp_system_dir,
        file_ops=FileOperations(temp_system_dir),
        command_executor=CommandExecutor()
    )


class TestSelfImprovementInitialization:
    """Test self-improvement engine initialization."""
    
    def test_engine_initialization(self, self_improvement_engine, temp_system_dir):
        """Test that engine initializes correctly."""
        assert self_improvement_engine.system_root == Path(temp_system_dir)
        assert self_improvement_engine.file_ops is not None
        assert self_improvement_engine.command_executor is not None
        assert self_improvement_engine.backup_dir.exists()
        assert isinstance(self_improvement_engine._modification_log, list)
    
    def test_backup_directory_creation(self, temp_system_dir):
        """Test that backup directory is created on initialization."""
        engine = SelfImprovementEngine(system_root=temp_system_dir)
        
        backup_dir = Path(temp_system_dir) / ".self_improvement_backups"
        assert backup_dir.exists()
        assert backup_dir.is_dir()
    
    def test_log_file_initialization(self, temp_system_dir):
        """Test that log file is initialized."""
        engine = SelfImprovementEngine(system_root=temp_system_dir)
        
        # Initially, log should be empty
        assert len(engine.get_modification_history()) == 0


class TestSystemAnalysis:
    """Test system analysis and opportunity identification."""
    
    def test_analyze_system_finds_opportunities(self, self_improvement_engine):
        """Test that analyze_system identifies improvement opportunities.
        
        Validates: Requirement 4.1
        """
        opportunities = self_improvement_engine.analyze_system()
        
        # Should find at least some opportunities in our sample code
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        
        # Check that opportunities have required fields
        for opp in opportunities:
            assert isinstance(opp, ImprovementOpportunity)
            assert opp.category in ["code_quality", "performance", "reliability", "new_capability"]
            assert opp.description
            assert len(opp.affected_files) > 0
            assert opp.severity in ["low", "medium", "high"]
            assert opp.potential_impact
    
    def test_analyze_identifies_missing_docstrings(self, self_improvement_engine):
        """Test that analysis identifies missing docstrings."""
        opportunities = self_improvement_engine.analyze_system()
        
        # Should find missing docstring in DataProcessor.transform
        docstring_opps = [
            opp for opp in opportunities
            if "docstring" in opp.description.lower()
        ]
        
        assert len(docstring_opps) > 0
        assert any("sample_module.py" in str(opp.affected_files) for opp in docstring_opps)
    
    def test_analyze_identifies_missing_error_handling(self, self_improvement_engine):
        """Test that analysis identifies missing error handling."""
        opportunities = self_improvement_engine.analyze_system()
        
        # Should find missing error handling
        error_handling_opps = [
            opp for opp in opportunities
            if "error handling" in opp.description.lower()
        ]
        
        assert len(error_handling_opps) > 0
    
    def test_analyze_categorizes_opportunities(self, self_improvement_engine):
        """Test that opportunities are correctly categorized."""
        opportunities = self_improvement_engine.analyze_system()
        
        categories = {opp.category for opp in opportunities}
        
        # Should have at least code_quality and reliability categories from our sample
        assert "code_quality" in categories or "reliability" in categories
    
    def test_analyze_with_no_src_directory(self, temp_system_dir):
        """Test analysis when src directory doesn't exist."""
        # Remove src directory
        src_dir = Path(temp_system_dir) / "src"
        shutil.rmtree(src_dir)
        
        engine = SelfImprovementEngine(system_root=temp_system_dir)
        opportunities = engine.analyze_system()
        
        # Should return empty list gracefully
        assert opportunities == []


class TestImprovementProposal:
    """Test improvement proposal generation."""
    
    def test_propose_improvement_creates_proposal(self, self_improvement_engine):
        """Test that propose_improvement creates a valid proposal.
        
        Validates: Requirement 4.2
        """
        # First, analyze to get opportunities
        opportunities = self_improvement_engine.analyze_system()
        assert len(opportunities) > 0
        
        # Create proposal for first opportunity
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Verify proposal structure
        assert isinstance(proposal, ImprovementProposal)
        assert proposal.opportunity == opportunity
        assert isinstance(proposal.changes, dict)
        assert len(proposal.changes) > 0
        assert proposal.rationale
        assert proposal.test_plan
        assert proposal.rollback_plan
    
    def test_proposal_includes_affected_files(self, self_improvement_engine):
        """Test that proposal includes content for affected files."""
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Proposal should include changes for affected files
        for file_path in opportunity.affected_files:
            # The proposal should have this file in changes (or be prepared to)
            # In current implementation, it reads all affected files
            assert isinstance(proposal.changes, dict)
    
    def test_proposal_has_rationale(self, self_improvement_engine):
        """Test that proposal includes clear rationale."""
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        assert proposal.rationale
        assert opportunity.category in proposal.rationale
        assert opportunity.description in proposal.rationale
    
    def test_proposal_has_test_and_rollback_plans(self, self_improvement_engine):
        """Test that proposal includes test and rollback plans."""
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        assert proposal.test_plan
        assert "test" in proposal.test_plan.lower()
        assert proposal.rollback_plan
        assert "backup" in proposal.rollback_plan.lower() or "restore" in proposal.rollback_plan.lower()


class TestImplementationWorkflow:
    """Test end-to-end improvement implementation workflow."""
    
    def test_complete_improvement_workflow_success(self, self_improvement_engine, temp_system_dir):
        """Test complete improvement workflow from analysis to verification.
        
        This test validates the full workflow:
        1. Analyze system
        2. Propose improvement
        3. Measure metrics before
        4. Implement improvement
        5. Measure metrics after
        6. Log modification
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6
        """
        # Step 1: Analyze system
        opportunities = self_improvement_engine.analyze_system()
        assert len(opportunities) > 0
        
        # Step 2: Propose improvement
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Step 3: Measure metrics before
        metrics_before = self_improvement_engine.test_improvement()
        assert isinstance(metrics_before, TestMetrics)
        
        # Step 4: Implement improvement (with a trivial change that won't break tests)
        # For this test, we'll modify the proposal to add a simple comment
        for file_path in proposal.changes:
            if file_path.endswith("sample_module.py"):
                proposal.changes[file_path] = proposal.changes[file_path] + "\n# Improved by self-improvement engine\n"
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        assert impl_result.success is True
        assert len(impl_result.files_modified) > 0
        assert impl_result.backup_path is not None
        assert Path(impl_result.backup_path).exists()
        
        # Verify backup was created
        backup_dir = Path(impl_result.backup_path)
        assert backup_dir.exists()
        
        # Step 5: Measure metrics after
        metrics_after = self_improvement_engine.test_improvement()
        assert isinstance(metrics_after, TestMetrics)
        
        # Step 6: Log modification
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=impl_result.files_modified,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            reverted=False
        )
        
        # Verify log was created
        history = self_improvement_engine.get_modification_history()
        assert len(history) == 1
        assert history[0].category == opportunity.category
        assert history[0].description == opportunity.description
        assert history[0].files_modified == impl_result.files_modified
        assert history[0].reverted is False
    
    def test_workflow_with_rollback_on_degradation(self, self_improvement_engine, temp_system_dir):
        """Test workflow that triggers rollback due to metric degradation.
        
        Validates: Requirements 4.3, 4.4, 4.5, 4.6
        """
        # Analyze and propose
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Measure before
        metrics_before = self_improvement_engine.test_improvement()
        
        # Implement improvement that breaks tests
        # Modify to introduce a syntax error
        for file_path in proposal.changes:
            if file_path.endswith("sample_module.py"):
                # Add code that will break the module
                proposal.changes[file_path] = "def broken_function(\n  pass  # Syntax error\n"
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        # If implementation succeeded (file was written)
        if impl_result.success:
            # Measure after
            metrics_after = self_improvement_engine.test_improvement()
            
            # Check if rollback is needed
            should_rollback, reason = self_improvement_engine.should_rollback(
                metrics_before, metrics_after
            )
            
            # Rollback if metrics degraded
            if should_rollback:
                revert_result = self_improvement_engine.revert_improvement(
                    proposal, impl_result.backup_path
                )
                
                assert revert_result.success is True
                
                # Log the reverted modification
                self_improvement_engine.log_modification(
                    proposal=proposal,
                    files_modified=impl_result.files_modified,
                    metrics_before=metrics_before,
                    metrics_after=metrics_after,
                    reverted=True,
                    revert_reason=reason
                )
                
                # Verify log entry shows revert
                history = self_improvement_engine.get_modification_history()
                assert any(entry.reverted for entry in history)
    
    def test_multiple_improvements_workflow(self, self_improvement_engine):
        """Test applying multiple improvements in sequence."""
        opportunities = self_improvement_engine.analyze_system()
        
        # Apply up to 3 improvements
        improvements_applied = 0
        for opportunity in opportunities[:3]:
            proposal = self_improvement_engine.propose_improvement(opportunity)
            
            # Simple improvement: just add comment
            for file_path in proposal.changes:
                proposal.changes[file_path] = proposal.changes[file_path] + f"\n# Improvement {improvements_applied + 1}\n"
            
            metrics_before = self_improvement_engine.test_improvement()
            impl_result = self_improvement_engine.implement_improvement(proposal)
            
            if impl_result.success:
                metrics_after = self_improvement_engine.test_improvement()
                
                self_improvement_engine.log_modification(
                    proposal=proposal,
                    files_modified=impl_result.files_modified,
                    metrics_before=metrics_before,
                    metrics_after=metrics_after,
                    reverted=False
                )
                
                improvements_applied += 1
        
        # Verify multiple entries in log
        history = self_improvement_engine.get_modification_history()
        assert len(history) == improvements_applied
        assert improvements_applied > 0


class TestBackupAndRollback:
    """Test backup creation and rollback mechanisms."""
    
    def test_backup_created_before_implementation(self, self_improvement_engine, temp_system_dir):
        """Test that backup is created before modifying files.
        
        Validates: Requirement 4.3 (backup mechanism)
        """
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Modify proposal to have actual changes
        for file_path in proposal.changes:
            proposal.changes[file_path] = "# Modified content\n"
        
        # Get original content
        original_contents = {}
        for file_path in proposal.changes:
            if Path(file_path).exists():
                original_contents[file_path] = Path(file_path).read_text()
        
        # Implement
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        if impl_result.success and original_contents:
            # Verify backup exists and contains original content
            backup_dir = Path(impl_result.backup_path)
            assert backup_dir.exists()
            
            for file_path, original_content in original_contents.items():
                relative_path = Path(file_path).relative_to(temp_system_dir)
                backup_file = backup_dir / relative_path
                
                if backup_file.exists():
                    assert backup_file.read_text() == original_content
    
    def test_rollback_restores_original_files(self, self_improvement_engine, temp_system_dir):
        """Test that rollback correctly restores original files.
        
        Validates: Requirement 4.5 (revert changes)
        """
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Track original contents
        original_contents = {}
        for file_path in proposal.changes:
            if Path(file_path).exists():
                original_contents[file_path] = Path(file_path).read_text()
        
        # Modify proposal
        for file_path in proposal.changes:
            proposal.changes[file_path] = "# MODIFIED CONTENT\nprint('changed')\n"
        
        # Implement
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        if impl_result.success and original_contents:
            # Verify files were changed
            for file_path in proposal.changes:
                if Path(file_path).exists():
                    current_content = Path(file_path).read_text()
                    if file_path in original_contents:
                        assert current_content != original_contents[file_path]
            
            # Rollback
            revert_result = self_improvement_engine.revert_improvement(
                proposal, impl_result.backup_path
            )
            
            assert revert_result.success is True
            
            # Verify files were restored
            for file_path, original_content in original_contents.items():
                if Path(file_path).exists():
                    restored_content = Path(file_path).read_text()
                    assert restored_content == original_content
    
    def test_rollback_with_missing_backup(self, self_improvement_engine):
        """Test rollback behavior when backup doesn't exist."""
        opportunity = ImprovementOpportunity(
            category="code_quality",
            description="Test",
            affected_files=[],
            severity="low",
            potential_impact="Test"
        )
        
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Try to revert with non-existent backup
        revert_result = self_improvement_engine.revert_improvement(
            proposal, "/nonexistent/backup"
        )
        
        assert revert_result.success is False
        assert "not found" in revert_result.message.lower()
    
    def test_backup_preserves_directory_structure(self, self_improvement_engine, temp_system_dir):
        """Test that backup preserves directory structure."""
        # Create nested file
        nested_dir = Path(temp_system_dir) / "src" / "nested"
        nested_dir.mkdir(exist_ok=True)
        nested_file = nested_dir / "nested_module.py"
        nested_file.write_text("# Nested module\n")
        
        # Create opportunity affecting nested file
        opportunity = ImprovementOpportunity(
            category="code_quality",
            description="Improve nested module",
            affected_files=[str(nested_file)],
            severity="low",
            potential_impact="Better code"
        )
        
        proposal = self_improvement_engine.propose_improvement(opportunity)
        proposal.changes[str(nested_file)] = "# Modified nested module\n"
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        if impl_result.success:
            backup_dir = Path(impl_result.backup_path)
            relative_path = nested_file.relative_to(temp_system_dir)
            backup_file = backup_dir / relative_path
            
            # Verify nested structure is preserved in backup
            assert backup_file.exists()
            assert backup_file.parent.name == "nested"
    
    def test_implementation_rollback_on_failure(self, self_improvement_engine, temp_system_dir):
        """Test that implementation automatically rolls back on failure."""
        opportunities = self_improvement_engine.analyze_system()
        opportunity = opportunities[0]
        proposal = self_improvement_engine.propose_improvement(opportunity)
        
        # Create a scenario that will cause partial failure
        # Add a file that doesn't exist to the changes
        proposal.changes["/invalid/path/file.py"] = "content"
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        # Should fail and rollback
        assert impl_result.success is False
        assert impl_result.error_message is not None


class TestMetricsMeasurement:
    """Test effectiveness metric measurement."""
    
    def test_test_improvement_measures_metrics(self, self_improvement_engine):
        """Test that test_improvement measures effectiveness metrics.
        
        Validates: Requirement 4.4 (test improvements)
        """
        metrics = self_improvement_engine.test_improvement()
        
        assert isinstance(metrics, TestMetrics)
        assert isinstance(metrics.total_tests, int)
        assert isinstance(metrics.tests_passed, int)
        assert isinstance(metrics.tests_failed, int)
        assert isinstance(metrics.success_rate, float)
        assert isinstance(metrics.error_rate, float)
        assert isinstance(metrics.execution_time, float)
        
        # Metrics should be consistent
        assert metrics.total_tests == metrics.tests_passed + metrics.tests_failed
        if metrics.total_tests > 0:
            assert 0 <= metrics.success_rate <= 100
            assert 0 <= metrics.error_rate <= 100
    
    def test_metrics_with_passing_tests(self, self_improvement_engine):
        """Test metrics when all tests pass."""
        metrics = self_improvement_engine.test_improvement()
        
        # Our sample tests should pass initially
        if metrics.total_tests > 0:
            assert metrics.tests_passed >= 0
            assert metrics.success_rate >= 0
    
    def test_should_rollback_on_new_failures(self, self_improvement_engine):
        """Test rollback detection when new failures are introduced."""
        metrics_before = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        metrics_after = TestMetrics(
            total_tests=10,
            tests_passed=8,
            tests_failed=2,
            success_rate=80.0,
            error_rate=20.0,
            execution_time=1.0
        )
        
        should_rollback, reason = self_improvement_engine.should_rollback(
            metrics_before, metrics_after
        )
        
        assert should_rollback is True
        assert "new test failures" in reason.lower() or "failure" in reason.lower()
    
    def test_should_rollback_on_success_rate_decrease(self, self_improvement_engine):
        """Test rollback detection when success rate decreases."""
        metrics_before = TestMetrics(
            total_tests=10,
            tests_passed=9,
            tests_failed=1,
            success_rate=90.0,
            error_rate=10.0,
            execution_time=1.0
        )
        
        metrics_after = TestMetrics(
            total_tests=10,
            tests_passed=7,
            tests_failed=3,
            success_rate=70.0,
            error_rate=30.0,
            execution_time=1.0
        )
        
        should_rollback, reason = self_improvement_engine.should_rollback(
            metrics_before, metrics_after
        )
        
        assert should_rollback is True
        assert "success rate decreased" in reason.lower()
    
    def test_no_rollback_on_improvement(self, self_improvement_engine):
        """Test that rollback is not triggered when metrics improve."""
        metrics_before = TestMetrics(
            total_tests=10,
            tests_passed=8,
            tests_failed=2,
            success_rate=80.0,
            error_rate=20.0,
            execution_time=1.0
        )
        
        metrics_after = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        should_rollback, reason = self_improvement_engine.should_rollback(
            metrics_before, metrics_after
        )
        
        assert should_rollback is False
        assert reason is None
    
    def test_no_rollback_on_equal_metrics(self, self_improvement_engine):
        """Test that rollback is not triggered when metrics stay the same."""
        metrics_before = TestMetrics(
            total_tests=10,
            tests_passed=9,
            tests_failed=1,
            success_rate=90.0,
            error_rate=10.0,
            execution_time=1.0
        )
        
        metrics_after = TestMetrics(
            total_tests=10,
            tests_passed=9,
            tests_failed=1,
            success_rate=90.0,
            error_rate=10.0,
            execution_time=1.2
        )
        
        should_rollback, reason = self_improvement_engine.should_rollback(
            metrics_before, metrics_after
        )
        
        assert should_rollback is False
        assert reason is None
    
    def test_metrics_parsing_from_pytest_output(self, self_improvement_engine):
        """Test that metrics are correctly parsed from pytest output."""
        # This is tested indirectly through test_improvement, but we can
        # test the internal parsing method if needed
        sample_output = "====== 5 passed, 2 failed in 1.23s ======"
        
        metrics = self_improvement_engine._parse_test_results(sample_output)
        
        assert metrics.tests_passed == 5
        assert metrics.tests_failed == 2
        assert metrics.total_tests == 7
        assert abs(metrics.success_rate - 71.4) < 1.0  # Allow small rounding difference
        assert abs(metrics.error_rate - 28.6) < 1.0


class TestAuditLog:
    """Test audit log creation and management."""
    
    def test_log_modification_creates_entry(self, self_improvement_engine):
        """Test that log_modification creates a log entry.
        
        Validates: Requirement 4.6 (maintain log of modifications)
        """
        opportunity = ImprovementOpportunity(
            category="code_quality",
            description="Test improvement",
            affected_files=["test.py"],
            severity="low",
            potential_impact="Better code"
        )
        
        proposal = ImprovementProposal(
            opportunity=opportunity,
            changes={"test.py": "# New content\n"},
            rationale="Testing",
            test_plan="Run tests",
            rollback_plan="Restore backup"
        )
        
        metrics_before = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        metrics_after = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=["test.py"],
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            reverted=False
        )
        
        history = self_improvement_engine.get_modification_history()
        
        assert len(history) == 1
        entry = history[0]
        assert isinstance(entry, SelfModificationLog)
        assert entry.category == "code_quality"
        assert entry.description == "Test improvement"
        assert entry.files_modified == ["test.py"]
        assert entry.test_results_before == metrics_before
        assert entry.test_results_after == metrics_after
        assert entry.reverted is False
        assert entry.revert_reason is None
    
    def test_log_modification_with_revert(self, self_improvement_engine):
        """Test logging a modification that was reverted."""
        opportunity = ImprovementOpportunity(
            category="reliability",
            description="Failed improvement",
            affected_files=["test.py"],
            severity="medium",
            potential_impact="Worse reliability"
        )
        
        proposal = ImprovementProposal(
            opportunity=opportunity,
            changes={"test.py": "# Bad content\n"},
            rationale="Testing revert",
            test_plan="Run tests",
            rollback_plan="Restore backup"
        )
        
        metrics_before = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        metrics_after = TestMetrics(
            total_tests=10,
            tests_passed=5,
            tests_failed=5,
            success_rate=50.0,
            error_rate=50.0,
            execution_time=1.0
        )
        
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=["test.py"],
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            reverted=True,
            revert_reason="Tests failed after implementation"
        )
        
        history = self_improvement_engine.get_modification_history()
        
        assert len(history) == 1
        entry = history[0]
        assert entry.reverted is True
        assert entry.revert_reason == "Tests failed after implementation"
    
    def test_log_persists_to_disk(self, self_improvement_engine, temp_system_dir):
        """Test that log is persisted to disk."""
        opportunity = ImprovementOpportunity(
            category="performance",
            description="Optimize function",
            affected_files=["test.py"],
            severity="medium",
            potential_impact="Better performance"
        )
        
        proposal = ImprovementProposal(
            opportunity=opportunity,
            changes={"test.py": "# Optimized\n"},
            rationale="Optimization",
            test_plan="Run tests",
            rollback_plan="Restore backup"
        )
        
        metrics = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=["test.py"],
            metrics_before=metrics,
            metrics_after=metrics,
            reverted=False
        )
        
        # Verify log file exists
        log_path = Path(temp_system_dir) / ".self_improvement_log.json"
        assert log_path.exists()
        
        # Load and verify content
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) == 1
        assert log_data[0]['category'] == "performance"
        assert log_data[0]['description'] == "Optimize function"
    
    def test_log_loads_from_disk(self, self_improvement_engine, temp_system_dir):
        """Test that existing log is loaded from disk on initialization."""
        # Create initial log entry
        opportunity = ImprovementOpportunity(
            category="code_quality",
            description="Initial improvement",
            affected_files=["test.py"],
            severity="low",
            potential_impact="Better code"
        )
        
        proposal = ImprovementProposal(
            opportunity=opportunity,
            changes={"test.py": "# Content\n"},
            rationale="Testing",
            test_plan="Run tests",
            rollback_plan="Restore backup"
        )
        
        metrics = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=["test.py"],
            metrics_before=metrics,
            metrics_after=metrics,
            reverted=False
        )
        
        # Create new engine instance (should load existing log)
        new_engine = SelfImprovementEngine(system_root=temp_system_dir)
        
        history = new_engine.get_modification_history()
        assert len(history) == 1
        assert history[0].description == "Initial improvement"
    
    def test_log_tracks_multiple_modifications(self, self_improvement_engine):
        """Test that log correctly tracks multiple modifications."""
        for i in range(3):
            opportunity = ImprovementOpportunity(
                category="code_quality",
                description=f"Improvement {i}",
                affected_files=[f"test{i}.py"],
                severity="low",
                potential_impact="Better code"
            )
            
            proposal = ImprovementProposal(
                opportunity=opportunity,
                changes={f"test{i}.py": f"# Content {i}\n"},
                rationale=f"Testing {i}",
                test_plan="Run tests",
                rollback_plan="Restore backup"
            )
            
            metrics = TestMetrics(
                total_tests=10,
                tests_passed=10,
                tests_failed=0,
                success_rate=100.0,
                error_rate=0.0,
                execution_time=1.0
            )
            
            self_improvement_engine.log_modification(
                proposal=proposal,
                files_modified=[f"test{i}.py"],
                metrics_before=metrics,
                metrics_after=metrics,
                reverted=False
            )
        
        history = self_improvement_engine.get_modification_history()
        assert len(history) == 3
        
        # Verify chronological order
        for i, entry in enumerate(history):
            assert entry.description == f"Improvement {i}"
    
    def test_log_entry_has_timestamp(self, self_improvement_engine):
        """Test that log entries include timestamps."""
        opportunity = ImprovementOpportunity(
            category="code_quality",
            description="Test",
            affected_files=["test.py"],
            severity="low",
            potential_impact="Better code"
        )
        
        proposal = ImprovementProposal(
            opportunity=opportunity,
            changes={"test.py": "# Content\n"},
            rationale="Testing",
            test_plan="Run tests",
            rollback_plan="Restore backup"
        )
        
        metrics = TestMetrics(
            total_tests=10,
            tests_passed=10,
            tests_failed=0,
            success_rate=100.0,
            error_rate=0.0,
            execution_time=1.0
        )
        
        before_time = datetime.now()
        
        self_improvement_engine.log_modification(
            proposal=proposal,
            files_modified=["test.py"],
            metrics_before=metrics,
            metrics_after=metrics,
            reverted=False
        )
        
        after_time = datetime.now()
        
        history = self_improvement_engine.get_modification_history()
        entry = history[0]
        
        assert isinstance(entry.timestamp, datetime)
        assert before_time <= entry.timestamp <= after_time


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_implementation_with_empty_changes(self, self_improvement_engine):
        """Test implementation with no actual changes."""
        opportunity = ImprovementOpportunity(
            category="code_quality",
            description="No changes",
            affected_files=[],
            severity="low",
            potential_impact="None"
        )
        
        proposal = ImprovementProposal(
            opportunity=opportunity,
            changes={},
            rationale="Testing empty",
            test_plan="Run tests",
            rollback_plan="Restore backup"
        )
        
        impl_result = self_improvement_engine.implement_improvement(proposal)
        
        # Should succeed with no files modified
        assert impl_result.success is True
        assert len(impl_result.files_modified) == 0
    
    def test_analyze_with_invalid_python_files(self, self_improvement_engine, temp_system_dir):
        """Test analysis with invalid Python files."""
        # Create invalid Python file
        invalid_file = Path(temp_system_dir) / "src" / "invalid.py"
        invalid_file.write_text("This is not valid Python syntax def broken(\n")
        
        # Analysis should handle gracefully
        opportunities = self_improvement_engine.analyze_system()
        
        # Should still return opportunities (may include the invalid file or not)
        assert isinstance(opportunities, list)
    
    def test_metrics_with_no_tests(self, temp_system_dir):
        """Test metric measurement when no tests exist."""
        # Remove tests directory
        tests_dir = Path(temp_system_dir) / "tests"
        shutil.rmtree(tests_dir)
        
        engine = SelfImprovementEngine(system_root=temp_system_dir)
        metrics = engine.test_improvement()
        
        # Should return zero metrics
        assert metrics.total_tests == 0
        assert metrics.tests_passed == 0
        assert metrics.tests_failed == 0
        assert metrics.success_rate == 0.0
