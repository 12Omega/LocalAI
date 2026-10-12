"""Integration tests for self-improvement workflow.

Tests the complete self-improvement cycle including analysis, proposal,
implementation, testing, and rollback decisions.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.self_improvement.self_improvement import SelfImprovementEngine
from src.core.models import TestMetrics


@pytest.fixture
def test_system():
    """Create a complete test system with source and tests."""
    temp_dir = tempfile.mkdtemp()
    
    # Create src directory
    src_dir = Path(temp_dir) / "src"
    src_dir.mkdir()
    
    # Create a module with improvement opportunities
    module_file = src_dir / "calculator.py"
    module_file.write_text("""def add(a, b):
    return a + b

def divide(a, b):
    try:
        return a / b
    except:
        return None

def multiply(a, b):
    result = a * b
    return result
""")
    
    # Create tests directory
    tests_dir = Path(temp_dir) / "tests"
    tests_dir.mkdir()
    
    # Create a passing test
    test_file = tests_dir / "test_calculator.py"
    test_file.write_text("""def test_add():
    from src.calculator import add
    assert add(2, 3) == 5

def test_multiply():
    from src.calculator import multiply
    assert multiply(3, 4) == 12
""")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_complete_improvement_workflow(test_system):
    """Test complete workflow: analyze -> propose -> implement -> test."""
    engine = SelfImprovementEngine(system_root=test_system)
    
    # Step 1: Analyze system
    opportunities = engine.analyze_system()
    assert len(opportunities) > 0
    
    # Should find bare except and missing docstrings
    categories = {opp.category for opp in opportunities}
    assert "code_quality" in categories or "reliability" in categories
    
    # Step 2: Propose improvement for first opportunity
    proposal = engine.propose_improvement(opportunities[0])
    assert proposal is not None
    assert len(proposal.changes) > 0
    
    # Step 3: Measure metrics before
    metrics_before = TestMetrics(
        total_tests=2,
        tests_passed=2,
        tests_failed=0,
        success_rate=100.0,
        error_rate=0.0,
        execution_time=0.5
    )
    
    # Step 4: Implement improvement
    result = engine.implement_improvement(proposal)
    assert result.success
    assert result.backup_path is not None
    
    # Step 5: Measure metrics after (simulated)
    metrics_after = TestMetrics(
        total_tests=2,
        tests_passed=2,
        tests_failed=0,
        success_rate=100.0,
        error_rate=0.0,
        execution_time=0.5
    )
    
    # Step 6: Check if rollback needed
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    assert not should_rollback  # Metrics didn't degrade
    
    # Step 7: Log the modification
    engine.log_modification(
        proposal=proposal,
        files_modified=result.files_modified,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        reverted=False
    )
    
    # Verify log entry was created
    history = engine.get_modification_history()
    assert len(history) > 0
    assert history[-1].category == opportunities[0].category


def test_improvement_with_rollback(test_system):
    """Test workflow where improvement degrades metrics and gets rolled back."""
    engine = SelfImprovementEngine(system_root=test_system)
    
    # Analyze and propose
    opportunities = engine.analyze_system()
    assert len(opportunities) > 0
    
    proposal = engine.propose_improvement(opportunities[0])
    
    # Metrics before: all tests passing
    metrics_before = TestMetrics(
        total_tests=5,
        tests_passed=5,
        tests_failed=0,
        success_rate=100.0,
        error_rate=0.0,
        execution_time=1.0
    )
    
    # Implement improvement
    result = engine.implement_improvement(proposal)
    assert result.success
    
    # Metrics after: improvement broke tests
    metrics_after = TestMetrics(
        total_tests=5,
        tests_passed=3,
        tests_failed=2,
        success_rate=60.0,
        error_rate=40.0,
        execution_time=1.0
    )
    
    # Check if rollback needed
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    assert should_rollback
    assert reason is not None
    
    # Perform rollback
    revert_result = engine.revert_improvement(proposal, result.backup_path)
    assert revert_result.success
    
    # Log the modification with revert
    engine.log_modification(
        proposal=proposal,
        files_modified=result.files_modified,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
        reverted=True,
        revert_reason=reason
    )
    
    # Verify log shows it was reverted
    history = engine.get_modification_history()
    assert history[-1].reverted
    assert history[-1].revert_reason == reason


def test_multiple_improvement_cycles(test_system):
    """Test multiple improvement cycles maintaining audit trail."""
    engine = SelfImprovementEngine(system_root=test_system)
    
    # First improvement cycle
    opportunities = engine.analyze_system()
    if len(opportunities) > 0:
        proposal1 = engine.propose_improvement(opportunities[0])
        result1 = engine.implement_improvement(proposal1)
        
        metrics = TestMetrics(5, 5, 0, 100.0, 0.0, 1.0)
        engine.log_modification(
            proposal=proposal1,
            files_modified=result1.files_modified,
            metrics_before=metrics,
            metrics_after=metrics,
            reverted=False
        )
    
    # Second improvement cycle (if more opportunities)
    opportunities = engine.analyze_system()
    if len(opportunities) > 1:
        proposal2 = engine.propose_improvement(opportunities[1])
        result2 = engine.implement_improvement(proposal2)
        
        metrics = TestMetrics(5, 5, 0, 100.0, 0.0, 1.0)
        engine.log_modification(
            proposal=proposal2,
            files_modified=result2.files_modified,
            metrics_before=metrics,
            metrics_after=metrics,
            reverted=False
        )
    
    # Verify audit trail
    history = engine.get_modification_history()
    assert len(history) >= 1
    
    # Each entry should have complete information
    for entry in history:
        assert entry.timestamp is not None
        assert entry.category in ["code_quality", "performance", "reliability", "new_capability"]
        assert entry.description
        assert isinstance(entry.reverted, bool)


def test_backup_directory_created(test_system):
    """Test that backup directory is created and maintained."""
    engine = SelfImprovementEngine(system_root=test_system)
    
    backup_dir = Path(test_system) / ".self_improvement_backups"
    assert backup_dir.exists()
    assert backup_dir.is_dir()


def test_log_file_created(test_system):
    """Test that modification log file is created."""
    engine = SelfImprovementEngine(system_root=test_system)
    
    # Make a modification to trigger log save
    opportunities = engine.analyze_system()
    if len(opportunities) > 0:
        proposal = engine.propose_improvement(opportunities[0])
        result = engine.implement_improvement(proposal)
        
        metrics = TestMetrics(1, 1, 0, 100.0, 0.0, 0.1)
        engine.log_modification(
            proposal=proposal,
            files_modified=result.files_modified,
            metrics_before=metrics,
            metrics_after=metrics,
            reverted=False
        )
    
    # Check log file exists
    log_path = Path(test_system) / ".self_improvement_log.json"
    assert log_path.exists()
    
    # Verify it can be loaded by a new engine instance
    engine2 = SelfImprovementEngine(system_root=test_system)
    history = engine2.get_modification_history()
    assert len(history) >= 1
