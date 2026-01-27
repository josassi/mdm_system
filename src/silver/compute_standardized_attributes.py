"""
STANDARDIZED_ATTRIBUTE Computation - Silver Layer

Transforms RAW_ATTRIBUTE into STANDARDIZED_ATTRIBUTE with:
1. Normalization: Clean and format values for matching
2. Classification: Detect attribute subtypes (e.g., HKID vs Passport)

Classification Logic Examples:
- Government ID: Detect HKID vs Passport vs Driver's License from format
- Phone: Detect mobile vs landline
- Email: Validate format and extract domain
- Address: Parse country/city (future)

Algorithm:
1. Load RAW_ATTRIBUTE and metadata
2. For each raw attribute:
   a. Determine attribute_type from METADATA_COLUMN
   b. Apply normalization rules based on type
   c. If requires_classification, detect attribute_subtype
   d. Create STANDARDIZED_ATTRIBUTE record
3. Write to STANDARDIZED_ATTRIBUTE table
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import uuid


def load_data():
    """Load Bronze data and metadata"""
    project_root = Path(__file__).parent.parent.parent
    bronze_dir = project_root / 'data/bronze'
    metadata_dir = project_root / 'data/uat_generation/metadata'
    
    print("Loading Bronze data and metadata...")
    
    raw_attribute = pd.read_csv(bronze_dir / 'raw_attribute.csv')
    metadata_column = pd.read_csv(metadata_dir / 'metadata_column.csv')
    metadata_attr_type = pd.read_csv(metadata_dir / 'metadata_attribute_type.csv')
    metadata_attr_subtype = pd.read_csv(metadata_dir / 'metadata_attribute_subtype.csv')
    
    print(f"  ✓ Loaded {len(raw_attribute)} RAW_ATTRIBUTE records")
    print(f"  ✓ Loaded {len(metadata_column)} METADATA_COLUMN records")
    print(f"  ✓ Loaded {len(metadata_attr_type)} METADATA_ATTRIBUTE_TYPE records")
    print(f"  ✓ Loaded {len(metadata_attr_subtype)} METADATA_ATTRIBUTE_SUBTYPE records")
    
    return raw_attribute, metadata_column, metadata_attr_type, metadata_attr_subtype


# =====================================================================
# NORMALIZATION FUNCTIONS
# =====================================================================

def normalize_name(value):
    """Normalize person names for matching"""
    if pd.isna(value) or value == '':
        return None
    
    # Trim whitespace, convert to uppercase, remove extra spaces
    normalized = ' '.join(str(value).strip().upper().split())
    
    # Remove common punctuation
    normalized = normalized.replace('.', '').replace(',', '')
    
    return normalized


def normalize_date(value):
    """Normalize dates to ISO format YYYY-MM-DD"""
    if pd.isna(value) or value == '':
        return None
    
    # Already in ISO format (from UAT data)
    return str(value).strip()


def normalize_email(value):
    """Normalize email addresses"""
    if pd.isna(value) or value == '':
        return None
    
    # Lowercase and trim
    normalized = str(value).strip().lower()
    
    # Basic validation
    if '@' not in normalized or '.' not in normalized.split('@')[1]:
        return None
    
    return normalized


def normalize_phone(value):
    """Normalize phone numbers"""
    if pd.isna(value) or value == '':
        return None
    
    # Remove all non-digit characters except + at start
    normalized = str(value).strip()
    
    # Keep + prefix if exists, remove all other non-digits
    if normalized.startswith('+'):
        normalized = '+' + re.sub(r'\D', '', normalized[1:])
    else:
        normalized = re.sub(r'\D', '', normalized)
    
    return normalized if normalized else None


def normalize_gov_id(value):
    """Normalize government IDs"""
    if pd.isna(value) or value == '':
        return None
    
    # Uppercase and remove extra spaces
    normalized = str(value).strip().upper()
    
    # Standardize HKID format: X######(#) - ensure parentheses
    if re.match(r'^[A-Z]\d{6}\(\d\)$', normalized):
        return normalized  # Already in correct format
    elif re.match(r'^[A-Z]\d{6}\d$', normalized):
        # Missing parentheses: A1234567 -> A123456(7)
        return f"{normalized[:7]}({normalized[7]})"
    
    return normalized


def normalize_address(value):
    """Normalize addresses (basic)"""
    if pd.isna(value) or value == '':
        return None
    
    # Uppercase and normalize spaces
    normalized = ' '.join(str(value).strip().upper().split())
    
    return normalized


def normalize_gender(value):
    """Normalize gender values"""
    if pd.isna(value) or value == '':
        return None
    
    normalized = str(value).strip().upper()
    
    # Standardize to M/F/O
    if normalized in ['M', 'MALE', 'MAN']:
        return 'M'
    elif normalized in ['F', 'FEMALE', 'WOMAN']:
        return 'F'
    elif normalized in ['O', 'OTHER', 'NON-BINARY']:
        return 'O'
    
    return normalized


def normalize_default(value):
    """Default normalization: trim and uppercase"""
    if pd.isna(value) or value == '':
        return None
    
    return str(value).strip().upper()


# =====================================================================
# CLASSIFICATION FUNCTIONS
# =====================================================================

def classify_government_id(standardized_value):
    """
    Detect government ID subtype from format
    
    Returns: (attribute_subtype_name, confidence)
    """
    if not standardized_value:
        return None, 0.0
    
    # HKID Pattern: X######(#) - Letter + 6 digits + (check digit)
    if re.match(r'^[A-Z]\d{6}\(\d\)$', standardized_value):
        return 'HKID', 1.0
    
    # Passport patterns (various countries)
    # Format: 1-2 letters + 6-8 digits (e.g., K1234567, PA12345678)
    if re.match(r'^[A-Z]{1,2}\d{6,8}$', standardized_value):
        return 'PASSPORT', 0.9
    
    # Driver's License (HK format): starts with letter, mix of letters/digits
    if re.match(r'^[A-Z]\d{7,10}$', standardized_value):
        return 'DRIVERS_LICENSE', 0.7
    
    # Default: Unknown
    return 'GOV_ID_UNKNOWN', 0.5


def classify_phone_number(standardized_value):
    """
    Detect phone subtype (mobile vs landline)
    
    Returns: (attribute_subtype_name, confidence)
    """
    if not standardized_value:
        return None, 0.0
    
    # Hong Kong mobile: +852-9XXX-XXXX or +852-6XXX-XXXX
    if re.match(r'^\+852[96]\d{7}$', standardized_value):
        return 'MOBILE', 0.95
    
    # Hong Kong landline: +852-2XXX-XXXX or +852-3XXX-XXXX
    if re.match(r'^\+852[23]\d{7}$', standardized_value):
        return 'LANDLINE', 0.95
    
    # International mobile (generic): +<country_code><digits>
    if re.match(r'^\+\d{10,15}$', standardized_value):
        return 'MOBILE', 0.7
    
    # Default: Phone (generic)
    return 'PHONE_GENERIC', 0.5


def classify_email(standardized_value):
    """
    Classify email (could detect personal vs business)
    
    Returns: (attribute_subtype_name, confidence)
    """
    if not standardized_value or '@' not in standardized_value:
        return None, 0.0
    
    domain = standardized_value.split('@')[1]
    
    # Common personal email domains
    personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
    if domain in personal_domains:
        return 'EMAIL_PERSONAL', 0.9
    
    # Default: Email (generic)
    return 'EMAIL_GENERIC', 0.8


# =====================================================================
# MAIN NORMALIZATION & CLASSIFICATION
# =====================================================================

def get_normalization_function(attribute_name):
    """Map attribute type to normalization function"""
    normalization_map = {
        'First Name': normalize_name,
        'Last Name': normalize_name,
        'Date of Birth': normalize_date,
        'Email Address': normalize_email,
        'Phone Number': normalize_phone,
        'Government ID': normalize_gov_id,
        'Address': normalize_address,
        'Gender': normalize_gender,
    }
    
    return normalization_map.get(attribute_name, normalize_default)


def get_classification_function(attribute_name):
    """Map attribute type to classification function"""
    classification_map = {
        'Government ID': classify_government_id,
        'Phone Number': classify_phone_number,
        'Email Address': classify_email,
    }
    
    return classification_map.get(attribute_name)


def create_standardized_attributes(raw_attr_df, metadata_col_df, metadata_type_df, metadata_subtype_df):
    """
    Transform RAW_ATTRIBUTE to STANDARDIZED_ATTRIBUTE
    """
    print("\n" + "="*70)
    print("CREATING STANDARDIZED ATTRIBUTES")
    print("="*70)
    
    # Join raw_attribute with metadata to get attribute_type info
    # Note: Bronze layer uses pandas index as column_id (integer)
    # We need to map integer column_id to metadata_column row
    metadata_col_indexed = metadata_col_df.reset_index()
    metadata_col_indexed['column_idx'] = metadata_col_indexed.index
    
    raw_with_metadata = raw_attr_df.merge(
        metadata_col_indexed[['column_idx', 'attribute_type']],
        left_on='column_id',
        right_on='column_idx',
        how='left'
    )
    
    raw_with_metadata = raw_with_metadata.merge(
        metadata_type_df[['attribute_type_id', 'attribute_name', 'requires_classification']],
        left_on='attribute_type',
        right_on='attribute_type_id',
        how='left'
    )
    
    standardized_records = []
    classification_stats = {}
    now = datetime.now()
    
    for idx, row in raw_with_metadata.iterrows():
        attribute_name = row['attribute_name']
        raw_value = row['raw_value']
        
        # Skip if no attribute_type mapping (shouldn't happen in clean data)
        if pd.isna(attribute_name):
            continue
        
        # Step 1: Normalize
        normalize_func = get_normalization_function(attribute_name)
        standardized_value = normalize_func(raw_value)
        
        if standardized_value is None:
            continue  # Skip null/invalid values
        
        # Step 2: Classify (if needed)
        requires_classification = row.get('requires_classification', False)
        
        if requires_classification:
            classify_func = get_classification_function(attribute_name)
            if classify_func:
                subtype_name, confidence = classify_func(standardized_value)
                
                # Track classification stats
                key = f"{attribute_name}::{subtype_name}"
                classification_stats[key] = classification_stats.get(key, 0) + 1
            else:
                # No classifier - use generic subtype
                subtype_name = f"{attribute_name.upper().replace(' ', '_')}_GENERIC"
                confidence = 0.5
        else:
            # No classification needed - use attribute_type as subtype
            subtype_name = attribute_name.upper().replace(' ', '_')
            confidence = 1.0
        
        # Get attribute_subtype_id from metadata
        subtype_row = metadata_subtype_df[
            metadata_subtype_df['subtype_name'] == subtype_name
        ]
        
        if len(subtype_row) == 0:
            # Subtype not in metadata - skip (or create dynamically in real system)
            continue
        
        attribute_subtype_id = subtype_row.iloc[0]['attribute_subtype_id']
        
        # Create STANDARDIZED_ATTRIBUTE record
        standardized_records.append({
            'standardized_attribute_id': str(uuid.uuid4()),
            'raw_attribute_id': row['raw_attribute_id'],
            'source_party_id': row['source_party_id'],
            'attribute_subtype_id': attribute_subtype_id,
            'standardized_value': standardized_value,
            'confidence_score': confidence,
            'pipeline_version': 'v1.0',
            'created_at': now,
            'is_current': True
        })
    
    print(f"\n✓ Created {len(standardized_records)} STANDARDIZED_ATTRIBUTE records")
    
    # Print classification statistics
    if classification_stats:
        print(f"\nClassification Statistics:")
        for key, count in sorted(classification_stats.items(), key=lambda x: -x[1]):
            print(f"  {key}: {count} records")
    
    return pd.DataFrame(standardized_records)


def export_standardized_attributes(std_attr_df, output_dir='data/silver'):
    """Export STANDARDIZED_ATTRIBUTE to CSV"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / output_dir
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = silver_dir / 'standardized_attribute.csv'
    std_attr_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Exported to {output_file}")


