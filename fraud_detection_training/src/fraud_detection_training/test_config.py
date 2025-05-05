from fraud_detection_common.database_config import load_database_config
from pathlib import Path

def main():
    try:
        # Use the config file from the root config directory
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "database_config.json"
        config = load_database_config(config_path)
        print("Configuration loaded successfully:")
        print(f"Connection URL: {config.connection.url}")
        print(f"Schema: {config.connection.schema}")
        print(f"Tables: {list(config.tables.keys())}")
        for table_name, table_config in config.tables.items():
            print(f"\nTable: {table_name}")
            print(f"Schema: {table_config.schema}")
            print("Indexes:")
            for index in table_config.indexes:
                print(f"  - {index.name} ({index.type}) on {index.column}")
    except Exception as e:
        print(f"Error loading configuration: {e}")

if __name__ == "__main__":
    main() 