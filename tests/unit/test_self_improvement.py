"""Unit tests for SelfImprovementEngine.

Tests cover the self-improvement workflow including analyzing system code,
proposing improvements, implementing changes with backup, testing, and rollback.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.self_improvement.self_improvement import SelfImprovementEngine
from src.core.models import (
    ImprovementOpportunity,
    ImprovementProposal,
    TestMetrics
)
from src.agents.file_operations import FileOperations
from src.agents.command_executor import CommandExecutor


@pytest.fixture
def temp_system_root():
    """Create a temporary system root directory with test files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create src directory structure
    src_dir = Path(temp_dir) / "src"
    src_dir.mkdir()
    
    # Create a sample module file
    module_file = src_dir / "sample_module.py"
    module_file.write_text("""# Sample module for testing
def function_without_docstring():
    pass

def function_with_error_handling():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        return None
    return result
""")
    
    # Create another file with bare except
    another_file = src_dir / "problematic.py"
    another_file.write_text("""def risky_function():
    try:
        result = some_operation()
    except:
        return None
    return result
""")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def self_improvement_engine(temp_system_root):
    """Create a SelfImprovementEngine instance for testing."""
    return SelfImprovementEngine(
        system_root=temp_system_root,
        file_ops=FileOperations(temp_system_root)
    )


def test_analyze_system_finds_opportunities(self_improvement_engine):
    """Test that analyze_system identifies improvement opportunities."""
    opportunities = self_improvement_engine.analyze_system()
    
    # Should find at least some opportunities in the test files
    assert len(opportunities) > 0
    
    # Check that opportunities have required fields
    for opp in opportunities:
        assert opp.category in ["code_quality", "performance", "reliability"]
        assert opp.description
        assert len(opp.affected_files) > 0
        assert opp.severity in ["low", "medium", "high"]
        assert opp.potential_impact


def test_analyze_system_finds_missing_docstrings(self_improvement_engine):
    """Test that analyze_system identifies missing docstrings."""
    opportunities = self_improvement_engine.analyze_system()
    
    # Should find missing docstring opportunity
    docstring_opportunities = [
        opp for opp in opportunities
        if "docstring" in opp.description.lower()
    ]
    assert len(docstring_opportunities) > 0


def test_analyze_system_finds_bare_except(self_improvement_engine):
    """Test that analyze_system identifies bare except clauses."""
    opportunities = self_improvement_engine.analyze_system()
    
    # Should find bare except opportunity
    bare_except_opportunities = [
        opp for opp in opportunities
        if "bare except" in opp.description.lower()
    ]
    assert len(bare_except_opportunities) > 0


def test_propose_improvement(self_improvement_engine):
    """Test that propose_improvement creates valid proposals."""
    # Create a test opportunity
    opportunity = ImprovementOpportunity(
        category="code_quality",
        description="Test improvement",
        affected_files=[str(Path(self_improvement_engine.system_root) / "src" / "sample_module.py")],
        severity="medium",
        potential_impact="Better code quality"
    )
    
    proposal = self_improvement_engine.propose_improvement(opportunity)
    
    # Verify proposal structure
    assert proposal.opportunity == opportunity
    assert len(proposal.changes) > 0
    assert proposal.rationale
    assert proposal.test_plan
    assert proposal.rollback_plan


def test_implement_improvement_creates_backup(self_improvement_engine, temp_system_root):
    """Test that implement_improvement creates backups before changes."""
    # Create a simple proposal
    test_file = Path(temp_system_root) / "src" / "sample_module.py"
    original_content = test_file.read_text()
    
    opportunity = ImprovementOpportunity(
        category="code_quality",
        description="Test change",
        affected_files=[str(test_file)],
        severity="low",
        potential_impact="Test"
    )
    
    proposal = ImprovementProposal(
        opportunity=opportunity,
        changes={str(test_file): "# Modified content\nprint('test')"},
        rationale="Testing backup",
        test_plan="Manual",
        rollback_plan="Restore from backup"
    )
    
    result = self_improvement_engine.implement_improvement(proposal)
    
    assert result.success
    assert result.backup_path
    assert Path(result.backup_path).exists()
    assert len(result.files_modified) == 1
    
    # Verify file was modified
    assert test_file.read_text() == "# Modified content\nprint('test')"
    
    # Verify backup exists and has original content
    backup_path = Path(result.backup_path)
    backup_file = backup_path / "src" / "sample_module.py"
    assert backup_file.exists()
    assert backup_file.read_text() == original_content


def test_revert_improvement_restores_from_backup(self_improvement_engine, temp_system_root):
    """Test that revert_improvement correctly restores files."""
    # First, implement a change
    test_file = Path(temp_system_root) / "src" / "sample_module.py"
    original_content = test_file.read_text()
    
    opportunity = ImprovementOpportunity(
        category="code_quality",
        description="Test change",
        affected_files=[str(test_file)],
        severity="low",
        potential_impact="Test"
    )
    
    proposal = ImprovementProposal(
        opportunity=opportunity,
        changes={str(test_file): "# Modified content"},
        rationale="Testing revert",
        test_plan="Manual",
        rollback_plan="Restore from backup"
    )
    
    impl_result = self_improvement_engine.implement_improvement(proposal)
    assert impl_result.success
    
    # Verify file was changed
    assert test_file.read_text() == "# Modified content"
    
    # Now revert
    revert_result = self_improvement_engine.revert_improvement(proposal, impl_result.backup_path)
    
    assert revert_result.success
    assert "reverted" in revert_result.message.lower()
    
    # Verify file was restored
    assert test_file.read_text() == original_content


