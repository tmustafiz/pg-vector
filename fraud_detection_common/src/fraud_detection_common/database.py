import os
from typing import List, Tuple, Optional, Type
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .config_schema import ModelConfig
from .dynamic_model import DynamicModelGenerator

load_dotenv()

class Database:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model_generator = DynamicModelGenerator(config)
        self.sqlalchemy_model = self.model_generator.get_sqlalchemy_model()
        self.pydantic_model = self.model_generator.get_pydantic_model()
        
        # Initialize database connection
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fraud_db')
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def store_application(self, merchant_id: str, application_data: dict):
        """Store a merchant application"""
        session = self.Session()
        try:
            # Create application instance
            application = self.sqlalchemy_model(
                merchant_id=merchant_id,
                **application_data
            )
            
            # Add to session and commit
            session.add(application)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def store_embedding(self, application_id: str, embedding: np.ndarray, 
                       fraud_reason: Optional[str] = None):
        """Store a merchant embedding in the database"""
        session = self.Session()
        try:
            # Update the application with embedding
            application = session.query(self.sqlalchemy_model).filter_by(merchant_id=application_id).first()
            if application:
                application.embedding = embedding.tolist()
                if fraud_reason:
                    application.fraud_reason = fraud_reason
                session.commit()
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def find_similar_cases(self, embedding: np.ndarray, threshold: float = 0.3, 
                          limit: int = 5) -> List[Tuple[str, float, dict, Optional[str]]]:
        """Find similar cases using pgvector cosine similarity"""
        session = self.Session()
        try:
            result = session.execute(text(f"""
                SELECT 
                    merchant_id,
                    1 - (embedding <=> :embedding) as similarity,
                    to_jsonb({self.config.name}) as application_data,
                    fraud_reason
                FROM {self.config.name}
                WHERE 1 - (embedding <=> :embedding) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """), {
                'embedding': embedding.tolist(),
                'threshold': threshold,
                'limit': limit
            })
            
            return result.fetchall()
            
        finally:
            session.close()

    def close(self):
        """Close the database connection"""
        self.engine.dispose() 