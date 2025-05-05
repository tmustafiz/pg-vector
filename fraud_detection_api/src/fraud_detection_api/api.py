from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, create_model
from typing import Optional, Dict, Any, List
from fraud_detection_common.database import Database
from fraud_detection_common.config import load_config
from fraud_detection_common.dynamic_model import DynamicModelGenerator
import uvicorn
import os
from collections import defaultdict

app = FastAPI(title="Fraud Detection API")

def get_model_generator():
    """Dependency to get the model generator"""
    config_path = os.getenv("FRAUD_DETECTION_CONFIG", "/app/config/database_config.json")
    model_generator = DynamicModelGenerator(config_path)
    try:
        yield model_generator
    finally:
        model_generator.close()

def get_merchant_model(model_generator: DynamicModelGenerator = Depends(get_model_generator)):
    """Dependency to get the merchant model"""
    table_config = next(iter(model_generator.db_config.tables.values()))
    fields = {field['name']: (str, ...) for field in table_config.fields}
    # Add merchant_id to the fields
    fields['merchant_id'] = (str, ...)
    return create_model('MerchantApplication', **fields)

def get_table_fields(model_generator: DynamicModelGenerator = Depends(get_model_generator)):
    """Dependency to get the table fields"""
    table_config = next(iter(model_generator.db_config.tables.values()))
    return {field['name']: field['type'] for field in table_config.fields}

def check_field_patterns(value: str, field_name: str, field_type: str) -> List[str]:
    """Check for patterns in field values based on field type"""
    reasons = []
    
    # Basic format validation based on field type
    if field_type == 'string':
        if not value.strip():
            reasons.append(f"Empty {field_name}")
    
    # Add more type-specific validations here if needed
    
    return reasons

@app.get("/schema")
async def get_schema(
    model_generator: DynamicModelGenerator = Depends(get_model_generator),
    merchant_model: type = Depends(get_merchant_model)
):
    """Get the API schema"""
    try:
        # Get the model's schema
        model_schema = merchant_model.model_json_schema()
        
        return {
            "endpoints": {
                "/predict": {
                    "method": "POST",
                    "description": "Submit a merchant application for fraud detection",
                    "request": {
                        "type": "object",
                        "properties": model_schema["properties"],
                        "required": model_schema["required"]
                    },
                    "response": {
                        "type": "object",
                        "properties": {
                            "merchant_id": {
                                "type": "string",
                                "description": "The merchant ID from the request"
                            },
                            "is_fraudulent": {
                                "type": "boolean",
                                "description": "Whether the application was flagged as fraudulent"
                            },
                            "fraud_reasons": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of reasons why the application was flagged as fraudulent"
                            },
                            "field_matches": {
                                "type": "object",
                                "description": "Fields that matched with existing applications and their merchant IDs"
                            }
                        }
                    }
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
async def predict_fraud(
    application: Dict[str, Any],
    model_generator: DynamicModelGenerator = Depends(get_model_generator),
    merchant_model: type = Depends(get_merchant_model),
    table_fields: Dict[str, str] = Depends(get_table_fields)
):
    """Predict fraud for a merchant application"""
    try:
        # Validate the application data
        merchant_application = merchant_model(**application)
        
        # Get the session
        session = model_generator.get_session()
        
        try:
            # Get the table
            table = model_generator.get_sqlalchemy_model()
            
            # Check for fraud patterns
            fraud_reasons = []
            field_matches = defaultdict(list)
            
            # Check each field for matches and patterns
            for field_name, field_type in table_fields.items():
                field_value = getattr(merchant_application, field_name)
                
                # Check for patterns
                pattern_reasons = check_field_patterns(field_value, field_name, field_type)
                fraud_reasons.extend(pattern_reasons)
                
                # Check for duplicate values
                matches = session.query(table).filter(
                    getattr(table, field_name) == field_value
                ).all()
                
                if len(matches) > 0:
                    field_matches[field_name].extend([m.merchant_id for m in matches])
                    fraud_reasons.append(f"Duplicate {field_name} found in previous applications")
            
            response = {
                "merchant_id": getattr(merchant_application, 'merchant_id'),
                "is_fraudulent": len(fraud_reasons) > 0,
                "fraud_reasons": fraud_reasons,
                "field_matches": dict(field_matches)  # Show which fields matched with which merchant IDs
            }
            
            # If fraudulent, store in database
            if response["is_fraudulent"]:
                new_entry = table(
                    **merchant_application.model_dump(),
                    fraud_reason=", ".join(fraud_reasons)
                )
                session.add(new_entry)
                session.commit()
            
            return response
            
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 