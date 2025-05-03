from typing import Dict, Any, List
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import hashlib
from .config_schema import ModelConfig

class EmbeddingGenerator:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.scaler = StandardScaler()
        self.pca = None  # Will be initialized during fit
        
    def _hash_value(self, value: str) -> float:
        """Convert a string value to a numeric hash"""
        if not value:
            return 0.0
        hash_value = int(hashlib.md5(str(value).encode()).hexdigest()[:8], 16)
        return float(hash_value) / (2**32)  # Normalize to [0, 1]
        
    def _preprocess_field(self, value: Any) -> float:
        """Preprocess a single field value"""
        if value is None:
            return 0.0
        return self._hash_value(str(value))
        
    def _prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for embedding generation"""
        features = []
        
        # Process each feature group
        for group in self.config.feature_groups:
            group_features = []
            for field_name in group.fields:
                value = data.get(field_name)
                processed_value = self._preprocess_field(value)
                group_features.append(processed_value)
            
            # Add group features
            features.extend(group_features)
        
        return np.array(features).reshape(1, -1)
    
    def fit(self, data: List[Dict[str, Any]]):
        """Fit the embedding generator on training data"""
        # Prepare features for all training samples
        features = np.vstack([self._prepare_features(d) for d in data])
        
        # Initialize PCA with appropriate dimensions
        n_components = min(features.shape[1], 32)  # Use smaller of feature count or 32
        self.pca = PCA(n_components=n_components)
        
        # Fit scaler and PCA
        scaled_features = self.scaler.fit_transform(features)
        self.pca.fit(scaled_features)
        
    def generate_embedding(self, data: Dict[str, Any]) -> np.ndarray:
        """Generate embedding for merchant application data"""
        if self.pca is None:
            raise ValueError("EmbeddingGenerator must be fit before generating embeddings")
            
        # Prepare features
        features = self._prepare_features(data)
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        # Apply PCA to get embedding
        embedding = self.pca.transform(scaled_features)[0]
        
        return embedding.astype(np.float32)  # Ensure float32 for pgvector 