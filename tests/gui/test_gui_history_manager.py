"""
Unit tests for GUI History Manager.

Tests Requirements:
- 5.1-5.11: History View functionality
- 14.1: Data persistence
- 14.7: Output size limits
- 14.8: Automatic purging
"""

import pytest
import tempfile
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

from src.gui.gui_history_manager import GUIHistoryManager, HistoryEntry


class TestHistoryEntry:
    """Test HistoryEntry dataclass."""
    
    def test_history_entry_creation(self):
        """HistoryEntry should be created with all fields."""
        entry = HistoryEntry(
            entry_id="test-123",
            task_description="Test task",
            timestamp=datetime.now(),
            duration_seconds=10.5,
            status="success",
            output="Test output",
            error_message=None,
            config_snapshot={'llm': {'endpoint': 'http://localhost:11434'}}
        )
        
        assert entry.entry_id == "test-123"
        assert entry.task_description == "Test task"
        assert entry.duration_seconds == 10.5
        assert entry.status == "success"
        assert entry.output == "Test output"
        assert entry.error_message is None
        assert entry.config_snapshot is not None
    
    def test_to_dict_conversion(self):
        """HistoryEntry should convert to dictionary correctly."""
        entry = HistoryEntry(
            entry_id="test-456",
            task_description="Another task",
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            duration_seconds=20.0,
            status="failed",
            output="Error output",
            error_message="Something went wrong",
            config_snapshot={}
        )
        
        result = entry.to_dict()
        
        assert result['entry_id'] == "test-456"
        assert result['task_description'] == "Another task"
        assert result['timestamp'] == "2024-01-15T14:30:00"
        assert result['duration_seconds'] == 20.0
        assert result['status'] == "failed"
        assert result['error_message'] == "Something went wrong"


