"""Demo script showing SelfImprovementEngine capabilities.

This script demonstrates the complete self-improvement workflow including:
- Analyzing system code for improvement opportunities
- Proposing specific improvements
- Implementing changes with backup
- Testing improvements
- Rolling back if metrics degrade
- Maintaining audit trail
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.self_improvement.self_improvement import SelfImprovementEngine
from src.core.models import TestMetrics


def main():
    """Run self-improvement demo."""
    print("=" * 60)
    print("Self-Improvement Engine Demo")
    print("=" * 60)
    
    # Initialize engine pointing to the project root
    project_root = Path(__file__).parent.parent
    engine = SelfImprovementEngine(system_root=str(project_root))
    
    print(f"\nSystem root: {project_root}")
    print(f"Backup directory: {engine.backup_dir}")
    print(f"Log file: {engine.log_path}")
    
    # Step 1: Analyze system
    print("\n" + "=" * 60)
    print("Step 1: Analyzing system code for improvements...")
    print("=" * 60)
    
    opportunities = engine.analyze_system()
    print(f"\nFound {len(opportunities)} improvement opportunities:")
    
    for i, opp in enumerate(opportunities[:5], 1):  # Show first 5
        print(f"\n{i}. Category: {opp.category}")
        print(f"   Severity: {opp.severity}")
        print(f"   Description: {opp.description}")
        print(f"   Affected files: {len(opp.affected_files)}")
        print(f"   Potential impact: {opp.potential_impact}")
    
    if len(opportunities) > 5:
        print(f"\n... and {len(opportunities) - 5} more opportunities")
    
    # Step 2: Show modification history
    print("\n" + "=" * 60)
    print("Step 2: Checking modification history...")
    print("=" * 60)
    
    history = engine.get_modification_history()
    print(f"\nFound {len(history)} previous modifications:")
    
    for i, entry in enumerate(history[:3], 1):  # Show first 3
        print(f"\n{i}. Timestamp: {entry.timestamp}")
        print(f"   Category: {entry.category}")
        print(f"   Description: {entry.description}")
        print(f"   Files modified: {len(entry.files_modified)}")
        print(f"   Tests before: {entry.test_results_before.tests_passed}/{entry.test_results_before.total_tests} passed")
        print(f"   Tests after: {entry.test_results_after.tests_passed}/{entry.test_results_after.total_tests} passed")
        print(f"   Reverted: {entry.reverted}")
        if entry.reverted:
            print(f"   Revert reason: {entry.revert_reason}")
    
    if len(history) > 3:
        print(f"\n... and {len(history) - 3} more modifications")
    
    # Step 3: Demonstrate rollback decision logic
    print("\n" + "=" * 60)
    print("Step 3: Testing rollback decision logic...")
    print("=" * 60)
    
    # Scenario 1: Metrics improve - no rollback
    print("\nScenario 1: Improvement makes tests better")
    metrics_before = TestMetrics(10, 8, 2, 80.0, 20.0, 1.0)
    metrics_after = TestMetrics(10, 10, 0, 100.0, 0.0, 1.0)
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    print(f"  Before: {metrics_before.tests_passed}/{metrics_before.total_tests} passed")
    print(f"  After: {metrics_after.tests_passed}/{metrics_after.total_tests} passed")
    print(f"  Should rollback: {should_rollback}")
    if reason:
        print(f"  Reason: {reason}")
    
    # Scenario 2: New failures introduced - rollback
    print("\nScenario 2: Improvement introduces new test failures")
    metrics_before = TestMetrics(10, 10, 0, 100.0, 0.0, 1.0)
    metrics_after = TestMetrics(10, 8, 2, 80.0, 20.0, 1.0)
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    print(f"  Before: {metrics_before.tests_passed}/{metrics_before.total_tests} passed")
    print(f"  After: {metrics_after.tests_passed}/{metrics_after.total_tests} passed")
    print(f"  Should rollback: {should_rollback}")
    if reason:
        print(f"  Reason: {reason}")
    
    # Scenario 3: Success rate decreases - rollback
    print("\nScenario 3: Improvement decreases success rate")
    metrics_before = TestMetrics(10, 9, 1, 90.0, 10.0, 1.0)
    metrics_after = TestMetrics(10, 7, 3, 70.0, 30.0, 1.0)
    should_rollback, reason = engine.should_rollback(metrics_before, metrics_after)
    print(f"  Before: {metrics_before.success_rate:.1f}% success rate")
    print(f"  After: {metrics_after.success_rate:.1f}% success rate")
    print(f"  Should rollback: {should_rollback}")
    if reason:
        print(f"  Reason: {reason}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    print("\nKey features demonstrated:")
    print("  ✓ System code analysis")
    print("  ✓ Improvement opportunity identification")
    print("  ✓ Modification history tracking")
    print("  ✓ Automatic rollback decision logic")
    print("  ✓ Audit trail maintenance")
    print("\nFor a complete workflow, see tests/integration/test_self_improvement_workflow.py")


if __name__ == "__main__":
    main()
