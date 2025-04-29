from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class MerchantApplication(BaseModel):
    """Model for merchant application data"""
    owner_ssn: str = Field(..., description="Owner's Social Security Number")
    business_fed_tax_id: str = Field(..., description="Business Federal Tax ID")
    owner_drivers_license: str = Field(..., description="Owner's Driver's License Number")
    business_phone_number: str = Field(..., description="Business Phone Number")
    owner_phone_number: str = Field(..., description="Owner's Phone Number")
    email: str = Field(..., description="Contact Email")
    address_line1: str = Field(..., description="Street Address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="ZIP Code")
    country: str = Field(..., description="Country")
    website: Optional[str] = Field(None, description="Business Website")

class FieldMatch(BaseModel):
    """Model for matching fields between applications"""
    field: str
    new_value: str
    fraud_value: str
    similarity: float

class FraudCase(BaseModel):
    """Model for fraud case details"""
    merchant_id: str
    vector_similarity: float
    fraud_reason: Optional[str]
    matching_fields: List[FieldMatch]

class EvaluationResponse(BaseModel):
    """Model for evaluation response"""
    decision: str  # "Approve", "Review", or "Decline"
    vector_similarity: float
    field_matches: List[FraudCase] 