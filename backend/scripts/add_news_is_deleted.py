"""Script to add is_deleted column to news table if not exists"""
import os
from sqlalchemy import create_engine, text

def add_is_deleted_column():
    """Add is_deleted column to news table if not exists"""
    
    # Get database URL from environment or use default
    # Use the actual database file that's being used by the app
    db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./data/app.db')
    # For SQLite, we can use synchronous engine for inspection
    sync_url = db_url.replace('sqlite+aiosqlite://', 'sqlite://')
    engine = create_engine(sync_url)
    
    with engine.begin() as conn:
        # List all tables
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"All tables in database: {tables}")
        
        # Check if news table exists
        news_exists = 'news' in tables
        
        if not news_exists:
            print("news table does not exist!")
            # Check for similar table names
            similar_tables = [t for t in tables if 'news' in t.lower()]
            if similar_tables:
                print(f"Similar tables found: {similar_tables}")
            return
        
        # Get current columns
        result = conn.execute(text("PRAGMA table_info(news)"))
        columns = [row[1] for row in result.fetchall()]
        
        print(f"Current columns in news table: {columns}")
        
        # Check if is_deleted exists
        has_is_deleted = 'is_deleted' in columns
        print(f"Has is_deleted column: {has_is_deleted}")
        
        if not has_is_deleted:
            # Add column
            conn.execute(text('ALTER TABLE news ADD COLUMN is_deleted BOOLEAN DEFAULT 0'))
            print("Successfully added is_deleted column!")
        else:
            print("is_deleted column already exists!")

if __name__ == '__main__':
    add_is_deleted_column()