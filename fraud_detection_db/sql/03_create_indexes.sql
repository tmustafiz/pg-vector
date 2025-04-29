-- Create indexes for merchant_applications
CREATE INDEX IF NOT EXISTS idx_merchant_applications_merchant_id 
ON merchant_applications(merchant_id);

-- Create indexes for merchant_embeddings
CREATE INDEX IF NOT EXISTS idx_merchant_embeddings_application_id 
ON merchant_embeddings(merchant_application_id);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_merchant_embeddings_embedding 
ON merchant_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100); 