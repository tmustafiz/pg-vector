from fastapi import FastAPI, HTTPException
from fraud_detection_common.database import Database
from fraud_detection_common.embeddings import EmbeddingGenerator
from fraud_detection_common.models import MerchantApplication, EvaluationResponse, FieldMatch, FraudCase

app = FastAPI(title="Fraud Detection API")

# Initialize components
db = Database()
embedding_generator = EmbeddingGenerator()

def _compare_fields(new_app: dict, fraud_app: dict) -> list[FieldMatch]:
    """Compare fields between applications"""
    matches = []
    
    # Compare email
    if new_app.get('email') and fraud_app.get('email'):
        if new_app['email'].lower() == fraud_app['email'].lower():
            matches.append(FieldMatch(
                field='email',
                new_value=new_app['email'],
                fraud_value=fraud_app['email'],
                similarity=1.0
            ))
    
    # Compare address
    if new_app.get('address_line1') and fraud_app.get('address_line1'):
        if new_app['address_line1'].lower() == fraud_app['address_line1'].lower():
            matches.append(FieldMatch(
                field='address',
                new_value=new_app['address_line1'],
                fraud_value=fraud_app['address_line1'],
                similarity=1.0
            ))
    
    return matches

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_application(application: MerchantApplication):
    """Evaluate a merchant application for potential fraud"""
    try:
        # Generate embedding
        embedding = embedding_generator.generate_embedding(application.dict())
        
        # Find similar cases
        similar_cases = db.find_similar_cases(embedding, threshold=0.3)
        
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
            matches = _compare_fields(application.dict(), fraud_app)
            
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
        if best_match.vector_similarity > 0.8:
            decision = "Decline"
        elif best_match.vector_similarity > 0.6:
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