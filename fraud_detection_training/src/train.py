import json
import uuid
from pathlib import Path
from tqdm import tqdm
from fraud_detection_common.database import Database
from fraud_detection_common.embeddings import EmbeddingGenerator
from fraud_detection_common.models import MerchantApplication

def load_training_data(file_path: str) -> list:
    """Load training data from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def process_training_data(data: list, db: Database, embedding_generator: EmbeddingGenerator):
    """Process training data and store embeddings"""
    # First, fit the embedding generator on all training data
    print("Fitting embedding generator...")
    embedding_generator.fit([item['application'] for item in data])
    
    # Then process and store each item
    for item in tqdm(data, desc="Processing training data"):
        try:
            # Validate data against our model
            application = MerchantApplication(**item['application'])
            
            # Generate embedding
            embedding = embedding_generator.generate_embedding(application.dict())
            
            # Store in database
            merchant_id = str(uuid.uuid4())
            db.store_embedding(
                merchant_id=merchant_id,
                embedding=embedding,
                application=application.dict(),
                fraud_reason=item.get('fraud_reason')
            )
            
        except Exception as e:
            print(f"Error processing item: {e}")
            continue

def main():
    # Initialize components
    db = Database()
    db.create_tables()
    embedding_generator = EmbeddingGenerator()
    
    # Load and process training data
    data_path = Path("data/training_data.json")
    if not data_path.exists():
        print(f"Training data not found at {data_path}")
        return
    
    training_data = load_training_data(data_path)
    process_training_data(training_data, db, embedding_generator)
    
    # Close database connection
    db.close()

if __name__ == "__main__":
    main() 