def test_should_rollback_detects_success_rate_decrease():
    """Test that should_rollback detects decreased success rate."""
    engine = SelfImprovementEngine(system_root=".")
    
    # Setup: both had failures, but success rate decreased
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
    
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    
    assert should_rollback
    assert "success rate decreased" in reason.lower()


def test_should_rollback_detects_new_failures():
    """Test that should_rollback detects newly introduced failures."""
    engine = SelfImprovementEngine(system_root=".")
    
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
        tests_passed=9,
        tests_failed=1,
        success_rate=90.0,
        error_rate=10.0,
        execution_time=1.0
    )
    
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    
    assert should_rollback
    assert "new test failures" in reason.lower()


def test_should_not_rollback_on_improvement():
    """Test that should_rollback returns False when metrics improve."""
    engine = SelfImprovementEngine(system_root=".")
    
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
    
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    
    assert not should_rollback
    assert reason is None


def test_log_modification(self_improvement_engine, temp_system_root):
    """Test that log_modification creates audit trail."""
    opportunity = ImprovementOpportunity(
        category="code_quality",
        description="Test modification",
        affected_files=["test.py"],
        severity="low",
        potential_impact="Test"
    )
    
    proposal = ImprovementProposal(
        opportunity=opportunity,
        changes={"test.py": "content"},
        rationale="Testing",
        test_plan="Manual",
        rollback_plan="Restore"
    )
    
    metrics_before = TestMetrics(10, 10, 0, 100.0, 0.0, 1.0)
    metrics_after = TestMetrics(10, 10, 0, 100.0, 0.0, 1.0)
    
    self_improvement_engine.log_modification(
        proposal=proposal,
        files_modified=["test.py"],
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        reverted=False
    )
    
    history = self_improvement_engine.get_modification_history()
    
    assert len(history) > 0
    last_entry = history[-1]
    assert last_entry.category == "code_quality"
    assert last_entry.description == "Test modification"
    assert last_entry.files_modified == ["test.py"]
    assert not last_entry.reverted


def test_parse_test_results():
    """Test parsing of pytest output."""
    engine = SelfImprovementEngine(system_root=".")
    
    pytest_output = """
============================= test session starts ==============================
collected 15 items

tests/test_example.py .........                                          [ 60%]
tests/test_other.py ......                                               [100%]

========================== 13 passed, 2 failed in 2.45s =======================
"""
    
    metrics = engine._parse_test_results(pytest_output)
    
    assert metrics.total_tests == 15
    assert metrics.tests_passed == 13
    assert metrics.tests_failed == 2
    assert abs(metrics.success_rate - 86.67) < 0.1  # Allow small floating point difference
    assert abs(metrics.error_rate - 13.33) < 0.1


def test_modification_log_persistence(temp_system_root):
    """Test that modification log persists across instances."""
    # Create first instance and log a modification
    engine1 = SelfImprovementEngine(system_root=temp_system_root)
    
    opportunity = ImprovementOpportunity(
        category="performance",
        description="Speed optimization",
        affected_files=["fast.py"],
        severity="high",
        potential_impact="2x faster"
    )
    
    proposal = ImprovementProposal(
        opportunity=opportunity,
        changes={"fast.py": "optimized"},
        rationale="Performance",
        test_plan="Benchmark",
        rollback_plan="Restore"
    )
    
    metrics = TestMetrics(5, 5, 0, 100.0, 0.0, 0.5)
    
    engine1.log_modification(
        proposal=proposal,
        files_modified=["fast.py"],
        metrics_before=metrics,
        metrics_after=metrics,
        reverted=False
    )
    
    # Create second instance and verify log is loaded
    engine2 = SelfImprovementEngine(system_root=temp_system_root)
    history = engine2.get_modification_history()
    
    assert len(history) == 1
    assert history[0].category == "performance"
    assert history[0].description == "Speed optimization"


def test_empty_system_analysis():
    """Test analyze_system on directory without source code."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = SelfImprovementEngine(system_root=temp_dir)
        opportunities = engine.analyze_system()
        
        # Should return empty list, not error
        assert opportunities == []


def test_test_improvement_with_no_tests(temp_system_root):
    """Test test_improvement when no tests directory exists."""
    engine = SelfImprovementEngine(system_root=temp_system_root)
    
    metrics = engine.test_improvement()
    
    # Should return zero metrics, not error
    assert metrics.total_tests == 0
    assert metrics.tests_passed == 0
    assert metrics.tests_failed == 0
    assert metrics.success_rate == 0.0
    assert metrics.error_rate == 0.0
