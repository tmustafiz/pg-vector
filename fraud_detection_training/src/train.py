import json
import csv
import uuid
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from fraud_detection_common.database import Database
from fraud_detection_common.embeddings import EmbeddingGenerator
from fraud_detection_common.config_schema import ModelConfig

def load_config(config_path: str) -> ModelConfig:
    """Load model configuration from JSON file"""
    with open(config_path, 'r') as f:
        return ModelConfig.parse_raw(f.read())

def load_training_data(file_path: str) -> List[Dict[str, Any]]:
    """Load training data from JSON or CSV file"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Training data file not found: {file_path}")
    
    if path.suffix.lower() == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            # If the data is a list of applications without fraud_reason
            if isinstance(data, list) and all(isinstance(item, dict) and 'application' not in item for item in data):
                return [{'application': item, 'fraud_reason': None} for item in data]
            return data
            
    elif path.suffix.lower() == '.csv':
        data = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert empty strings to None
                row = {k: (v if v != '' else None) for k, v in row.items()}
                # If fraud_reason column exists, use it, otherwise set to None
                fraud_reason = row.pop('fraud_reason', None)
                data.append({
                    'application': row,
                    'fraud_reason': fraud_reason
                })
        return data
    
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Supported formats: .json, .csv")

def process_training_data(data: list, db: Database, embedding_generator: EmbeddingGenerator):
    """Process training data and store embeddings"""
    # First, fit the embedding generator on all training data
    print("Fitting embedding generator...")
    embedding_generator.fit([item['application'] for item in data])
    
    # Then process and store each item
    for item in tqdm(data, desc="Processing training data"):
        try:
            # Generate embedding
            embedding = embedding_generator.generate_embedding(item['application'])
            
            # Store in database
            merchant_id = str(uuid.uuid4())
            db.store_application(
                merchant_id=merchant_id,
                application_data=item['application']
            )
            db.store_embedding(
                application_id=merchant_id,
                embedding=embedding,
                fraud_reason=item.get('fraud_reason')
            )
            
        except Exception as e:
            print(f"Error processing item: {e}")
            continue

def main():
    # Load configuration
    config = load_config("config/model_config.json")
    
    # Initialize components
    db = Database(config)
    embedding_generator = EmbeddingGenerator(config)
    
    # Load and process training data
    data_path = Path("data/training_data.csv")
    if not data_path.exists():
        print(f"Training data not found at {data_path}")
        return
    
    training_data = load_training_data(data_path)
    process_training_data(training_data, db, embedding_generator)
    
    # Close database connection
    db.close()

if __name__ == "__main__":
    main() 