from typing import Dict, Any, Type, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, UserDefinedType
from pydantic import BaseModel, create_model
from datetime import datetime
from .config_schema import ModelConfig, FieldConfig

Base = declarative_base()

class Vector(UserDefinedType):
    """PostgreSQL vector type for storing embeddings"""
    
    def get_col_spec(self, **kw):
        return "vector"
    
    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return value
        return process
    
    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return value
        return process

class DynamicModelGenerator:
    """Generates SQLAlchemy models dynamically based on configuration"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        
    def get_sqlalchemy_model(self):
        """Generate SQLAlchemy model based on configuration"""
        
        # Create model attributes
        attrs = {
            '__tablename__': self.config.name,
            'merchant_id': Column(String(36), primary_key=True),
            'embedding': Column(Vector),
            'fraud_reason': Column(Text, nullable=True)
        }
        
        # Add columns for each field in config
        for field in self.config.fields:
            attrs[field.name] = Column(String(255), nullable=True)
        
        # Create model class
        model = type(
            self.config.name.title(),
            (Base,),
            attrs
        )
        
        return model
    
    def _create_pydantic_model(self) -> Type[BaseModel]:
        """Create Pydantic model dynamically"""
        field_definitions = {}
        
        for field in self.config.fields:
            field_type = {
                "string": str,
                "integer": int,
                "float": float,
                "boolean": bool,
                "datetime": datetime
            }[field.type]
            
            field_definitions[field.name] = (
                field_type if field.required else Optional[field_type],
                ... if field.required else None
            )
        
        return create_model(
            f"{self.config.name.capitalize()}Schema",
            **field_definitions
        )
    
    def get_pydantic_model(self) -> Type[BaseModel]:
        """Get the generated Pydantic model"""
        return self._create_pydantic_model() 