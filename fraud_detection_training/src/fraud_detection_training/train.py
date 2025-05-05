import json
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict
from fraud_detection_common.database import Database
from fraud_detection_common.embeddings import EmbeddingGenerator
from fraud_detection_common.config import load_config
from fraud_detection_common.dynamic_model import DynamicModelGenerator
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_training_data(data_path: Path):
    """Load training data from file"""
    if data_path.suffix == '.json':
        return pd.read_json(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def process_training_data(data: pd.DataFrame, model_generator: DynamicModelGenerator):
    """Process training data and store in database"""
    session = model_generator.get_session()
    try:
        # Create tables if they don't exist
        model_generator.create_tables()
        
        # Process each row
        for _, row in data.iterrows():
            # Convert row to dict
            application_data = row.to_dict()
            
            # Get merchant_id
            merchant_id = application_data.pop('merchant_id', None)
            if not merchant_id:
                print(f"Skipping row without merchant_id: {application_data}")
                continue
            
            # Get fraud_reason if present
            fraud_reason = application_data.pop('fraud_reason', None)
            
            try:
                # Get the table configuration
                table_config = next(iter(model_generator.db_config.tables.values()))
                
                # Create a mapping of field names to their types
                valid_fields = {field['name']: field['type'] for field in table_config.fields}
                
                # Filter out fields that are not in the table configuration
                filtered_data = {k: v for k, v in application_data.items() if k in valid_fields}
                
                # Create table entry
                table = model_generator.get_sqlalchemy_model()
                entry = table(
                    merchant_id=merchant_id,
                    fraud_reason=fraud_reason,
                    **filtered_data
                )
                session.add(entry)
                session.commit()
            except Exception as e:
                print(f"Error processing row for merchant {merchant_id}: {e}")
                session.rollback()
                continue
    finally:
        session.close()

def main():
    # Get config path relative to the project root
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Try to use local config first, fall back to Docker config
    config_path = project_root / "config" / "database_config.local.json"
    if not config_path.exists():
        config_path = project_root / "config" / "database_config.json"
    
    # Initialize model generator
    model_generator = DynamicModelGenerator(config_path)
    
    try:
        # Load training data
        data_path = project_root / "fraud_detection_training" / "data" / "training_data.csv"
        data = load_training_data(data_path)
        
        # Process training data
        process_training_data(data, model_generator)
        
    finally:
        model_generator.close()

if __name__ == "__main__":
    main() 