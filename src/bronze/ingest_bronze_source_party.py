"""
Bronze Layer Ingestion - SOURCE_PARTY Table
Reads source CSV files and metadata to populate SOURCE_PARTY table.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
import sys


class BronzeSourcePartyIngestion:
    """Ingests source data into SOURCE_PARTY table using metadata-driven logic"""
    
    def __init__(self, metadata_dir=None, source_data_dir=None, output_dir=None, incremental=False):
        # Default to project root paths
        project_root = Path(__file__).parent.parent.parent
        self.metadata_dir = Path(metadata_dir) if metadata_dir else project_root / 'data' / 'uat_generation' / 'metadata'
        self.source_data_dir = Path(source_data_dir) if source_data_dir else project_root / 'data' / 'uat_generation' / 'sources'
        self.output_dir = Path(output_dir) if output_dir else project_root / 'data' / 'bronze'
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.metadata_system = None
        self.metadata_system_table = None
        self.metadata_party_type = None
        self.metadata_column = None
        self.existing_source_party = None  # For SCD2 incremental
        
        self.incremental = incremental
        self.source_party_records = []
        self.ingestion_timestamp = datetime.now()
        
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
    
    def load_existing_source_party(self):
        """Load existing SOURCE_PARTY for SCD2 incremental processing"""
        source_party_file = self.output_dir / 'source_party.csv'
        
        if source_party_file.exists():
            self.existing_source_party = pd.read_csv(source_party_file)
            # Convert date columns
            if 'rec_start_date' in self.existing_source_party.columns:
                self.existing_source_party['rec_start_date'] = pd.to_datetime(self.existing_source_party['rec_start_date'], format='ISO8601')
            if 'rec_end_date' in self.existing_source_party.columns:
                self.existing_source_party['rec_end_date'] = pd.to_datetime(self.existing_source_party['rec_end_date'], format='ISO8601')
            
            print(f"\nLoading existing SOURCE_PARTY for incremental processing...")
            print(f"  ✓ Loaded {len(self.existing_source_party)} existing SOURCE_PARTY records")
        else:
            print(f"\nNo existing SOURCE_PARTY found - will create initial version")
            self.existing_source_party = pd.DataFrame()
    
    def get_system_table_id(self, system_name, table_name):
        """Get system_table_id for a given system and table"""
        system = self.metadata_system[self.metadata_system['system_name'] == system_name]
        if system.empty:
            raise ValueError(f"System not found: {system_name}")
        
        system_id = system.iloc[0]['system_id']
        
        table = self.metadata_system_table[
            (self.metadata_system_table['system_id'] == system_id) &
            (self.metadata_system_table['table_name'] == table_name)
        ]
        if table.empty:
            raise ValueError(f"Table not found: {system_name}.{table_name}")
        
        return table.iloc[0]['system_table_id']
    
    def get_party_type_id(self, party_type):
        """Get party_type_id for a given party_type string"""
        pt = self.metadata_party_type[self.metadata_party_type['party_type'] == party_type]
        if pt.empty:
            raise ValueError(f"Party type not found: {party_type}")
        return pt.iloc[0]['party_type_id']
    
    def get_table_party_types(self, system_name, table_name):
        """
        Get all party_types defined for a table.
        
        Returns:
            list of party_type strings, or empty list if no attributes defined
        """
        party_types = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['is_attribute'] == True)
        ]['party_type'].unique().tolist()
        
        # Filter out None values
        return [pt for pt in party_types if pd.notna(pt)]
    
    def is_column_subset_table(self, system_name, table_name):
        """
        Determine if table uses column-subset pattern (multiple parties in one row).
        
        Pattern detection:
        - Column-subset: Multiple distinct party_types have attributes in this table
        - Conditional: One party_type per row, determined by discriminator column
        """
        party_types = self.get_table_party_types(system_name, table_name)
        
        # If multiple party_types exist, check if there's a discriminator
        if len(party_types) > 1:
            # Check if there's a party_type_condition column
            has_discriminator = len(self.metadata_column[
                (self.metadata_column['source_system'] == system_name) &
                (self.metadata_column['source_table'] == table_name) &
                (self.metadata_column['is_party_type_condition'] == True)
            ]) > 0
            
            # Column-subset pattern: multiple party_types WITHOUT conditional logic
            return not has_discriminator
        
        return False
    
    def _has_conditional_party_type(self, system_name, table_name):
        """
        Check if table has conditional party type logic (discriminator column).
        
        Returns True if table uses is_party_type_condition=True
        (e.g., quote_member with relationship_type discriminator)
        """
        table_columns = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['is_party_type_condition'] == True)
        ]
        
        return not table_columns.empty
    
    def determine_party_type(self, system_name, table_name, row):
        """
        Determine party_type for a source row by evaluating condition_logic.
        
        For tables with conditional party types (quote_member, policy_member),
        this evaluates the relationship_type column against condition_logic.
        For simple tables (lead), returns the single party_type.
        """
        # Get party type condition rows for this table
        conditions = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['is_party_type_condition'] == True)
        ]
        
        if len(conditions) == 0:
            # Simple table - single party_type for all rows
            # Get any attribute row to find the party_type
            attr_row = self.metadata_column[
                (self.metadata_column['source_system'] == system_name) &
                (self.metadata_column['source_table'] == table_name) &
                (self.metadata_column['is_attribute'] == True)
            ].iloc[0]
            return attr_row['party_type']
        
        # Conditional party type - evaluate conditions
        for _, cond in conditions.iterrows():
            condition_column = cond['condition_column']
            condition_logic = cond['condition_logic']
            
            # Parse conditions
            if ' IN ' in condition_logic:
                # Handle IN conditions: "relationship_type IN ('Spouse','Child','Dependent')"
                parts = condition_logic.split(' IN ')
                col_name = parts[0].strip()
                values_str = parts[1].strip()
                
                # Extract values from parentheses and remove quotes
                values_str = values_str.strip('()')
                # Split by comma and clean each value
                values = []
                for v in values_str.split(','):
                    clean_v = v.strip().strip("'").strip('"')
                    values.append(clean_v)
                
                if col_name in row and str(row[col_name]) in values:
                    return cond['party_type']
                    
            elif '=' in condition_logic:
                # Simple equality: "relationship_type='Primary'"
                parts = condition_logic.split('=', 1)  # Split only on first =
                col_name = parts[0].strip()
                expected_value = parts[1].strip().strip("'\"")
                
                if col_name in row and str(row[col_name]) == expected_value:
                    return cond['party_type']
        
        raise ValueError(f"Could not determine party_type for {system_name}.{table_name} with row: {row.to_dict()}")
    
    def ingest_source_table(self, system_name, table_name, csv_filename):
        """
        Ingest a single source table into SOURCE_PARTY.
        
        Supports two patterns:
        1. Column-subset: Multiple parties per row (e.g., applicant + spouse in application)
        2. Conditional: One party per row (e.g., quote_member with relationship_type discriminator)
        
        Args:
            system_name: e.g., 'SmartPlus', 'Smile'
            table_name: e.g., 'lead', 'quote_member', 'application'
            csv_filename: e.g., 'smartplus_lead.csv'
        """
        print(f"\nIngesting {system_name}.{table_name}...")
        
        # Load source data
        source_file = self.source_data_dir / csv_filename
        if not source_file.exists():
            print(f"  ⚠ File not found: {source_file}")
            return
        
        df = pd.read_csv(source_file)
        print(f"  → {len(df)} rows")
        
        # Get system_table_id
        system_table_id = self.get_system_table_id(system_name, table_name)
        
        # Get primary key column
        pk_columns = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['is_relationship'] == True)
        ]['source_column'].tolist()
        
        if not pk_columns:
            raise ValueError(f"No primary key column found for {system_name}.{table_name}")
        
        pk_column = pk_columns[0]
        ingestion_timestamp = self.ingestion_timestamp.isoformat()
        
        # Detect pattern
        is_column_subset = self.is_column_subset_table(system_name, table_name)
        has_conditional_logic = self._has_conditional_party_type(system_name, table_name)
        
        if is_column_subset:
            # Pattern 1: Column-subset (multiple parties per row)
            parties_created = self._ingest_column_subset_table(
                system_name, table_name, df, system_table_id, pk_column, ingestion_timestamp
            )
            print(f"  ✓ Created {parties_created} SOURCE_PARTY records (column-subset pattern)")
        elif has_conditional_logic:
            # Pattern 2: Conditional (one party per row with discriminator)
            parties_created = self._ingest_conditional_table(
                system_name, table_name, df, system_table_id, pk_column, ingestion_timestamp
            )
            print(f"  ✓ Created {parties_created} SOURCE_PARTY records (conditional pattern)")
        else:
            # Pattern 3: Simple (one party per row, use main_party_type_id)
            parties_created = self._ingest_simple_table(
                system_name, table_name, df, system_table_id, pk_column, ingestion_timestamp
            )
            print(f"  ✓ Created {parties_created} SOURCE_PARTY records (simple pattern)")
    
    def _ingest_column_subset_table(self, system_name, table_name, df, system_table_id, pk_column, ingestion_timestamp):
        """
        Ingest table with column-subset pattern (multiple parties per row).
        
        For each row:
        - Iterate through all party_types defined for this table
        - Check if party has non-NULL attributes
        - Create SOURCE_PARTY only if attributes exist
        """
        parties_created = 0
        party_types = self.get_table_party_types(system_name, table_name)
        
        for idx, row in df.iterrows():
            pk_value = str(row[pk_column])
            
            # Create SOURCE_PARTY for each party_type that has data
            for party_type in party_types:
                # Get attribute columns for this party_type
                attr_columns = self.metadata_column[
                    (self.metadata_column['source_system'] == system_name) &
                    (self.metadata_column['source_table'] == table_name) &
                    (self.metadata_column['party_type'] == party_type) &
                    (self.metadata_column['is_attribute'] == True)
                ]['source_column'].tolist()
                
                # Check if at least one attribute has a non-NULL value
                has_data = any(pd.notna(row.get(col)) for col in attr_columns)
                
                if not has_data:
                    continue  # Skip if all attributes are NULL
                
                # Extract party_type suffix for source_party_id
                party_suffix = party_type.split('.')[-1]  # e.g., 'applicant' from 'smartplus.application.applicant'
                
                party_type_id = self.get_party_type_id(party_type)
                source_party_id = f"SP_{system_name}_{table_name}_{pk_value}_{party_suffix}"
                
                source_party_record = {
                    'source_party_id': source_party_id,
                    'system_table_id': system_table_id,
                    'party_type_id': party_type_id,
                    'source_record_id': pk_value,
                    'ingestion_timestamp': ingestion_timestamp,
                    'is_active': True
                }
                
                # Process with SCD2
                self.process_source_party_scd2(source_party_record, system_table_id, pk_value, party_type_id)
                parties_created += 1
        
        return parties_created
    
    def _ingest_simple_table(self, system_name, table_name, df, system_table_id, pk_column, ingestion_timestamp):
        """
        Ingest table with simple pattern (one party per row, using main_party_type_id).
        
        Used for business objects (quote, policy, claim) where each row represents
        exactly one entity with no conditional logic.
        
        For each row:
        - Use main_party_type_id from METADATA_SYSTEM_TABLE
        - Create one SOURCE_PARTY
        """
        parties_created = 0
        
        # Get main_party_type_id for this table
        system_row = self.metadata_system[self.metadata_system['system_name'] == system_name]
        if system_row.empty:
            raise ValueError(f"System not found: {system_name}")
        system_id = system_row.iloc[0]['system_id']
        
        table_row = self.metadata_system_table[
            (self.metadata_system_table['system_id'] == system_id) &
            (self.metadata_system_table['table_name'] == table_name)
        ]
        if table_row.empty:
            raise ValueError(f"Table not found: {system_name}.{table_name}")
        
        main_party_type_id = table_row.iloc[0].get('main_party_type_id')
        if pd.isna(main_party_type_id):
            raise ValueError(f"No main_party_type_id defined for {system_name}.{table_name}")
        
        for idx, row in df.iterrows():
            pk_value = str(row[pk_column])
            source_party_id = f"SP_{system_name}_{table_name}_{pk_value}"
            
            source_party_record = {
                'source_party_id': source_party_id,
                'system_table_id': system_table_id,
                'party_type_id': main_party_type_id,
                'source_record_id': pk_value,
                'ingestion_timestamp': ingestion_timestamp,
                'is_active': True
            }
            
            # Process with SCD2
            self.process_source_party_scd2(source_party_record, system_table_id, pk_value, main_party_type_id)
            parties_created += 1
        
        return parties_created
    
    def _ingest_conditional_table(self, system_name, table_name, df, system_table_id, pk_column, ingestion_timestamp):
        """
        Ingest table with conditional pattern (one party per row, type determined by discriminator).
        
        For each row:
        - Evaluate condition_logic to determine party_type
        - Create one SOURCE_PARTY
        """
        parties_created = 0
        
        for idx, row in df.iterrows():
            try:
                # Determine party_type for this row
                party_type = self.determine_party_type(system_name, table_name, row)
                party_type_id = self.get_party_type_id(party_type)
                
                # Create SOURCE_PARTY record
                source_party_id = f"SP_{system_name}_{table_name}_{row[pk_column]}"
                
                source_party_record = {
                    'source_party_id': source_party_id,
                    'system_table_id': system_table_id,
                    'party_type_id': party_type_id,
                    'source_record_id': str(row[pk_column]),
                    'ingestion_timestamp': ingestion_timestamp,
                    'is_active': True
                }
                
                # Process with SCD2
                self.process_source_party_scd2(source_party_record, system_table_id, str(row[pk_column]), party_type_id)
                parties_created += 1
                
            except Exception as e:
                print(f"  ✗ Error processing row {idx}: {e}")
                print(f"    Row data: {row.to_dict()}")
                raise
        
        return parties_created
    
    def process_source_party_scd2(self, source_party_record, system_table_id, source_record_id, party_type_id):
        """
        Process SOURCE_PARTY with SCD2 logic (delta-based):
        - If incremental and party exists: check if changed, close old, create new version
        - If new: create with rec_start_date = now, rec_end_date = NULL
        """
        # Check if this SOURCE_PARTY already exists (current version)
        existing_match = None
        if self.incremental and not self.existing_source_party.empty:
            existing_match = self.existing_source_party[
                (self.existing_source_party['system_table_id'] == system_table_id) &
                (self.existing_source_party['source_record_id'] == source_record_id) &
                (self.existing_source_party['party_type_id'] == party_type_id) &
                (self.existing_source_party['rec_end_date'].isna())
            ]
        
        if existing_match is not None and not existing_match.empty:
            # Party exists - close old version and create new
            idx = existing_match.index[0]
            old_is_active = existing_match.iloc[0]['is_active']
            new_is_active = source_party_record.get('is_active', True)
            
            # Check if anything actually changed
            if old_is_active == new_is_active:
                # No change - don't create new version
                return
            
            # Close old version
            self.existing_source_party.at[idx, 'rec_end_date'] = self.ingestion_timestamp
            
            # Create new version with incremented ID
            old_id = existing_match.iloc[0]['source_party_id']
            if '_v' in old_id:
                base_id, version = old_id.rsplit('_v', 1)
                new_version = int(version) + 1
                source_party_id = f"{base_id}_v{new_version}"
            else:
                source_party_id = f"{old_id}_v2"
        else:
            # New party - use the provided ID
            source_party_id = source_party_record['source_party_id']
        
        # Create SOURCE_PARTY record with SCD2 columns
        scd2_record = {
            'source_party_id': source_party_id,
            'system_table_id': source_party_record['system_table_id'],
            'party_type_id': source_party_record['party_type_id'],
            'source_record_id': source_party_record['source_record_id'],
            'ingestion_timestamp': source_party_record['ingestion_timestamp'],
            'is_active': source_party_record['is_active'],
            'rec_start_date': self.ingestion_timestamp.isoformat(),
            'rec_end_date': None
        }
        
        self.source_party_records.append(scd2_record)
    
    def ingest_all_sources(self):
        """Ingest all source tables that contain party data"""
        
        # Map of tables that contain party records
        # Includes both person tables and business object tables (for FK relationships)
        source_tables = [
            ('SmartPlus', 'lead', 'smartplus_lead.csv'),
            ('SmartPlus', 'quote', 'smartplus_quote.csv'),  # Business object
            ('SmartPlus', 'application', 'smartplus_application.csv'),
            ('SmartPlus', 'quote_member', 'smartplus_quote_member.csv'),
            ('SmartPlus', 'contact_person', 'smartplus_contact_person.csv'),  # Person (for bridge table)
            ('Smile', 'policy', 'smile_policy.csv'),  # Business object
            ('Smile', 'policy_member', 'smile_policy_member.csv'),
            ('Smile', 'claim', 'smile_claim.csv'),  # Business object
        ]
        
        for system, table, filename in source_tables:
            self.ingest_source_table(system, table, filename)
    
    def export_source_party(self):
        """Export SOURCE_PARTY table to CSV with SCD2 history"""
        # Combine existing (with updates) + new records
        if self.incremental and not self.existing_source_party.empty:
            existing_records = self.existing_source_party.to_dict('records')
            all_records = existing_records + self.source_party_records
            df = pd.DataFrame(all_records)
        else:
            df = pd.DataFrame(self.source_party_records)
        
        output_file = self.output_dir / 'source_party.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*70}")
        print(f"✓ Exported SOURCE_PARTY: {len(df)} total records")
        print(f"  File: {output_file}")
        
        # SCD2 statistics
        if 'rec_end_date' in df.columns:
            current_count = df['rec_end_date'].isna().sum()
            historical_count = df['rec_end_date'].notna().sum()
            print(f"\nSCD2 Statistics:")
            print(f"  Current versions:    {current_count:>5}")
            print(f"  Historical versions: {historical_count:>5}")
            print(f"  Total records:       {len(df):>5}")
        
        # Print summary by party_type (current versions only)
        print(f"\nBreakdown by party_type:")
        current_df = df[df['rec_end_date'].isna()] if 'rec_end_date' in df.columns else df
        for party_type_id in current_df['party_type_id'].unique():
            count = len(current_df[current_df['party_type_id'] == party_type_id])
            party_type = self.metadata_party_type[
                self.metadata_party_type['party_type_id'] == party_type_id
            ].iloc[0]['party_type']
            print(f"  {party_type:<45} {count:>3} records")
    
    def run(self):
        """Execute SOURCE_PARTY ingestion (full or incremental)"""
        print("="*70)
        print(f"BRONZE LAYER INGESTION - SOURCE_PARTY ({'INCREMENTAL' if self.incremental else 'FULL'})")
        print("="*70)
        
        self.load_metadata()
        
        if self.incremental:
            self.load_existing_source_party()
        
        self.ingest_all_sources()
        self.export_source_party()
        
        print(f"\n✓ Bronze SOURCE_PARTY ingestion complete ({'incremental' if self.incremental else 'full'})")


if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Bronze SOURCE_PARTY Ingestion')
    parser.add_argument('--source', type=str, default='sources',
                        help='Source directory name (e.g., sources, sources_t1, sources_t2)')
    parser.add_argument('--incremental', action='store_true',
                        help='Run in incremental mode (SCD2)')
    
    args = parser.parse_args()
    
    # Set source directory
    project_root = Path(__file__).parent.parent.parent
    source_data_dir = project_root / 'data' / 'uat_generation' / args.source
    
    print(f"Source directory: {source_data_dir}")
    print(f"Incremental mode: {args.incremental}")
    print()
    
    ingestion = BronzeSourcePartyIngestion(
        source_data_dir=source_data_dir,
        incremental=args.incremental
    )
    ingestion.run()
