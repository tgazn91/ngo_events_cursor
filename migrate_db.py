# Database Migration Script
# Purpose: This script handles database schema migrations for the NGO Events application.
# It currently ensures the 'eposter' column exists in the event table, which is used
# to store paths to event poster images.
#
# Usage: 
# 1. Make sure the Flask application (app.py) is configured correctly
# 2. Run this script directly: python migrate_db.py
# 3. The script will automatically check and add missing columns if needed
#
# Note: This script should be run whenever there are database schema changes
# that need to be propagated to existing databases.

from app import app, db
import sqlite3

def migrate():
    """
    Performs database migrations to ensure all necessary columns exist.
    Currently handles:
    - Adding 'eposter' column to the event table if it doesn't exist
    
    Returns:
        None
    
    Raises:
        Exception: If there's an error during migration process
    """
    print("Starting database migration...")
    try:
        # Create a database connection within the Flask application context
        with app.app_context():
            # Connect to the SQLite database file
            conn = sqlite3.connect('instance/events.db')
            cursor = conn.cursor()
            
            # Get information about columns in the event table
            cursor.execute("PRAGMA table_info(event)")
            columns = cursor.fetchall()
            # Extract just the column names from the table info
            column_names = [column[1] for column in columns]
            
            # Check and add the eposter column if it doesn't exist
            if 'eposter' not in column_names:
                print("Adding eposter column to event table...")
                cursor.execute('ALTER TABLE event ADD COLUMN eposter TEXT;')
                conn.commit()
                print("Migration completed successfully!")
            else:
                print("eposter column already exists")
                
            # Clean up by closing the database connection
            conn.close()
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        # Ensure the connection is closed even if an error occurs
        if 'conn' in locals():
            conn.close()

# Allow the script to be run directly
if __name__ == '__main__':
    migrate()