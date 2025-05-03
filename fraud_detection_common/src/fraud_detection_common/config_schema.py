from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

class FieldConfig(BaseModel):
    """Configuration for a single field in the model"""
    name: str
    type: Literal["string", "integer", "float", "boolean", "datetime"]
    required: bool = True
    description: Optional[str] = None
    validation_rules: Optional[Dict] = None

class FeatureGroup(BaseModel):
    """Configuration for a group of features"""
    name: str
    description: Optional[str] = None
    fields: List[str]  # List of field names that belong to this feature group
    preprocessing: Optional[Dict] = None  # Custom preprocessing steps for this group
    weight: float = 1.0  # Weight for this feature group in similarity calculation

class ModelConfig(BaseModel):
    """Configuration for the entire model"""
    name: str
    description: Optional[str] = None
    fields: List[FieldConfig]
    feature_groups: List[FeatureGroup]
    embedding_dim: int = Field(default=384, ge=32, le=1024)
    similarity_thresholds: Dict[str, float] = Field(
        default={
            "decline": 0.8,
            "review": 0.6
        }
    )
    preprocessing_config: Optional[Dict] = None  # Global preprocessing configuration

# Example configuration
EXAMPLE_CONFIG = {
    "name": "merchant_fraud_detection",
    "description": "Configuration for merchant fraud detection model",
    "fields": [
        {
            "name": "owner_ssn",
            "type": "string",
            "required": True,
            "description": "Owner's Social Security Number",
            "validation_rules": {
                "pattern": r"^\d{3}-\d{2}-\d{4}$"
            }
        },
        {
            "name": "business_fed_tax_id",
            "type": "string",
            "required": True
        },
        {
            "name": "email",
            "type": "string",
            "required": True,
            "validation_rules": {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            }
        }
    ],
    "feature_groups": [
        {
            "name": "identity_features",
            "description": "Features related to business and owner identity",
            "fields": ["owner_ssn", "business_fed_tax_id"],
            "weight": 1.5
        },
        {
            "name": "contact_features",
            "description": "Features related to contact information",
            "fields": ["email", "phone_number"],
            "preprocessing": {
                "normalize": True,
                "hash": True
            }
        }
    ],
    "embedding_dim": 384,
    "similarity_thresholds": {
        "decline": 0.8,
        "review": 0.6
    }
} 