"""
GUI History Manager - Task execution history persistence

This module provides persistent storage and querying of task execution history
using SQLite database.
"""

import os
import json
import csv
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from .platform_paths import PlatformPaths


@dataclass
class HistoryEntry:
    """Single task execution history entry."""
    entry_id: str  # UUID
    task_description: str
    timestamp: datetime
    duration_seconds: float
    status: str  # 'success', 'failed', 'cancelled'
    output: str  # Truncated to max 10MB
    error_message: Optional[str] = None
    config_snapshot: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'entry_id': self.entry_id,
            'task_description': self.task_description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'output': self.output,
            'error_message': self.error_message,
            'config_snapshot': self.config_snapshot
        }
    
    @staticmethod
    def from_db_row(row: tuple) -> 'HistoryEntry':
        """Create HistoryEntry from database row."""
        return HistoryEntry(
            entry_id=row[0],
            task_description=row[1],
            timestamp=datetime.fromisoformat(row[2]) if row[2] else None,
            duration_seconds=row[3],
            status=row[4],
            output=row[5],
            error_message=row[6],
            config_snapshot=json.loads(row[7]) if row[7] else None
        )


class GUIHistoryManager:
    """
    Task execution history manager with SQLite backend.
    
    Provides:
    - Persistent storage of task executions
    - Search and filtering capabilities
    - Export to JSON and CSV
    - Automatic purging of old entries
    """
    
    # Maximum output size to store (10MB)
    MAX_OUTPUT_SIZE = 10 * 1024 * 1024
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize history manager.
        
        Args:
            db_path: Path to SQLite database (default: platform-appropriate data directory)
        
        Requirements: 15.7
        """
        self.db_path = db_path or str(PlatformPaths.get_history_db_path())
        self._ensure_db_directory()
        self._init_database()
    
    def add_entry(self, entry: HistoryEntry) -> str:
        """
        Add a new history entry.
        
        Args:
            entry: HistoryEntry object
            
        Returns:
            entry_id: UUID of the created entry
        """
        # Generate UUID if not provided
        if not entry.entry_id:
            entry.entry_id = str(uuid.uuid4())
        
        # Truncate output if too large
        if entry.output and len(entry.output) > self.MAX_OUTPUT_SIZE:
            entry.output = entry.output[:self.MAX_OUTPUT_SIZE] + "\n... (output truncated)"
        
        # Convert config snapshot to JSON
        config_json = json.dumps(entry.config_snapshot) if entry.config_snapshot else None
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history_entries (
                    entry_id, task_description, timestamp, duration_seconds,
                    status, output, error_message, config_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.entry_id,
                entry.task_description,
                entry.timestamp.isoformat() if entry.timestamp else None,
                entry.duration_seconds,
                entry.status,
                entry.output,
                entry.error_message,
                config_json
            ))
            conn.commit()
            return entry.entry_id
        finally:
            conn.close()
    
    def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        search_query: Optional[str] = None,
        status_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoryEntry]:
        """
        Retrieve history entries with optional filtering and pagination.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip (for pagination)
            search_query: Filter by task description (case-insensitive)
            status_filter: Filter by status ('success', 'failed', 'cancelled')
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of HistoryEntry objects, sorted by timestamp (newest first)
        
        Requirements: 5.1, 5.2, 5.3, 18.1
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM history_entries WHERE 1=1"
            params = []
            
            if search_query:
                query += " AND task_description LIKE ?"
                params.append(f"%{search_query}%")
            
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            # Add LIMIT and OFFSET for pagination (Req 18.1)
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [HistoryEntry.from_db_row(row) for row in rows]
        finally:
            conn.close()
    
    def get_entry_by_id(self, entry_id: str) -> Optional[HistoryEntry]:
        """
        Get a specific history entry by ID.
        
        Args:
            entry_id: UUID of the entry
            
        Returns:
            HistoryEntry if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM history_entries WHERE entry_id = ?",
                (entry_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return HistoryEntry.from_db_row(row)
            return None
        finally:
            conn.close()
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a history entry.
        
        Args:
            entry_id: UUID of the entry to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history_entries WHERE entry_id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def clear_all(self) -> int:
        """
        Delete all history entries.
        
        Returns:
            Number of entries deleted
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history_entries")
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    def purge_old_entries(self, days: int = 90) -> int:
        """
        Delete entries older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of entries deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM history_entries WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    def export_to_json(self, filepath: str) -> bool:
        """
        Export all history to JSON file.
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful
        """
        try:
            entries = self.get_entries(limit=1000000)  # Get all entries
            
            data = {
                'export_date': datetime.now().isoformat(),
                'entry_count': len(entries),
                'entries': [entry.to_dict() for entry in entries]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Failed to export to JSON: {e}")
            return False
    
    def export_to_csv(self, filepath: str) -> bool:
        """
        Export all history to CSV file.
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful
        """
        try:
            entries = self.get_entries(limit=1000000)  # Get all entries
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Entry ID',
                    'Task Description',
                    'Timestamp',
                    'Duration (seconds)',
                    'Status',
                    'Error Message',
                    'Output'
                ])
                
                # Write entries
                for entry in entries:
                    writer.writerow([
                        entry.entry_id,
                        entry.task_description,
                        entry.timestamp.isoformat() if entry.timestamp else '',
                        entry.duration_seconds,
                        entry.status,
                        entry.error_message or '',
                        entry.output[:1000] + '...' if len(entry.output) > 1000 else entry.output
                    ])
            
            return True
        except Exception as e:
            print(f"Failed to export to CSV: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get history statistics.
        
        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM history_entries")
            total_entries = cursor.fetchone()[0]
            
            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM history_entries 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Duration statistics
            cursor.execute("""
                SELECT 
                    SUM(duration_seconds),
                    AVG(duration_seconds)
                FROM history_entries
            """)
            duration_row = cursor.fetchone()
            total_duration = duration_row[0] or 0
            avg_duration = duration_row[1] or 0
            
            return {
                'total_entries': total_entries,
                'success_count': status_counts.get('success', 0),
                'failed_count': status_counts.get('failed', 0),
                'cancelled_count': status_counts.get('cancelled', 0),
                'total_duration_seconds': total_duration,
                'average_duration_seconds': avg_duration
            }
        finally:
            conn.close()
    
    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists.
        
        Requirements: 15.7
        """
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize database schema if not exists."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history_entries (
                    entry_id TEXT PRIMARY KEY,
                    task_description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL,
                    status TEXT NOT NULL,
                    output TEXT,
                    error_message TEXT,
                    config_snapshot TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON history_entries(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON history_entries(status)
            """)
            
            conn.commit()
        finally:
            conn.close()
