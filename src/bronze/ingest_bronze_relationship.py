"""
Bronze Layer Ingestion - RELATIONSHIP Table
Discovers and creates relationships between SOURCE_PARTY records using metadata.
Handles both FK-based relationships and semantic within-row relationships.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid


class BronzeRelationshipIngestion:
    """Ingests relationships using metadata-driven discovery logic"""
    
    def __init__(self, metadata_dir=None, source_data_dir=None, bronze_dir=None):
        # Default to project root paths
        project_root = Path(__file__).parent.parent.parent
        self.metadata_dir = Path(metadata_dir) if metadata_dir else project_root / 'data' / 'uat_generation' / 'metadata'
        self.source_data_dir = Path(source_data_dir) if source_data_dir else project_root / 'data' / 'uat_generation' / 'sources'
        self.bronze_dir = Path(bronze_dir) if bronze_dir else project_root / 'data' / 'bronze'
        
        # Metadata tables
        self.metadata_system = None
        self.metadata_system_table = None
        self.metadata_party_type = None
        self.metadata_relationship = None
        self.metadata_party_type_relationship = None
        self.metadata_column = None
        
        # Bronze tables
        self.source_party = None
        
        # Output
        self.relationship_records = []
        
    def load_metadata(self):
        """Load all required metadata tables"""
        print("Loading metadata...")
        
        self.metadata_system = pd.read_csv(self.metadata_dir / 'metadata_system.csv')
        self.metadata_system_table = pd.read_csv(self.metadata_dir / 'metadata_system_table.csv')
        self.metadata_party_type = pd.read_csv(self.metadata_dir / 'metadata_party_type.csv')
        self.metadata_relationship = pd.read_csv(self.metadata_dir / 'metadata_relationship.csv')
        self.metadata_party_type_relationship = pd.read_csv(self.metadata_dir / 'metadata_party_type_relationship.csv')
        self.metadata_column = pd.read_csv(self.metadata_dir / 'metadata_column.csv')
        
        print(f"  ✓ Loaded {len(self.metadata_system)} systems")
        print(f"  ✓ Loaded {len(self.metadata_system_table)} tables")
        print(f"  ✓ Loaded {len(self.metadata_party_type)} party types")
        print(f"  ✓ Loaded {len(self.metadata_relationship)} FK-based relationships")
        print(f"  ✓ Loaded {len(self.metadata_party_type_relationship)} semantic relationships")
        print(f"  ✓ Loaded {len(self.metadata_column)} column mappings")
    
    def load_source_party(self):
        """Load SOURCE_PARTY table"""
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
    
    def resolve_column_id(self, column_id):
        """
        Resolve column_id to (system_name, table_name, column_name).
        
        Returns:
            tuple: (system_name, table_name, column_name)
        """
        if pd.isna(column_id):
            return None, None, None
        
        col_row = self.metadata_column[self.metadata_column['column_id'] == column_id]
        if col_row.empty:
            raise ValueError(f"column_id not found: {column_id}")
        
        col = col_row.iloc[0]
        return col['source_system'], col['source_table'], col['source_column']
    
    def ingest_fk_based_relationships(self):
        """
        Discover FK-based relationships using METADATA_RELATIONSHIP.
        
        For each relationship definition:
        1. Load source and target tables
        2. Match on foreign key columns
        3. Create RELATIONSHIP records linking SOURCE_PARTY records
        """
        print("\n" + "="*70)
        print("INGESTING FK-BASED RELATIONSHIPS")
        print("="*70)
        
        for idx, rel_meta in self.metadata_relationship.iterrows():
            # Resolve column_ids to system/table/column
            from_system, from_table, from_column = self.resolve_column_id(rel_meta['from_column_id'])
            to_system, to_table, to_column = self.resolve_column_id(rel_meta['to_column_id'])
            
            print(f"\nProcessing: {from_system}.{from_table}.{from_column} → {to_system}.{to_table}.{to_column}")
            
            # Load source table
            from_file = self.source_data_dir / f"{from_system.lower()}_{from_table}.csv"
            if not from_file.exists():
                print(f"  ⚠ Source file not found: {from_file}")
                continue
            
            from_df = pd.read_csv(from_file)
            
            # Load target table
            to_file = self.source_data_dir / f"{to_system.lower()}_{to_table}.csv"
            if not to_file.exists():
                print(f"  ⚠ Target file not found: {to_file}")
                continue
            
            to_df = pd.read_csv(to_file)
            
            # Get primary key columns for lookups
            from_pk = self._get_primary_key(from_system, from_table)
            to_pk = self._get_primary_key(to_system, to_table)
            
            ingestion_timestamp = datetime.now().isoformat()
            relationships_found = 0
            
            # Get main_party_type_id for from and to tables
            from_main_party_type_id = self._get_main_party_type_id(from_system, from_table)
            to_main_party_type_id = self._get_main_party_type_id(to_system, to_table)
            
            if from_main_party_type_id is None or to_main_party_type_id is None:
                print(f"  ⚠ Warning: No main_party_type_id for one or both tables - skipping")
                print(f"    from_table: {from_table} ({from_main_party_type_id})")
                print(f"    to_table: {to_table} ({to_main_party_type_id})")
                continue
            
            # Check if this is a bridge table relationship
            has_bridge = pd.notna(rel_meta.get('bridge_table_id'))
            
            if has_bridge:
                # Handle bridge table relationship (many-to-many)
                relationships_found = self._ingest_bridge_table_relationship(
                    rel_meta, from_df, to_df, from_pk, to_pk, 
                    from_main_party_type_id, to_main_party_type_id, ingestion_timestamp,
                    from_system, from_table, from_column, to_system, to_table, to_column
                )
                print(f"  ✓ Created {relationships_found} relationships (via bridge table)")
                continue
            
            # Check if composite key (pipe-separated columns)
            is_composite = '|' in from_column
            
            if is_composite:
                # Composite key matching
                from_columns = from_column.split('|')
                to_columns = to_column.split('|')
                
                for _, from_row in from_df.iterrows():
                    # Build composite key value
                    from_key_parts = [str(from_row.get(col, '')) for col in from_columns]
                    
                    # Skip if any part is NULL
                    if any(pd.isna(from_row.get(col)) for col in from_columns):
                        continue
                    
                    # Find matching target row(s) by composite key
                    to_match_filter = True
                    for from_col, to_col in zip(from_columns, to_columns):
                        to_match_filter = to_match_filter & (to_df[to_col] == from_row[from_col])
                    
                    to_matches = to_df[to_match_filter]
                    
                    for _, to_row in to_matches.iterrows():
                        # Find SOURCE_PARTY for from_row (filtered by main_party_type_id)
                        from_party = self._find_source_party(
                            from_system, 
                            from_table, 
                            str(from_row[from_pk]),
                            party_type_id=from_main_party_type_id
                        )
                        
                        # Find SOURCE_PARTY for to_row (filtered by main_party_type_id)
                        to_party = self._find_source_party(
                            to_system, 
                            to_table, 
                            str(to_row[to_pk]),
                            party_type_id=to_main_party_type_id
                        )
                        
                        if from_party is None or to_party is None:
                            continue
                        
                        # Create RELATIONSHIP record
                        relationship_id = f"REL_FK_{from_party}_{to_party}"
                        composite_value = '|'.join(from_key_parts)
                        
                        relationship_record = {
                            'party_relationship_id': relationship_id,
                            'metadata_relationship_id': rel_meta['relationship_id'],
                            'metadata_party_type_relationship_id': None,
                            'from_party_id': from_party,
                            'to_party_id': to_party,
                            'from_matching_value': composite_value,
                            'to_matching_value': composite_value,
                            'rec_start_date': ingestion_timestamp,
                            'rec_end_date': None
                        }
                        
                        self.relationship_records.append(relationship_record)
                        relationships_found += 1
            else:
                # Simple single-column FK matching
                for _, from_row in from_df.iterrows():
                    fk_value = from_row.get(from_column)
                    
                    # Skip NULL foreign keys
                    if pd.isna(fk_value):
                        continue
                    
                    # Find matching target row(s)
                    to_matches = to_df[to_df[to_column] == fk_value]
                    
                    for _, to_row in to_matches.iterrows():
                        # Find SOURCE_PARTY for from_row (filtered by main_party_type_id)
                        from_party = self._find_source_party(
                            from_system, 
                            from_table, 
                            str(from_row[from_pk]),
                            party_type_id=from_main_party_type_id
                        )
                        
                        # Find SOURCE_PARTY for to_row (filtered by main_party_type_id)
                        to_party = self._find_source_party(
                            to_system, 
                            to_table, 
                            str(to_row[to_pk]),
                            party_type_id=to_main_party_type_id
                        )
                        
                        if from_party is None or to_party is None:
                            continue
                        
                        # Create RELATIONSHIP record
                        relationship_id = f"REL_FK_{from_party}_{to_party}"
                        
                        relationship_record = {
                            'party_relationship_id': relationship_id,
                            'metadata_relationship_id': rel_meta['relationship_id'],
                            'metadata_party_type_relationship_id': None,
                            'from_party_id': from_party,
                            'to_party_id': to_party,
                            'from_matching_value': str(fk_value),
                            'to_matching_value': str(fk_value),
                            'rec_start_date': ingestion_timestamp,
                            'rec_end_date': None
                        }
                        
                        self.relationship_records.append(relationship_record)
                        relationships_found += 1
            
            print(f"  ✓ Created {relationships_found} relationships")
    
    def ingest_semantic_relationships(self):
        """
        Discover same-row semantic relationships using METADATA_PARTY_TYPE_RELATIONSHIP.
        
        For column-subset pattern (e.g., applicant + spouse in same application row):
        1. Group SOURCE_PARTY by (system_table_id, source_record_id)
        2. For groups with multiple parties, apply relationship rules
        3. Create RELATIONSHIP if party_types match the rule
        
        NOTE: No condition_logic needed - parties in same row are implicitly related.
        """
        print("\n" + "="*70)
        print("INGESTING SAME-ROW SEMANTIC RELATIONSHIPS")
        print("="*70)
        
        ingestion_timestamp = datetime.now().isoformat()
        
        for idx, rel_meta in self.metadata_party_type_relationship.iterrows():
            print(f"\nProcessing: {rel_meta['from_party_type']} → {rel_meta['to_party_type']}")
            print(f"  Source: {rel_meta['source_system']}.{rel_meta['source_table']}")
            
            # Get system_table_id for this table
            system_row = self.metadata_system[self.metadata_system['system_name'] == rel_meta['source_system']]
            if system_row.empty:
                print(f"  ⚠ System not found: {rel_meta['source_system']}")
                continue
            system_id = system_row.iloc[0]['system_id']
            
            table_row = self.metadata_system_table[
                (self.metadata_system_table['system_id'] == system_id) &
                (self.metadata_system_table['table_name'] == rel_meta['source_table'])
            ]
            if table_row.empty:
                print(f"  ⚠ Table not found: {rel_meta['source_table']}")
                continue
            system_table_id = table_row.iloc[0]['system_table_id']
            
            # Filter SOURCE_PARTY for this table
            table_parties = self.source_party[self.source_party['system_table_id'] == system_table_id]
            
            relationships_found = 0
            
            # Group by source_record_id to find parties in the same row
            for source_record_id, group in table_parties.groupby('source_record_id'):
                if len(group) < 2:
                    continue  # Need at least 2 parties in same row
                
                # Get party_types in this row
                party_type_ids = group['party_type_id'].tolist()
                party_types_map = {}
                for _, party_row in group.iterrows():
                    pt_row = self.metadata_party_type[
                        self.metadata_party_type['party_type_id'] == party_row['party_type_id']
                    ]
                    if not pt_row.empty:
                        party_type = pt_row.iloc[0]['party_type']
                        party_types_map[party_type] = party_row['source_party_id']
                
                # Check if this row has the party_types specified in the relationship rule
                if rel_meta['from_party_type'] in party_types_map and rel_meta['to_party_type'] in party_types_map:
                    from_party_id = party_types_map[rel_meta['from_party_type']]
                    to_party_id = party_types_map[rel_meta['to_party_type']]
                    
                    # Create forward relationship
                    relationship_id = f"REL_SR_{from_party_id}_{to_party_id}"
                    
                    relationship_record = {
                        'party_relationship_id': relationship_id,
                        'metadata_relationship_id': None,
                        'metadata_party_type_relationship_id': rel_meta['party_type_relationship_id'],
                        'from_party_id': from_party_id,
                        'to_party_id': to_party_id,
                        'from_matching_value': source_record_id,
                        'to_matching_value': source_record_id,
                        'rec_start_date': ingestion_timestamp,
                        'rec_end_date': None
                    }
                    
                    self.relationship_records.append(relationship_record)
                    relationships_found += 1
                    
                    # Handle bidirectional relationships
                    if rel_meta['is_bidirectional']:
                        reverse_relationship_id = f"REL_SR_{to_party_id}_{from_party_id}"
                        reverse_record = relationship_record.copy()
                        reverse_record['party_relationship_id'] = reverse_relationship_id
                        reverse_record['from_party_id'] = to_party_id
                        reverse_record['to_party_id'] = from_party_id
                        self.relationship_records.append(reverse_record)
                        relationships_found += 1
            
            print(f"  ✓ Created {relationships_found} relationships")
    
    def _ingest_bridge_table_relationship(self, rel_meta, from_df, to_df, from_pk, to_pk, 
                                          from_main_party_type_id, to_main_party_type_id, ingestion_timestamp,
                                          from_system, from_table, from_column, to_system, to_table, to_column):
        """
        Ingest many-to-many relationships via bridge table.
        
        Example: lead → lead_contact → contact_person
        
        Logic:
        1. Load bridge table
        2. For each bridge row:
           - Match from_table via from_bridge_column
           - Match to_table via to_bridge_column
           - Find SOURCE_PARTY for both sides using main_party_type_id
           - Create RELATIONSHIP record
        """
        relationships_found = 0
        
        # Resolve bridge table_id to get bridge table name
        bridge_table_id = rel_meta['bridge_table_id']
        bridge_system_table = self.metadata_system_table[
            self.metadata_system_table['system_table_id'] == bridge_table_id
        ]
        if bridge_system_table.empty:
            print(f"    ⚠ Bridge table_id not found: {bridge_table_id}")
            return 0
        
        bridge_table_name = bridge_system_table.iloc[0]['table_name']
        
        # Load bridge table
        bridge_file = self.source_data_dir / f"{from_system.lower()}_{bridge_table_name}.csv"
        
        if not bridge_file.exists():
            print(f"    ⚠ Bridge table file not found: {bridge_file}")
            return 0
        
        bridge_df = pd.read_csv(bridge_file)
        print(f"    → Bridge table '{bridge_table_name}': {len(bridge_df)} rows")
        
        # Resolve bridge column_ids
        _, _, from_bridge_col = self.resolve_column_id(rel_meta['bridge_column_source_id'])
        _, _, to_bridge_col = self.resolve_column_id(rel_meta['bridge_column_target_id'])
        
        # Iterate through bridge table
        for _, bridge_row in bridge_df.iterrows():
            from_fk_value = bridge_row.get(from_bridge_col)
            to_fk_value = bridge_row.get(to_bridge_col)
            
            # Skip NULL foreign keys
            if pd.isna(from_fk_value) or pd.isna(to_fk_value):
                continue
            
            # Find matching from_table row
            from_match = from_df[from_df[from_column] == from_fk_value]
            if from_match.empty:
                continue
            
            # Find matching to_table row
            to_match = to_df[to_df[to_column] == to_fk_value]
            if to_match.empty:
                continue
            
            # Get first match (should be unique based on FK integrity)
            from_row = from_match.iloc[0]
            to_row = to_match.iloc[0]
            
            # Find SOURCE_PARTY for from_row (filtered by main_party_type_id)
            from_party = self._find_source_party(
                from_system, 
                from_table, 
                str(from_row[from_pk]),
                party_type_id=from_main_party_type_id
            )
            
            # Find SOURCE_PARTY for to_row (filtered by main_party_type_id)
            to_party = self._find_source_party(
                to_system, 
                to_table, 
                str(to_row[to_pk]),
                party_type_id=to_main_party_type_id
            )
            
            if from_party is None or to_party is None:
                continue
            
            # Create RELATIONSHIP record
            relationship_id = f"REL_FK_{from_party}_{to_party}"
            
            relationship_record = {
                'party_relationship_id': relationship_id,
                'metadata_relationship_id': rel_meta['relationship_id'],
                'metadata_party_type_relationship_id': None,
                'from_party_id': from_party,
                'to_party_id': to_party,
                'from_matching_value': str(from_fk_value),
                'to_matching_value': str(to_fk_value),
                'rec_start_date': ingestion_timestamp,
                'rec_end_date': None
            }
            
            self.relationship_records.append(relationship_record)
            relationships_found += 1
        
        return relationships_found
    
    def _get_primary_key(self, system_name, table_name):
        """Get primary key column name for a table"""
        pk_columns = self.metadata_column[
            (self.metadata_column['source_system'] == system_name) &
            (self.metadata_column['source_table'] == table_name) &
            (self.metadata_column['is_relationship'] == True)
        ]['source_column'].tolist()
        
        if not pk_columns:
            raise ValueError(f"No primary key found for {system_name}.{table_name}")
        
        return pk_columns[0]
    
    def _get_main_party_type_id(self, system_name, table_name):
        """
        Get main_party_type_id for a table from METADATA_SYSTEM_TABLE.
        
        Returns:
            main_party_type_id or None (for business object tables)
        """
        system_row = self.metadata_system[self.metadata_system['system_name'] == system_name]
        if system_row.empty:
            return None
        system_id = system_row.iloc[0]['system_id']
        
        table_row = self.metadata_system_table[
            (self.metadata_system_table['system_id'] == system_id) &
            (self.metadata_system_table['table_name'] == table_name)
        ]
        if table_row.empty:
            return None
        
        main_party_type_id = table_row.iloc[0].get('main_party_type_id')
        return main_party_type_id if pd.notna(main_party_type_id) else None
    
    def _find_source_party(self, system_name, table_name, source_record_id, party_type_id=None):
        """
        Find source_party_id for a given source record.
        
        Args:
            system_name: e.g., 'SmartPlus'
            table_name: e.g., 'application'
            source_record_id: Primary key value
            party_type_id: Optional party_type_id to filter by (for main_party_type_id)
        
        Returns:
            source_party_id or None
        """
        # Get system_table_id
        system_row = self.metadata_system[self.metadata_system['system_name'] == system_name]
        if system_row.empty:
            return None
        system_id = system_row.iloc[0]['system_id']
        
        table_row = self.metadata_system_table[
            (self.metadata_system_table['system_id'] == system_id) &
            (self.metadata_system_table['table_name'] == table_name)
        ]
        if table_row.empty:
            return None
        system_table_id = table_row.iloc[0]['system_table_id']
        
        # Find SOURCE_PARTY
        party_filter = (
            (self.source_party['system_table_id'] == system_table_id) &
            (self.source_party['source_record_id'] == source_record_id)
        )
        
        # If party_type_id specified, filter by it (for main_party_type_id)
        if party_type_id is not None:
            party_filter = party_filter & (self.source_party['party_type_id'] == party_type_id)
        
        party = self.source_party[party_filter]
        
        if party.empty:
            return None
        
        return party.iloc[0]['source_party_id']
    
    def _extract_group_column(self, condition_logic):
        """
        Extract the grouping column from condition_logic.
        e.g., "from.quote_id=to.quote_id" → "quote_id"
        """
        if 'quote_id' in condition_logic:
            return 'quote_id'
        elif 'policy_id' in condition_logic:
            return 'policy_id'
        else:
            raise ValueError(f"Cannot extract group column from: {condition_logic}")
    
    def _find_parties_matching_condition(self, group_df, condition_logic, party_role, system_name, table_name):
        """
        Find parties matching a specific condition within a group.
        
        Args:
            group_df: DataFrame of rows in the same group
            condition_logic: Full condition string
            party_role: 'from' or 'to'
            
        Returns:
            List of (source_party_id, primary_key_value) tuples
        """
        # Parse condition for this role
        # e.g., "from.relationship_type='Primary'" from full condition
        condition_parts = [c.strip() for c in condition_logic.split(' AND ')]
        
        role_conditions = []
        for part in condition_parts:
            if part.startswith(f'{party_role}.'):
                # Skip join conditions like "from.quote_id=to.quote_id"
                if '=to.' in part or '=from.' in part:
                    continue
                # Remove role prefix
                clean_condition = part.replace(f'{party_role}.', '')
                role_conditions.append(clean_condition)
        
        if not role_conditions:
            return []
        
        # Apply conditions to filter rows
        filtered_df = group_df.copy()
        
        for condition in role_conditions:
            if ' IN ' in condition:
                # Handle IN clause: "relationship_type IN ('Spouse','Child','Dependent')"
                parts = condition.split(' IN ')
                col_name = parts[0].strip()
                values_str = parts[1].strip().strip('()')
                values = [v.strip().strip("'\"") for v in values_str.split(',')]
                filtered_df = filtered_df[filtered_df[col_name].isin(values)]
            elif '=' in condition:
                # Simple equality: "relationship_type='Primary'"
                parts = condition.split('=', 1)
                col_name = parts[0].strip()
                expected_value = parts[1].strip().strip("'\"")
                filtered_df = filtered_df[filtered_df[col_name] == expected_value]
        
        # Get primary key
        pk_column = self._get_primary_key(system_name, table_name)
        
        # Find SOURCE_PARTY for each matching row
        result = []
        for _, row in filtered_df.iterrows():
            source_party_id = self._find_source_party(system_name, table_name, str(row[pk_column]))
            if source_party_id:
                result.append((source_party_id, row[pk_column]))
        
        return result
    
    def export_relationship(self):
        """Export RELATIONSHIP table to CSV"""
        df = pd.DataFrame(self.relationship_records)
        output_file = self.bronze_dir / 'relationship.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*70}")
        print(f"✓ Exported RELATIONSHIP: {len(df)} records")
        print(f"  File: {output_file}")
        
        if len(df) > 0:
            # Print summary by type
            fk_count = len(df[df['metadata_relationship_id'].notna()])
            semantic_count = len(df[df['metadata_party_type_relationship_id'].notna()])
            
            print(f"\nBreakdown by relationship type:")
            print(f"  FK-based relationships:       {fk_count:>3}")
            print(f"  Semantic relationships:       {semantic_count:>3}")
        else:
            print("\n⚠ No relationships created - check source data and metadata")
    
    def run(self):
        """Execute full RELATIONSHIP ingestion"""
        print("="*70)
        print("BRONZE LAYER INGESTION - RELATIONSHIP")
        print("="*70)
        
        self.load_metadata()
        self.load_source_party()
        self.ingest_fk_based_relationships()
        self.ingest_semantic_relationships()
        self.export_relationship()
        
        print("\n✓ Bronze RELATIONSHIP ingestion complete")


if __name__ == '__main__':
    ingestion = BronzeRelationshipIngestion()
    ingestion.run()
