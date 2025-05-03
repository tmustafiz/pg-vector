from fastapi import FastAPI, HTTPException
from fraud_detection_common.database import Database
from fraud_detection_common.embeddings import EmbeddingGenerator
from fraud_detection_common.config_schema import ModelConfig
from typing import List, Optional
from pydantic import BaseModel

# Load configuration
with open("config/model_config.json") as f:
    config = ModelConfig.parse_raw(f.read())

# Initialize components
db = Database(config)
embedding_generator = EmbeddingGenerator(config)

# Create response models dynamically
class FieldMatch(BaseModel):
    field: str
    new_value: str
    fraud_value: str
    similarity: float

class FraudCase(BaseModel):
    merchant_id: str
    vector_similarity: float
    fraud_reason: Optional[str]
    matching_fields: List[FieldMatch]

class EvaluationResponse(BaseModel):
    decision: str
    vector_similarity: float
    field_matches: List[FraudCase]

app = FastAPI(title="Fraud Detection API")

def _compare_fields(new_app: dict, fraud_app: dict) -> List[FieldMatch]:
    """Compare fields between applications"""
    matches = []
    
    for field in config.fields:
        if field.name in new_app and field.name in fraud_app:
            if str(new_app[field.name]).lower() == str(fraud_app[field.name]).lower():
                matches.append(FieldMatch(
                    field=field.name,
                    new_value=str(new_app[field.name]),
                    fraud_value=str(fraud_app[field.name]),
                    similarity=1.0
                ))
    
    return matches

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_application(application: dict):
    """Evaluate a merchant application for potential fraud"""
    try:
        # Generate embedding
        embedding = embedding_generator.generate_embedding(application)
        
        # Find similar cases
        similar_cases = db.find_similar_cases(
            embedding,
            threshold=config.similarity_thresholds["review"]
        )
        
        if not similar_cases:
            return EvaluationResponse(
                decision="Approve",
                vector_similarity=0.0,
                field_matches=[]
            )
        
        # Process matches
        field_matches = []
        for case in similar_cases:
            merchant_id, similarity, fraud_app, fraud_reason = case
            matches = _compare_fields(application, fraud_app)
            
            if matches:
                field_matches.append(FraudCase(
                    merchant_id=merchant_id,
                    vector_similarity=similarity,
                    fraud_reason=fraud_reason,
                    matching_fields=matches
                ))
        
        if not field_matches:
            return EvaluationResponse(
                decision="Approve",
                vector_similarity=0.0,
                field_matches=[]
            )
        
        # Make decision based on best match
        best_match = field_matches[0]
        if best_match.vector_similarity > config.similarity_thresholds["decline"]:
            decision = "Decline"
        elif best_match.vector_similarity > config.similarity_thresholds["review"]:
            decision = "Review"
        else:
            decision = "Approve"
        
        return EvaluationResponse(
            decision=decision,
            vector_similarity=best_match.vector_similarity,
            field_matches=field_matches
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    db.close() 