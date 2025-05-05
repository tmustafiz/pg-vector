from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import json
import os

class ConnectionConfig(BaseModel):
    url: str
    schema: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int

class IndexConfig(BaseModel):
    name: str
    type: str
    column: str
    lists: Optional[int] = None

class TableConfig(BaseModel):
    schema: str
    fields: List[Dict[str, str]] = Field(default_factory=list)
    indexes: List[IndexConfig] = Field(default_factory=list)

class DatabaseConfig(BaseModel):
    """Configuration for the entire database"""
    connection: ConnectionConfig
    tables: Dict[str, TableConfig]
    extensions: List[str] = Field(default_factory=list)

def load_database_config(config_path: Optional[str] = None) -> DatabaseConfig:
    """Load database configuration from file and environment variables"""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "database_config.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Database config file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    # Override connection settings with environment variables if they exist
    if 'connection' in config_data:
        for key in ['url', 'schema', 'pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle']:
            env_key = f"DATABASE_{key.upper()}" if key == 'url' else f"DB_{key.upper()}"
            if env_key in os.environ:
                config_data['connection'][key] = os.environ[env_key]
    
    return DatabaseConfig.model_validate(config_data) 