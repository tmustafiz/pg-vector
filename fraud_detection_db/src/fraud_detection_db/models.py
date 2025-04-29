from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import vector
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class MerchantApplication(Base):
    """SQLAlchemy model for merchant applications"""
    __tablename__ = 'merchant_applications'

    id = Column(Integer, primary_key=True)
    merchant_id = Column(String(255), unique=True, nullable=False)
    owner_ssn = Column(String(255), nullable=False)
    business_fed_tax_id = Column(String(255), nullable=False)
    owner_drivers_license = Column(String(255), nullable=False)
    business_phone_number = Column(String(255), nullable=False)
    owner_phone_number = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10), nullable=False)
    country = Column(String(2), nullable=False)
    website = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to embeddings
    embedding = relationship("MerchantEmbedding", back_populates="application", uselist=False)

class MerchantEmbedding(Base):
    """SQLAlchemy model for merchant embeddings"""
    __tablename__ = 'merchant_embeddings'

    id = Column(Integer, primary_key=True)
    merchant_application_id = Column(Integer, ForeignKey('merchant_applications.id'), nullable=False)
    embedding = Column(vector(384), nullable=False)  # Using pgvector's vector type with 384 dimensions
    fraud_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to application
    application = relationship("MerchantApplication", back_populates="embedding") 