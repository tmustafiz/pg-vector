import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fraud_detection_common.config_schema import ModelConfig
from fraud_detection_common.dynamic_model import DynamicModelGenerator

def setup_database():
    """Setup database tables and indexes using dynamic model generation"""
    # Load configuration
    config_path = Path(__file__).parent.parent.parent / "config" / "model_config.json"
    with open(config_path, 'r') as f:
        config = ModelConfig.parse_raw(f.read())
    
    # Get database connection details from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fraud_db')
    
    # Create engine
    engine = create_engine(db_url)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create pgvector extension if not exists
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Generate and create model
        model_generator = DynamicModelGenerator(config)
        model = model_generator.get_sqlalchemy_model()
        model.metadata.create_all(engine)
        
        # Create vector index
        session.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_{config.name}_embedding 
            ON {config.name} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))
        
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