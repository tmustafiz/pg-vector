from typing import Dict, Any, List
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import hashlib
from .config_schema import ModelConfig

class EmbeddingGenerator:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = None
        self.target_dim = 384  # Target dimension for pgvector
        self.pca = None  # Initialize PCA later when we know the number of features

    def _hash_value(self, value: Any) -> int:
        """Hash a value to an integer."""
        if value is None:
            return 0
        return int(hashlib.md5(str(value).encode()).hexdigest(), 16) % 1000

    def _preprocess_field(self, value: Any) -> float:
        """Preprocess a field value."""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, bool):
            return 1.0 if value else 0.0
        elif isinstance(value, str):
            return self._hash_value(value)
        return 0.0

    def _prepare_features(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """Prepare features from the data."""
        if not data:
            return np.array([])

        # Get all unique field names
        field_names = set()
        for item in data:
            field_names.update(item.keys())
        self.feature_names = sorted(field_names)

        # Create feature matrix
        features = []
        for item in data:
            row = [self._preprocess_field(item.get(field, None)) for field in self.feature_names]
            features.append(row)

        return np.array(features)

    def fit(self, data: List[Dict[str, Any]]) -> None:
        """Fit the embedding generator on the data."""
        features = self._prepare_features(data)
        if len(features) > 0:
            # Scale the features
            features = self.scaler.fit_transform(features)
            
            # Initialize PCA with appropriate number of components
            n_features = features.shape[1]
            n_components = min(n_features, 100)  # Use at most 100 components
            self.pca = PCA(n_components=n_components)
            self.pca.fit(features)

    def generate_embedding(self, data: Dict[str, Any]) -> np.ndarray:
        """Generate an embedding for a single data point."""
        if self.feature_names is None:
            raise ValueError("EmbeddingGenerator must be fitted before generating embeddings")

        # Prepare features
        features = np.array([self._preprocess_field(data.get(field, None)) for field in self.feature_names])
        if len(features) > 0:
            # Scale the features
            features = self.scaler.transform(features.reshape(1, -1))[0]
            
            if self.pca is not None:
                # Apply PCA
                features = self.pca.transform(features.reshape(1, -1))[0]

        # Pad to target dimension
        if len(features) < self.target_dim:
            # Pad with zeros
            padding = np.zeros(self.target_dim - len(features))
            embedding = np.concatenate([features, padding])
        else:
            # Truncate to target dimension
            embedding = features[:self.target_dim]

        return embedding.astype(np.float32) 