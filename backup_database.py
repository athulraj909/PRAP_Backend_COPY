"""
Database Backup Script for PRAP Backend
Safely backs up existing database before migration
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """
    Creates a timestamped backup of the SQLite database
    """
    # Get the project directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    db_path = BASE_DIR / 'db.sqlite3'
    
    # Create backups directory
    backup_dir = BASE_DIR / 'database_backups'
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'db.sqlite3.backup_{timestamp}'
    
    try:
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up successfully: {backup_path}")
        print(f"📁 Backup location: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

if __name__ == '__main__':
    print("🔄 Starting database backup...")
    backup_database()
    print("✨ Backup process completed!")