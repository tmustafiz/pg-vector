from typing import Dict, Any
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
import hashlib

class EmbeddingGenerator:
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=embedding_dim)
        self.label_encoders = {}
        
    def _hash_value(self, value: str) -> int:
        """Convert a string value to a numeric hash"""
        if not value:
            return 0
        return int(hashlib.md5(str(value).encode()).hexdigest()[:8], 16) % 10000
        
    def _prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for embedding generation"""
        # Define feature categories
        identity_features = [
            self._hash_value(data.get('owner_ssn', '')),
            self._hash_value(data.get('business_fed_tax_id', '')),
            self._hash_value(data.get('owner_drivers_license', ''))
        ]
        
        contact_features = [
            self._hash_value(data.get('business_phone_number', '')),
            self._hash_value(data.get('owner_phone_number', '')),
            self._hash_value(data.get('email', ''))
        ]
        
        location_features = [
            self._hash_value(data.get('address_line1', '')),
            self._hash_value(data.get('city', '')),
            self._hash_value(data.get('state', '')),
            self._hash_value(data.get('zip_code', '')),
            self._hash_value(data.get('country', ''))
        ]
        
        business_features = [
            self._hash_value(data.get('website', ''))
        ]
        
        # Combine all features
        features = np.array(
            identity_features + 
            contact_features + 
            location_features + 
            business_features
        )
        
        return features.reshape(1, -1)
    
    def fit(self, data: list[Dict[str, Any]]):
        """Fit the embedding generator on training data"""
        # Prepare features for all training samples
        features = np.vstack([self._prepare_features(d) for d in data])
        
        # Fit scaler and PCA
        scaled_features = self.scaler.fit_transform(features)
        self.pca.fit(scaled_features)
        
    def generate_embedding(self, data: Dict[str, Any]) -> np.ndarray:
        """Generate embedding for merchant application data"""
        # Prepare features
        features = self._prepare_features(data)
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        # Apply PCA to get embedding
        embedding = self.pca.transform(scaled_features)[0]
        
        return embedding.astype(np.float32)  # Ensure float32 for pgvector 