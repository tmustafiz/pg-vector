import json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer
from sklearn.decomposition import PCA

class EmbeddingGenerator:
    def __init__(self, config):
        self.config = config
        self.embedding_dim = config.get("embedding_dim", 128)
        self.group_pipelines = {}
        self.group_weights = {}
        self.pca = None
        self._build_group_pipelines()

    def _build_group_pipelines(self):
        # Map field configs by name for quick lookup
        field_configs = {f["name"]: f for f in self.config["fields"]}
        for group in self.config["feature_groups"]:
            transformers = []
            for fname in group["fields"]:
                fconfig = field_configs[fname]
                ttype = fconfig.get("transformer")
                transformers.append(self._make_transformer(fname, ttype))
            group_transformer = ColumnTransformer(transformers, remainder='drop', sparse_threshold=0.3)
            pipeline = Pipeline([("transform", group_transformer)])
            self.group_pipelines[group["name"]] = pipeline
            self.group_weights[group["name"]] = group.get("weight", 1.0)

    def _make_transformer(self, fname, ttype):
        # Choose transformer by type (as specified in config)
        if ttype == "onehot":
            return (fname, OneHotEncoder(sparse=False, handle_unknown='ignore'), [fname])
        elif ttype == "hashing":
            return (fname, HashingVectorizer(analyzer='char', ngram_range=(2, 4), n_features=8), fname)
        elif ttype == "tfidf":
            return (fname, TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=16), fname)
        elif ttype == "scaler":
            return (fname, StandardScaler(), [fname])
        else:
            return (fname, TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=8), fname)

    def fit(self, data):
        df = pd.DataFrame(data)
        for group_name, pipeline in self.group_pipelines.items():
            pipeline.fit(df)
        all_embeds = np.array([self._raw_embedding(row) for row in data])
        if all_embeds.shape[1] > self.embedding_dim:
            self.pca = PCA(n_components=self.embedding_dim)
            self.pca.fit(all_embeds)

    def transform(self, row):
        raw_emb = self._raw_embedding(row)
        if self.pca:
            return self.pca.transform([raw_emb])[0]
        # Pad if too short, trim if too long
        if len(raw_emb) < self.embedding_dim:
            return np.pad(raw_emb, (0, self.embedding_dim - len(raw_emb)))
        elif len(raw_emb) > self.embedding_dim:
            return raw_emb[:self.embedding_dim]
        else:
            return raw_emb

    def _raw_embedding(self, row):
        df_row = pd.DataFrame([row])
        group_vecs = []
        for group_name, pipeline in self.group_pipelines.items():
            vec = pipeline.transform(df_row)
            if hasattr(vec, "toarray"):
                vec = vec.toarray()
            vec = np.asarray(vec).flatten()
            weighted_vec = vec * self.group_weights[group_name]
            group_vecs.append(weighted_vec)
        return np.concatenate(group_vecs).astype(np.float32)