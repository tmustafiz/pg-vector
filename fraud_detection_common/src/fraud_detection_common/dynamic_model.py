from typing import Dict, Any, Type, List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ARRAY, create_engine, ForeignKey, Table, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, UserDefinedType
from pydantic import BaseModel, create_model
from datetime import datetime
from .config_schema import ModelConfig, FieldConfig
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import numpy as np
from .database_config import load_database_config, TableConfig, DatabaseConfig

Base = declarative_base()

class Vector(UserDefinedType):
    """PostgreSQL vector type for storing embeddings"""
    
    def get_col_spec(self, **kw):
        return "vector"
    
    def bind_processor(self, dialect):
        def process(value):
            return value
        return process
    
    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process

class DynamicModelGenerator:
    """Generates SQLAlchemy models dynamically based on configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.db_config = load_database_config(config_path)
        self.engine = create_engine(
            self.db_config.connection.url,
            pool_size=self.db_config.connection.pool_size,
            max_overflow=self.db_config.connection.max_overflow,
            pool_timeout=self.db_config.connection.pool_timeout,
            pool_recycle=self.db_config.connection.pool_recycle
        )
        self.metadata = MetaData(schema=self.db_config.connection.schema)
        self.Base = declarative_base(metadata=self.metadata)
        self.Session = sessionmaker(bind=self.engine)
        
    def _get_sqlalchemy_type(self, field):
        """Map field type to SQLAlchemy type"""
        type_mapping = {
            'string': String,
            'integer': Integer,
            'float': Float,
            'boolean': Boolean,
            'datetime': DateTime
        }
        return type_mapping.get(field['type'], String)
    
    def get_sqlalchemy_model(self, Base=None):
        """Generate SQLAlchemy model from configuration"""
        if Base is None:
            Base = declarative_base()

        field_definitions = {}
        for field in self.db_config.tables.values():
            for f in field.fields:
                field_type = self._get_sqlalchemy_type(f)
                field_definitions[f['name']] = Column(field_type, nullable=True)

        # Add common fields
        field_definitions.update({
            'merchant_id': Column(String, primary_key=True),
            'embedding': Column(Vector),
            'fraud_reason': Column(String, nullable=True),
            'created_at': Column(DateTime(timezone=True), server_default=func.now()),
            'updated_at': Column(DateTime(timezone=True), onupdate=func.now())
        })

        # Create model class
        model = type(
            'MerchantFraud',  # Use a fixed name since we only have one table
            (Base,),
            {
                '__tablename__': 'merchant_fraud',  # Use the table name from config
                **field_definitions
            }
        )

        return model
    
    def _create_pydantic_model(self) -> Type[BaseModel]:
        """Create Pydantic model dynamically"""
        field_definitions = {}
        
        for field in self.db_config.tables.values():
            for f in field.fields:
                field_type = {
                    "string": str,
                    "integer": int,
                    "float": float,
                    "boolean": bool,
                    "datetime": datetime
                }[f.type]
                
                field_definitions[f.name] = (
                    field_type if f.required else Optional[field_type],
                    ... if f.required else None
                )
        
        return create_model(
            f"{self.db_config.name.capitalize()}Schema",
            **field_definitions
        )
    
    def get_pydantic_model(self) -> Type[BaseModel]:
        """Get the generated Pydantic model"""
        return self._create_pydantic_model()

    def create_tables(self):
        """Create all tables defined in the configuration"""
        for table_name, table_config in self.db_config.tables.items():
            self._create_table(table_name, table_config)
        self.metadata.create_all(self.engine)

    def _create_table(self, table_name: str, table_config: TableConfig):
        """Create a single table with its indexes"""
        # Create the vector extension first
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

        # Get embedding dimension from config
        embedding_dim = 384  # Default value
        if hasattr(self.db_config, 'embedding_dim'):
            embedding_dim = self.db_config.embedding_dim

        # Build the field definitions
        field_definitions = []
        for field in table_config.fields:
            field_type = {
                'string': 'VARCHAR',
                'integer': 'INTEGER',
                'float': 'FLOAT',
                'boolean': 'BOOLEAN',
                'datetime': 'TIMESTAMP WITH TIME ZONE'
            }.get(field['type'], 'VARCHAR')
            field_definitions.append(f"{field['name']} {field_type}")

        # Drop and create the table with vector dimensions
        with self.engine.connect() as conn:
            # Drop the table if it exists
            conn.execute(text(f"DROP TABLE IF EXISTS {table_config.schema}.{table_name} CASCADE;"))
            conn.commit()

            # Create the table
            fields_sql = ',\n'.join(field_definitions)
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_config.schema}.{table_name} (
                    id SERIAL PRIMARY KEY,
                    {fields_sql},
                    merchant_id VARCHAR NOT NULL UNIQUE,
                    embedding vector({embedding_dim}),
                    fraud_reason VARCHAR,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()

            # Create indexes
            for index_config in table_config.indexes:
                if index_config.type == 'ivfflat':
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index_config.name}
                        ON {table_config.schema}.{table_name} USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = {index_config.lists or 100});
                    """))
                elif index_config.type == 'btree' and index_config.column:
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index_config.name}
                        ON {table_config.schema}.{table_name} ({index_config.column});
                    """))
                conn.commit()

            # Create trigger for updating updated_at
            conn.execute(text(f"""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';

                DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_config.schema}.{table_name};
                CREATE TRIGGER update_{table_name}_updated_at
                    BEFORE UPDATE ON {table_config.schema}.{table_name}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """))
            conn.commit()

    def get_session(self):
        """Get a new database session"""
        return self.Session()

    def close(self):
        """Close the database connection"""
        self.engine.dispose() 