def verify_standardization(raw_attr_df, std_attr_df):
    """Verify standardization completeness"""
    print("\n" + "="*70)
    print("STANDARDIZATION VERIFICATION")
    print("="*70)
    
    # Count non-null raw values
    non_null_raw = raw_attr_df['raw_value'].notna().sum()
    
    print(f"✓ Input: {len(raw_attr_df)} RAW_ATTRIBUTE records")
    print(f"  - Non-null values: {non_null_raw}")
    print(f"✓ Output: {len(std_attr_df)} STANDARDIZED_ATTRIBUTE records")
    
    # Coverage percentage (accounting for nulls and invalid values)
    coverage = (len(std_attr_df) / non_null_raw * 100) if non_null_raw > 0 else 0
    print(f"✓ Coverage: {coverage:.1f}% of non-null raw values standardized")
    
    # Check for parties with attributes
    parties_with_std_attr = std_attr_df['source_party_id'].nunique()
    print(f"✓ Parties with standardized attributes: {parties_with_std_attr}")
    
    # Sample output
    print(f"\nSample standardized attributes:")
    sample = std_attr_df.head(5)[['source_party_id', 'attribute_subtype_id', 'standardized_value', 'confidence_score']]
    for _, row in sample.iterrows():
        print(f"  {row['source_party_id'][:30]:30} | {row['attribute_subtype_id']:30} | {row['standardized_value'][:40]:40} | {row['confidence_score']:.2f}")


def main():
    """Main standardization pipeline"""
    print("="*70)
    print("STANDARDIZED ATTRIBUTE COMPUTATION")
    print("="*70)
    
    # Step 1: Load data
    raw_attr_df, metadata_col_df, metadata_type_df, metadata_subtype_df = load_data()
    
    # Step 2: Create standardized attributes
    std_attr_df = create_standardized_attributes(
        raw_attr_df,
        metadata_col_df,
        metadata_type_df,
        metadata_subtype_df
    )
    
    # Step 3: Verify
    verify_standardization(raw_attr_df, std_attr_df)
    
    # Step 4: Export
    export_standardized_attributes(std_attr_df)
    
    print("\n" + "="*70)
    print("✅ STANDARDIZATION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
