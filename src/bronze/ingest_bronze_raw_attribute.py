"""
Bronze Layer Ingestion - RAW_ATTRIBUTE Table
Reads source CSV files and metadata to populate RAW_ATTRIBUTE table.
Links each attribute value to its SOURCE_PARTY and METADATA_COLUMN.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid


class BronzeRawAttributeIngestion:
    """Ingests source attributes into RAW_ATTRIBUTE table using metadata-driven logic"""
    
    def __init__(self, metadata_dir=None, source_data_dir=None, bronze_dir=None):
        # Default to project root paths
        project_root = Path(__file__).parent.parent.parent
        self.metadata_dir = Path(metadata_dir) if metadata_dir else project_root / 'data' / 'uat_generation' / 'metadata'
        self.source_data_dir = Path(source_data_dir) if source_data_dir else project_root / 'data' / 'uat_generation' / 'sources'
        self.bronze_dir = Path(bronze_dir) if bronze_dir else project_root / 'data' / 'bronze'
        
        self.metadata_system = None
        self.metadata_system_table = None
        self.metadata_party_type = None
        self.metadata_column = None
        self.source_party = None
        
        self.raw_attribute_records = []
        
    def load_metadata(self):
        """Load all required metadata tables"""
        print("Loading metadata...")
        
        self.metadata_system = pd.read_csv(self.metadata_dir / 'metadata_system.csv')
        self.metadata_system_table = pd.read_csv(self.metadata_dir / 'metadata_system_table.csv')
        self.metadata_party_type = pd.read_csv(self.metadata_dir / 'metadata_party_type.csv')
        self.metadata_column = pd.read_csv(self.metadata_dir / 'metadata_column.csv')
        
        print(f"  ✓ Loaded {len(self.metadata_system)} systems")
        print(f"  ✓ Loaded {len(self.metadata_system_table)} tables")
        print(f"  ✓ Loaded {len(self.metadata_party_type)} party types")
        print(f"  ✓ Loaded {len(self.metadata_column)} column mappings")
    
    def load_source_party(self):
        """Load SOURCE_PARTY table created by previous ingestion"""
        print("\nLoading SOURCE_PARTY...")
        source_party_file = self.bronze_dir / 'source_party.csv'
        
        if not source_party_file.exists():
            raise FileNotFoundError(
                f"SOURCE_PARTY not found at {source_party_file}. "
                "Please run ingest_bronze_source_party.py first."
            )
        
        self.source_party = pd.read_csv(source_party_file)
        print(f"  ✓ Loaded {len(self.source_party)} SOURCE_PARTY records")
    
    def get_system_table_info(self, system_table_id):
        """Get system name and table name from system_table_id"""
        table_row = self.metadata_system_table[
            self.metadata_system_table['system_table_id'] == system_table_id
        ]
        if table_row.empty:
            raise ValueError(f"system_table_id not found: {system_table_id}")
        
        system_id = table_row.iloc[0]['system_id']
        table_name = table_row.iloc[0]['table_name']
        
        system_row = self.metadata_system[self.metadata_system['system_id'] == system_id]
        system_name = system_row.iloc[0]['system_name']
        
        return system_name, table_name
    
    def get_party_type(self, party_type_id):
        """Get party_type string from party_type_id"""
        pt = self.metadata_party_type[self.metadata_party_type['party_type_id'] == party_type_id]
        if pt.empty:
            raise ValueError(f"party_type_id not found: {party_type_id}")
        return pt.iloc[0]['party_type']
    
    def get_column_id(self, system_name, table_name, column_name, party_type):
        """
        Get column_id (index in METADATA_COLUMN) for a specific attribute.
        
        Must match:
        - source_system
        - source_table
        - source_column
        - party_type (critical!)
        - is_attribute = True
        """
        matches = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['source_column'] == column_name) &
            (self.metadata_column['party_type'] == party_type) &
            (self.metadata_column['is_attribute'] == True)
        ]
        
        if matches.empty:
            # Not an error - this column might be a relationship column, not an attribute
            return None
        
        # Return the index as column_id
        return matches.index[0]
    
    def ingest_source_table(self, system_name, table_name, csv_filename):
        """
        Ingest attributes from a single source table into RAW_ATTRIBUTE.
        
        For each row:
        1. Find corresponding SOURCE_PARTY record (to get party_type)
        2. For each column that's an attribute:
           - Find matching METADATA_COLUMN (system/table/column/party_type)
           - Create RAW_ATTRIBUTE record
        """
        print(f"\nIngesting attributes from {system_name}.{table_name}...")
        
        # Load source data
        source_file = self.source_data_dir / csv_filename
        if not source_file.exists():
            print(f"  ⚠ File not found: {source_file}")
            return
        
        df = pd.read_csv(source_file)
        
        # Get system_table_id
        table_row = self.metadata_system_table[
            (self.metadata_system_table['table_name'] == table_name)
        ]
        system_row = self.metadata_system[self.metadata_system['system_name'] == system_name]
        system_id = system_row.iloc[0]['system_id']
        
        table_match = self.metadata_system_table[
            (self.metadata_system_table['system_id'] == system_id) &
            (self.metadata_system_table['table_name'] == table_name)
        ]
        system_table_id = table_match.iloc[0]['system_table_id']
        
        # Get primary key column
        pk_columns = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['is_relationship'] == True)
        ]['source_column'].tolist()
        
        if not pk_columns:
            raise ValueError(f"No primary key column found for {system_name}.{table_name}")
        
        pk_column = pk_columns[0]
        
        # Process each row
        ingestion_timestamp = datetime.now().isoformat()
        attributes_created = 0
        
        for idx, row in df.iterrows():
            source_record_id = str(row[pk_column])
            
            # Find ALL SOURCE_PARTY records for this row (may be multiple for column-subset pattern)
            source_party_matches = self.source_party[
                (self.source_party['system_table_id'] == system_table_id) &
                (self.source_party['source_record_id'] == source_record_id)
            ]
            
            if source_party_matches.empty:
                print(f"  ⚠ No SOURCE_PARTY found for {system_name}.{table_name}.{source_record_id}")
                continue
            
            # Process each SOURCE_PARTY (important for column-subset tables!)
            for _, source_party_row in source_party_matches.iterrows():
                source_party_id = source_party_row['source_party_id']
                party_type_id = source_party_row['party_type_id']
                party_type = self.get_party_type(party_type_id)
                
                # Extract attribute values for THIS party_type
                for column_name in df.columns:
                    # Get column_id for this attribute matching the party_type
                    column_id = self.get_column_id(system_name, table_name, column_name, party_type)
                    
                    if column_id is None:
                        # Not an attribute column for this party_type
                        continue
                    
                    # Get raw value
                    raw_value = row[column_name]
                    
                    # Skip NULL/NaN values
                    if pd.isna(raw_value):
                        continue
                    
                    # Create RAW_ATTRIBUTE record
                    raw_attribute_id = f"RA_{source_party_id}_{column_name}"
                    
                    raw_attribute_record = {
                        'raw_attribute_id': raw_attribute_id,
                        'source_party_id': source_party_id,
                        'column_id': column_id,
                        'raw_value': str(raw_value),
                        'ingestion_timestamp': ingestion_timestamp
                    }
                    
                    self.raw_attribute_records.append(raw_attribute_record)
                    attributes_created += 1
        
        print(f"  ✓ Created {attributes_created} RAW_ATTRIBUTE records from {len(df)} rows")
    
    def ingest_all_sources(self):
        """Ingest attributes from all source tables that contain party data"""
        
        source_tables = [
            ('SmartPlus', 'lead', 'smartplus_lead.csv'),
            ('SmartPlus', 'application', 'smartplus_application.csv'),
            ('SmartPlus', 'quote_member', 'smartplus_quote_member.csv'),
            ('SmartPlus', 'contact_person', 'smartplus_contact_person.csv'),
            ('Smile', 'policy_member', 'smile_policy_member.csv'),
        ]
        
        for system, table, filename in source_tables:
            self.ingest_source_table(system, table, filename)
    
    def export_raw_attribute(self):
        """Export RAW_ATTRIBUTE table to CSV"""
        df = pd.DataFrame(self.raw_attribute_records)
        output_file = self.bronze_dir / 'raw_attribute.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*70}")
        print(f"✓ Exported RAW_ATTRIBUTE: {len(df)} records")
        print(f"  File: {output_file}")
        
        # Print summary by source table
        print(f"\nBreakdown by source_party_id prefix:")
        
        # Count by table
        df['table_prefix'] = df['source_party_id'].str.split('_').str[2]
        counts = df['table_prefix'].value_counts()
        for table, count in counts.items():
            print(f"  {table:<20} {count:>5} attributes")
    
    def run(self):
        """Execute full RAW_ATTRIBUTE ingestion"""
        print("="*70)
        print("BRONZE LAYER INGESTION - RAW_ATTRIBUTE")
        print("="*70)
        
        self.load_metadata()
        self.load_source_party()
        self.ingest_all_sources()
        self.export_raw_attribute()
        
        print("\n✓ Bronze RAW_ATTRIBUTE ingestion complete")


if __name__ == '__main__':
    ingestion = BronzeRawAttributeIngestion()
    ingestion.run()