class TestGUIHistoryManager:
    """Test GUIHistoryManager class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test_history.db'
            yield str(db_path)
    
    @pytest.fixture
    def manager(self, temp_db):
        """Create GUIHistoryManager instance with temporary database."""
        return GUIHistoryManager(db_path=temp_db)
    
    @pytest.fixture
    def sample_entry(self):
        """Create a sample history entry."""
        return HistoryEntry(
            entry_id="sample-001",
            task_description="Sample task",
            timestamp=datetime.now(),
            duration_seconds=15.5,
            status="success",
            output="Sample output",
            error_message=None,
            config_snapshot={'test': 'config'}
        )
    
    def test_database_initialization(self, manager, temp_db):
        """Database should be initialized with proper schema."""
        assert Path(temp_db).exists()
        
        # Verify tables exist
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='history_entries'
        """)
        assert cursor.fetchone() is not None
        
        # Verify indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name IN ('idx_timestamp', 'idx_status')
        """)
        indexes = cursor.fetchall()
        assert len(indexes) == 2
        
        conn.close()
    
    def test_add_and_retrieve_entry(self, manager, sample_entry):
        """Adding an entry should make it retrievable. (Req 5.10, 14.1)"""
        # Add entry
        entry_id = manager.add_entry(sample_entry)
        
        assert entry_id == sample_entry.entry_id
        
        # Retrieve entry
        entries = manager.get_entries(limit=10)
        
        assert len(entries) == 1
        assert entries[0].entry_id == sample_entry.entry_id
        assert entries[0].task_description == sample_entry.task_description
        assert entries[0].status == sample_entry.status
    
    def test_add_entry_generates_uuid_if_missing(self, manager):
        """Entry without ID should get auto-generated UUID."""
        entry = HistoryEntry(
            entry_id="",  # Empty ID
            task_description="Test",
            timestamp=datetime.now(),
            duration_seconds=5.0,
            status="success",
            output="Output"
        )
        
        entry_id = manager.add_entry(entry)
        
        assert entry_id is not None
        assert len(entry_id) > 0
        assert entry.entry_id == entry_id
    
    def test_add_entry_truncates_large_output(self, manager):
        """Large output should be truncated to max size. (Req 14.7)"""
        large_output = "x" * (15 * 1024 * 1024)  # 15MB
        
        entry = HistoryEntry(
            entry_id="large-001",
            task_description="Large output task",
            timestamp=datetime.now(),
            duration_seconds=10.0,
            status="success",
            output=large_output
        )
        
        manager.add_entry(entry)
        
        retrieved = manager.get_entry_by_id("large-001")
        
        assert retrieved is not None
        assert len(retrieved.output) <= manager.MAX_OUTPUT_SIZE + 50  # Allow for truncation message
        assert "truncated" in retrieved.output
    
    def test_get_entry_by_id(self, manager, sample_entry):
        """Should retrieve specific entry by ID. (Req 5.4)"""
        manager.add_entry(sample_entry)
        
        retrieved = manager.get_entry_by_id(sample_entry.entry_id)
        
        assert retrieved is not None
        assert retrieved.entry_id == sample_entry.entry_id
        assert retrieved.task_description == sample_entry.task_description
    
    def test_get_entry_by_id_returns_none_if_not_found(self, manager):
        """Should return None for non-existent ID."""
        result = manager.get_entry_by_id("non-existent-id")
        
        assert result is None
    
    def test_get_entries_with_limit(self, manager):
        """Should respect limit parameter. (Req 5.3)"""
        # Add 5 entries
        for i in range(5):
            entry = HistoryEntry(
                entry_id=f"entry-{i}",
                task_description=f"Task {i}",
                timestamp=datetime.now(),
                duration_seconds=float(i),
                status="success",
                output=f"Output {i}"
            )
            manager.add_entry(entry)
        
        # Retrieve with limit
        entries = manager.get_entries(limit=3)
        
        assert len(entries) == 3
    
    def test_get_entries_sorted_by_timestamp_desc(self, manager):
        """Entries should be sorted newest first. (Req 5.1, 5.2)"""
        # Add entries with different timestamps
        now = datetime.now()
        
        entry1 = HistoryEntry(
            entry_id="old",
            task_description="Old task",
            timestamp=now - timedelta(hours=2),
            duration_seconds=10.0,
            status="success",
            output="Old output"
        )
        
        entry2 = HistoryEntry(
            entry_id="new",
            task_description="New task",
            timestamp=now,
            duration_seconds=5.0,
            status="success",
            output="New output"
        )
        
        manager.add_entry(entry1)
        manager.add_entry(entry2)
        
        entries = manager.get_entries()
        
        assert len(entries) == 2
        assert entries[0].entry_id == "new"  # Newest first
        assert entries[1].entry_id == "old"
    
    def test_search_filters_by_description(self, manager):
        """Search should filter by task description. (Req 5.8)"""
        # Add multiple entries
        entries_data = [
            ("calc-1", "Create calculator module", "success"),
            ("api-1", "Add REST API endpoint", "success"),
            ("calc-2", "Fix calculator bug", "failed"),
            ("ui-1", "Update user interface", "success"),
        ]
        
        for entry_id, description, status in entries_data:
            entry = HistoryEntry(
                entry_id=entry_id,
                task_description=description,
                timestamp=datetime.now(),
                duration_seconds=10.0,
                status=status,
                output="Output"
            )
            manager.add_entry(entry)
        
        # Search for "calculator"
        results = manager.get_entries(search_query="calculator")
        
        assert len(results) == 2
        assert all("calculator" in entry.task_description.lower() for entry in results)
    
    def test_filter_by_status(self, manager):
        """Should filter by status. (Req 5.2)"""
        # Add entries with different statuses
        statuses = [
            ("success-1", "success"),
            ("failed-1", "failed"),
            ("success-2", "success"),
            ("cancelled-1", "cancelled"),
        ]
        
        for entry_id, status in statuses:
            entry = HistoryEntry(
                entry_id=entry_id,
                task_description=f"Task {entry_id}",
                timestamp=datetime.now(),
                duration_seconds=10.0,
                status=status,
                output="Output"
            )
            manager.add_entry(entry)
        
        # Filter by success
        success_entries = manager.get_entries(status_filter="success")
        assert len(success_entries) == 2
        assert all(e.status == "success" for e in success_entries)
        
        # Filter by failed
        failed_entries = manager.get_entries(status_filter="failed")
        assert len(failed_entries) == 1
        assert failed_entries[0].status == "failed"
    
    def test_filter_by_date_range(self, manager):
        """Should filter by date range."""
        now = datetime.now()
        
        # Add entries with different dates
        dates = [
            ("old", now - timedelta(days=10)),
            ("recent", now - timedelta(days=2)),
            ("new", now),
        ]
        
        for entry_id, timestamp in dates:
            entry = HistoryEntry(
                entry_id=entry_id,
                task_description=f"Task {entry_id}",
                timestamp=timestamp,
                duration_seconds=10.0,
                status="success",
                output="Output"
            )
            manager.add_entry(entry)
        
        # Filter by start date (last 5 days)
        start_date = now - timedelta(days=5)
        results = manager.get_entries(start_date=start_date)
        
        assert len(results) == 2
        assert all(e.timestamp >= start_date for e in results)
        
        # Filter by end date
        end_date = now - timedelta(days=3)
        results = manager.get_entries(end_date=end_date)
        
        assert len(results) == 1
        assert results[0].entry_id == "old"
    
    def test_delete_entry(self, manager, sample_entry):
        """Should delete specific entry. (Req 5.6)"""
        manager.add_entry(sample_entry)
        
        # Verify entry exists
        assert manager.get_entry_by_id(sample_entry.entry_id) is not None
        
        # Delete entry
        result = manager.delete_entry(sample_entry.entry_id)
        
        assert result is True
        assert manager.get_entry_by_id(sample_entry.entry_id) is None
    
    def test_delete_entry_returns_false_if_not_found(self, manager):
        """Should return False when deleting non-existent entry."""
        result = manager.delete_entry("non-existent")
        
        assert result is False
    
    def test_clear_all(self, manager):
        """Should delete all entries. (Req 5.7)"""
        # Add multiple entries
        for i in range(5):
            entry = HistoryEntry(
                entry_id=f"entry-{i}",
                task_description=f"Task {i}",
                timestamp=datetime.now(),
                duration_seconds=10.0,
                status="success",
                output="Output"
            )
            manager.add_entry(entry)
        
        # Verify entries exist
        assert len(manager.get_entries()) == 5
        
        # Clear all
        deleted_count = manager.clear_all()
        
        assert deleted_count == 5
        assert len(manager.get_entries()) == 0
    
    def test_purge_old_entries(self, manager):
        """Should delete entries older than specified days. (Req 14.8)"""
        now = datetime.now()
        
        # Add old entry (100 days ago)
        old_entry = HistoryEntry(
            entry_id="old",
            task_description="Old task",
            timestamp=now - timedelta(days=100),
            duration_seconds=10.0,
            status="success",
            output="Old output"
        )
        manager.add_entry(old_entry)
        
        # Add recent entry (10 days ago)
        recent_entry = HistoryEntry(
            entry_id="recent",
            task_description="Recent task",
            timestamp=now - timedelta(days=10),
            duration_seconds=5.0,
            status="success",
            output="Recent output"
        )
        manager.add_entry(recent_entry)
        
        # Add current entry
        current_entry = HistoryEntry(
            entry_id="current",
            task_description="Current task",
            timestamp=now,
            duration_seconds=3.0,
            status="success",
            output="Current output"
        )
        manager.add_entry(current_entry)
        
        # Purge entries older than 90 days
        deleted_count = manager.purge_old_entries(days=90)
        
        assert deleted_count == 1
        
        # Verify only recent and current entries remain
        entries = manager.get_entries()
        assert len(entries) == 2
        assert "old" not in [e.entry_id for e in entries]
    
    def test_export_to_json(self, manager, temp_db):
        """Should export history to JSON file. (Req 5.9)"""
        # Add test entries
        for i in range(3):
            entry = HistoryEntry(
                entry_id=f"entry-{i}",
                task_description=f"Task {i}",
                timestamp=datetime.now(),
                duration_seconds=float(i + 1),
                status="success",
                output=f"Output {i}"
            )
            manager.add_entry(entry)
        
        # Export to JSON
        export_path = Path(temp_db).parent / 'export.json'
        result = manager.export_to_json(str(export_path))
        
        assert result is True
        assert export_path.exists()
        
        # Verify JSON content
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'export_date' in data
        assert data['entry_count'] == 3
        assert len(data['entries']) == 3
        assert data['entries'][0]['entry_id'] in ['entry-0', 'entry-1', 'entry-2']
    
    def test_export_to_csv(self, manager, temp_db):
        """Should export history to CSV file. (Req 5.9)"""
        # Add test entries
        for i in range(3):
            entry = HistoryEntry(
                entry_id=f"entry-{i}",
                task_description=f"Task {i}",
                timestamp=datetime.now(),
                duration_seconds=float(i + 1),
                status="success",
                output=f"Output {i}"
            )
            manager.add_entry(entry)
        
        # Export to CSV
        export_path = Path(temp_db).parent / 'export.csv'
        result = manager.export_to_csv(str(export_path))
        
        assert result is True
        assert export_path.exists()
        
        # Verify CSV content
        with open(export_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Header + 3 data rows
        assert len(rows) == 4
        assert rows[0][0] == 'Entry ID'
        assert rows[1][0] in ['entry-0', 'entry-1', 'entry-2']
    
    def test_get_statistics(self, manager):
        """Should return accurate statistics."""
        # Add entries with different statuses and durations
        entries_data = [
            ("success-1", "success", 10.0),
            ("success-2", "success", 20.0),
            ("failed-1", "failed", 5.0),
            ("cancelled-1", "cancelled", 2.0),
        ]
        
        for entry_id, status, duration in entries_data:
            entry = HistoryEntry(
                entry_id=entry_id,
                task_description=f"Task {entry_id}",
                timestamp=datetime.now(),
                duration_seconds=duration,
                status=status,
                output="Output"
            )
            manager.add_entry(entry)
        
        # Get statistics
        stats = manager.get_statistics()
        
        assert stats['total_entries'] == 4
        assert stats['success_count'] == 2
        assert stats['failed_count'] == 1
        assert stats['cancelled_count'] == 1
        assert stats['total_duration_seconds'] == 37.0
        assert stats['average_duration_seconds'] == 9.25
    
    def test_empty_database_statistics(self, manager):
        """Should handle statistics for empty database."""
        stats = manager.get_statistics()
        
        assert stats['total_entries'] == 0
        assert stats['success_count'] == 0
        assert stats['failed_count'] == 0
        assert stats['cancelled_count'] == 0
        assert stats['total_duration_seconds'] == 0
        assert stats['average_duration_seconds'] == 0
    
    def test_default_db_path(self):
        """Should use default database path in user home directory."""
        manager = GUIHistoryManager()
        
        db_path = Path(manager.db_path)
        
        assert '.local-ai-dev' in str(db_path)
        assert db_path.name == 'history.db'
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    def test_concurrent_entries(self, manager):
        """Should handle adding multiple entries correctly."""
        entries = []
        for i in range(10):
            entry = HistoryEntry(
                entry_id=f"concurrent-{i}",
                task_description=f"Concurrent task {i}",
                timestamp=datetime.now(),
                duration_seconds=float(i),
                status="success",
                output=f"Output {i}"
            )
            entries.append(entry)
            manager.add_entry(entry)
        
        # Retrieve all
        retrieved = manager.get_entries(limit=20)
        
        assert len(retrieved) == 10
        retrieved_ids = [e.entry_id for e in retrieved]
        for entry in entries:
            assert entry.entry_id in retrieved_ids


class TestHistoryEntryEdgeCases:
    """Test edge cases for HistoryEntry."""
    
    def test_entry_with_none_timestamp(self):
        """Should handle None timestamp gracefully."""
        entry = HistoryEntry(
            entry_id="test",
            task_description="Test",
            timestamp=None,
            duration_seconds=0.0,
            status="success",
            output="Output"
        )
        
        result = entry.to_dict()
        assert result['timestamp'] is None
    
    def test_entry_with_empty_config_snapshot(self):
        """Should handle empty config snapshot."""
        entry = HistoryEntry(
            entry_id="test",
            task_description="Test",
            timestamp=datetime.now(),
            duration_seconds=0.0,
            status="success",
            output="Output",
            config_snapshot={}
        )
        
        result = entry.to_dict()
        assert result['config_snapshot'] == {}
    
    def test_entry_with_special_characters(self):
        """Should handle special characters in strings."""
        entry = HistoryEntry(
            entry_id="test-special",
            task_description="Task with 'quotes' and \"double quotes\" and \n newlines",
            timestamp=datetime.now(),
            duration_seconds=10.0,
            status="success",
            output="Output with unicode: 日本語, emoji: 🚀"
        )
        
        result = entry.to_dict()
        assert "quotes" in result['task_description']
        assert "🚀" in result['output']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
