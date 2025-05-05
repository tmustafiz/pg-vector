import os
from pathlib import Path
from typing import Optional
from .config_schema import ModelConfig

def get_project_root() -> Path:
    """Get the root directory of the project"""
    # Start from the current file and go up until we find the root marker (like pyproject.toml or .git)
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / '.git').exists():
            return parent
    raise FileNotFoundError("Could not find project root")

def find_config_file(config_path: Optional[str] = None) -> Path:
    """
    Find the configuration file using the following precedence:
    1. Explicit path provided via argument
    2. Environment variable FRAUD_DETECTION_CONFIG
    3. Environment-specific config in root config directory
    4. Default config in root config directory
    """
    if config_path:
        path = Path(config_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config file not found at specified path: {config_path}")

    # Check environment variable
    env_path = os.getenv('FRAUD_DETECTION_CONFIG')
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # Get the project root
    root_dir = get_project_root()
    
    # Check environment-specific config
    env = os.getenv('FRAUD_DETECTION_ENV', 'development')
    env_config = root_dir / 'config' / f'model_config.{env}.json'
    if env_config.exists():
        return env_config

    # Check default config
    default_config = root_dir / 'config' / 'model_config.json'
    if default_config.exists():
        return default_config

    raise FileNotFoundError(
        "Could not find model_config.json. Expected locations:\n"
        f"1. {env_config} (environment-specific)\n"
        f"2. {default_config} (default)"
    )

def load_config(config_path: Optional[str] = None) -> ModelConfig:
    """
    Load the model configuration from the specified path or using the default resolution strategy.
    
    The configuration is loaded in the following order:
    1. Explicit path if provided
    2. Path from FRAUD_DETECTION_CONFIG environment variable
    3. Environment-specific config (based on FRAUD_DETECTION_ENV)
    4. Default config from project root
    """
    config_file = find_config_file(config_path)
    with open(config_file, 'r') as f:
        return ModelConfig.model_validate_json(f.read()) 