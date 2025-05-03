import csv
import random
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

def generate_ssn() -> str:
    """Generate a realistic-looking SSN"""
    return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

def generate_tax_id() -> str:
    """Generate a realistic-looking business tax ID"""
    return f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"

def generate_phone() -> str:
    """Generate a realistic-looking phone number"""
    return f"{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

def generate_drivers_license() -> str:
    """Generate a realistic-looking driver's license number"""
    return f"DL{random.randint(10000000, 99999999)}"

def generate_email(name: str, domain: str) -> str:
    """Generate a realistic-looking email"""
    return f"{name.lower().replace(' ', '.')}@{domain}"

def generate_address() -> str:
    """Generate a realistic-looking address"""
    streets = ["Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Lincoln", "Jefferson"]
    return f"{random.randint(1, 9999)} {random.choice(streets)} St"

def generate_website(company_name: str) -> str:
    """Generate a realistic-looking website"""
    return f"www.{company_name.lower().replace(' ', '')}.com"

def generate_company_name() -> str:
    """Generate a realistic-looking company name"""
    prefixes = ["Global", "International", "National", "American", "United"]
    types = ["Tech", "Solutions", "Systems", "Services", "Enterprises"]
    suffixes = ["Inc", "LLC", "Corp", "Ltd"]
    return f"{random.choice(prefixes)} {random.choice(types)} {random.choice(suffixes)}"

def generate_test_data(num_records: int, fraud_ratio: float = 0.1) -> List[Dict[str, Any]]:
    """Generate test data with some fraudulent patterns"""
    data = []
    num_fraud = int(num_records * fraud_ratio)
    
    # Generate some common patterns that will be reused
    common_patterns = {
        'ssn': [generate_ssn() for _ in range(5)],
        'tax_id': [generate_tax_id() for _ in range(5)],
        'phone': [generate_phone() for _ in range(5)],
        'email_domain': ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'],
        'city_state': [
            ('New York', 'NY'),
            ('Los Angeles', 'CA'),
            ('Chicago', 'IL'),
            ('Houston', 'TX'),
            ('Phoenix', 'AZ')
        ]
    }
    
    for i in range(num_records):
        is_fraud = i < num_fraud
        company_name = generate_company_name()
        
        # For fraudulent cases, reuse some patterns
        if is_fraud:
            ssn = random.choice(common_patterns['ssn'])
            tax_id = random.choice(common_patterns['tax_id'])
            phone = random.choice(common_patterns['phone'])
            email_domain = random.choice(common_patterns['email_domain'])
            city, state = random.choice(common_patterns['city_state'])
            fraud_reason = random.choice([
                "Duplicate SSN",
                "Suspicious tax ID pattern",
                "Multiple applications from same phone",
                "Known fraudulent email domain",
                "Suspicious address pattern"
            ])
        else:
            ssn = generate_ssn()
            tax_id = generate_tax_id()
            phone = generate_phone()
            email_domain = random.choice(common_patterns['email_domain'])
            city, state = random.choice(common_patterns['city_state'])
            fraud_reason = None
        
        record = {
            'owner_ssn': ssn,
            'business_fed_tax_id': tax_id,
            'owner_drivers_license': generate_drivers_license(),
            'business_phone_number': phone,
            'owner_phone_number': generate_phone(),
            'email': generate_email(company_name, email_domain),
            'address_line1': generate_address(),
            'city': city,
            'state': state,
            'zip_code': f"{random.randint(10000, 99999)}",
            'country': 'US',
            'website': generate_website(company_name),
            'fraud_reason': fraud_reason
        }
        data.append(record)
    
    return data

def save_to_csv(data: List[Dict[str, Any]], output_path: str):
    """Save the generated data to a CSV file"""
    if not data:
        return
    
    # Get field names from the first record
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    # Create output directory if it doesn't exist
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Generate and save test data
    test_data = generate_test_data(1000, fraud_ratio=0.1)
    output_path = output_dir / "training_data.csv"
    save_to_csv(test_data, output_path)
    
    print(f"Generated {len(test_data)} records with {sum(1 for r in test_data if r['fraud_reason'])} fraudulent cases")
    print(f"Data saved to {output_path}")

if __name__ == "__main__":
    main() 