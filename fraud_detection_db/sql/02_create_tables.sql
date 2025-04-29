-- Create merchant_applications table
CREATE TABLE IF NOT EXISTS merchant_applications (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(255) UNIQUE NOT NULL,
    owner_ssn VARCHAR(255) NOT NULL,
    business_fed_tax_id VARCHAR(255) NOT NULL,
    owner_drivers_license VARCHAR(255) NOT NULL,
    business_phone_number VARCHAR(255) NOT NULL,
    owner_phone_number VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    country VARCHAR(2) NOT NULL,
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create merchant_embeddings table
CREATE TABLE IF NOT EXISTS merchant_embeddings (
    id SERIAL PRIMARY KEY,
    merchant_application_id INTEGER NOT NULL REFERENCES merchant_applications(id),
    embedding vector(384) NOT NULL,
    fraud_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 