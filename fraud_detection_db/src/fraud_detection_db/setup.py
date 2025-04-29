import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base

def setup_database():
    """Setup database tables and indexes using external SQL files"""
    # Get database connection details from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fraud_db')
    
    # Create engine
    engine = create_engine(db_url)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get the directory containing this file
        current_dir = Path(__file__).parent.parent.parent
        
        # Read and execute each SQL file in order
        sql_files = [
            current_dir / 'sql' / '01_create_extensions.sql',
            current_dir / 'sql' / '02_create_tables.sql',
            current_dir / 'sql' / '03_create_indexes.sql'
        ]
        
        for sql_file in sql_files:
            with open(sql_file, 'r') as f:
                sql = f.read()
                session.execute(text(sql))
        
        session.commit()
        print("Database setup completed successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error during database setup: {e}")
        raise
        
    finally:
        session.close()

if __name__ == "__main__":
    setup_database() 