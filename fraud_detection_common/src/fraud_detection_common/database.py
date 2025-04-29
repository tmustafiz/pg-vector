import os
from typing import List, Tuple, Optional
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/fraud_db')
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def store_application(self, merchant_id: str, application_data: dict) -> int:
        """Store a merchant application and return its ID"""
        session = self.Session()
        try:
            # Insert application data
            result = session.execute(text("""
                INSERT INTO merchant_applications (
                    merchant_id, owner_ssn, business_fed_tax_id, owner_drivers_license,
                    business_phone_number, owner_phone_number, email, address_line1,
                    city, state, zip_code, country, website
                ) VALUES (
                    :merchant_id, :owner_ssn, :business_fed_tax_id, :owner_drivers_license,
                    :business_phone_number, :owner_phone_number, :email, :address_line1,
                    :city, :state, :zip_code, :country, :website
                ) RETURNING id
            """), application_data)
            
            application_id = result.scalar()
            session.commit()
            return application_id
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def store_embedding(self, application_id: int, embedding: np.ndarray, 
                       fraud_reason: Optional[str] = None):
        """Store a merchant embedding in the database"""
        session = self.Session()
        try:
            session.execute(text("""
                INSERT INTO merchant_embeddings 
                (merchant_application_id, embedding, fraud_reason)
                VALUES (:application_id, :embedding, :fraud_reason)
            """), {
                'application_id': application_id,
                'embedding': embedding.tolist(),  # Convert numpy array to list for pgvector
                'fraud_reason': fraud_reason
            })
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
            result = session.execute(text("""
                SELECT 
                    ma.merchant_id,
                    1 - (me.embedding <=> :embedding) as similarity,
                    json_build_object(
                        'owner_ssn', ma.owner_ssn,
                        'business_fed_tax_id', ma.business_fed_tax_id,
                        'owner_drivers_license', ma.owner_drivers_license,
                        'business_phone_number', ma.business_phone_number,
                        'owner_phone_number', ma.owner_phone_number,
                        'email', ma.email,
                        'address_line1', ma.address_line1,
                        'city', ma.city,
                        'state', ma.state,
                        'zip_code', ma.zip_code,
                        'country', ma.country,
                        'website', ma.website
                    ) as application_data,
                    me.fraud_reason
                FROM merchant_embeddings me
                JOIN merchant_applications ma ON me.merchant_application_id = ma.id
                WHERE 1 - (me.embedding <=> :embedding) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """), {
                'embedding': embedding.tolist(),  # Convert numpy array to list for pgvector
                'threshold': threshold,
                'limit': limit
            })
            
            return result.fetchall()
            
        finally:
            session.close()

    def close(self):
        """Close the database connection"""
        self.engine.dispose() 