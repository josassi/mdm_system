"""
Generate SCD2 UAT Test Data - Bronze Layer Testing

Creates time-series delta snapshots for testing Bronze SCD2 implementation:
- T0: Baseline (existing sources/ folder - NOT modified by this script)
- T1: First change batch (sources_t1/ folder - delta only)
- T2: Second change batch (sources_t2/ folder - delta only)

Usage:
    python generate_uat_scd2_data.py
    
Output:
    data/uat_generation/sources_t1/ - Delta files for T1
    data/uat_generation/sources_t2/ - Delta files for T2
    data/uat_generation/scd2_test_scenarios.md - Documentation
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from uat_scenarios_scd2 import (
    generate_t1_delta,
    generate_t2_delta,
    generate_t0_additions_for_testing
)


def export_delta_files(data, output_dir, timestamp_label):
    """
    Export delta data to CSV files.
    Only exports tables that have data (non-empty).
    
    Args:
        data: Dictionary of dataframes
        output_dir: Path to output directory
        timestamp_label: Label for timestamp (e.g., 'T1', 'T2')
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    source_files = {
        'leads': 'smartplus_lead.csv',
        'quotes': 'smartplus_quote.csv',
        'quote_members': 'smartplus_quote_member.csv',
        'applications': 'smartplus_application.csv',
        'policies': 'smile_policy.csv',
        'policy_members': 'smile_policy_member.csv',
        'claims': 'smile_claim.csv',
        'lead_contacts': 'smartplus_lead_contact.csv',
        'contact_persons': 'smartplus_contact_person.csv'
    }
    
    files_created = 0
    rows_exported = 0
    
    for key, filename in source_files.items():
        if key in data and len(data[key]) > 0:
            filepath = output_dir / filename
            data[key].to_csv(filepath, index=False, date_format='%Y-%m-%d')
            files_created += 1
            rows_exported += len(data[key])
            print(f"  ✓ {filename:40s} ({len(data[key]):>4} delta rows)")
    
    return files_created, rows_exported


def generate_scenario_documentation(t1_data, t2_data, output_dir):
    """Generate markdown documentation for SCD2 test scenarios"""
    
    doc_content = """# Bronze SCD2 UAT Test Scenarios

This document describes the test data generated for validating Bronze layer SCD2 implementation.

## Test Data Structure

```
data/uat_generation/
├── sources/          # T0: Baseline (DO NOT MODIFY - existing test data)
├── sources_t1/       # T1: First change batch (DELTA - new + changed rows only)
├── sources_t2/       # T2: Second change batch (DELTA - additional changes)
└── expected_scd2/    # Expected Bronze outputs (to be generated)
```

## Testing Workflow

1. **Establish T0 Baseline:**
   ```bash
   # Run Bronze ingestion on existing sources/ data
   python src/bronze/ingest_bronze_source_party.py
   python src/bronze/ingest_bronze_raw_attribute.py
   python src/bronze/ingest_bronze_relationship.py
   ```
   
2. **Process T1 Delta (Incremental):**
   ```bash
   # Run Bronze ingestion on sources_t1/ data (incremental mode)
   python src/bronze/ingest_bronze_source_party.py --source=sources_t1 --incremental
   python src/bronze/ingest_bronze_raw_attribute.py --source=sources_t1 --incremental
   python src/bronze/ingest_bronze_relationship.py --source=sources_t1 --incremental
   ```
   
3. **Process T2 Delta (Incremental):**
   ```bash
   # Run Bronze ingestion on sources_t2/ data (incremental mode)
   python src/bronze/ingest_bronze_source_party.py --source=sources_t2 --incremental
   python src/bronze/ingest_bronze_raw_attribute.py --source=sources_t2 --incremental
   python src/bronze/ingest_bronze_relationship.py --source=sources_t2 --incremental
   ```

## Test Scenarios Coverage

### Category 1: SOURCE_PARTY Changes

| ID | Scenario | T1 Delta | T2 Delta | Description |
|----|----------|----------|----------|-------------|
| SCD2-01 | New Party Insert | Lead L100 | Lead L200 | New records created |
| SCD2-02 | Party Soft Delete | Lead L002 (deleted) | - | is_active flag change |
| SCD2-03 | Party Reactivation | Policy P003 (reactivated) | - | Status change |
| SCD2-06 | Bulk Insert | 20 policy members | - | Performance test |
| SCD2-07 | Multiple Changes Same Party | Lead L001 (phone) | Lead L001 (email) | Sequential updates |

### Category 2: RAW_ATTRIBUTE Changes

| ID | Scenario | T1 Delta | T2 Delta | Description |
|----|----------|----------|----------|-------------|
| SCD2-09 | Single Attribute Update | Lead L009 (email) | - | Only 1 attribute changes |
| SCD2-10 | Multi-Attribute Update | App A010 (name+phone) | - | 2 attributes change |
| SCD2-11 | NULL to Value | Lead L011 (phone added) | - | Attribute addition |
| SCD2-12 | Value to NULL | Lead L012 (address removed) | - | Attribute removal |
| SCD2-13 | Attribute Correction | PM013 (typo fix) | - | Data quality correction |
| SCD2-14 | Complex Object Changes | App A014 (spouse removed) | - | Multi-column object |

### Category 3: RELATIONSHIP Changes

| ID | Scenario | T1 Delta | T2 Delta | Description |
|----|----------|----------|----------|-------------|
| SCD2-16 | New FK Relationship | Quote Q016 (lead_id added) | - | FK established |
| SCD2-17 | FK Relationship Broken | Quote Q017 (lead_id removed) | - | FK deleted |
| SCD2-18 | FK Relationship Changed | App A018 (quote_id changed) | - | FK updated |

### Category 4: Edge Cases & Data Quality

| ID | Scenario | T1 Delta | T2 Delta | Description |
|----|----------|----------|----------|-------------|
| SCD2-24 | Rapid Successive Changes | Lead L024 (email) | Lead L024 (phone) | Quick sequence |
| SCD2-27 | Special Characters | Lead L027 (unicode name) | - | Encoding test |

## T1 Delta Summary

"""
    
    # Add T1 statistics
    total_t1_rows = sum(len(df) for df in t1_data.values() if isinstance(df, pd.DataFrame))
    doc_content += f"**Total T1 delta rows:** {total_t1_rows}\n\n"
    
    for table_name, df in t1_data.items():
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            doc_content += f"- **{table_name}:** {len(df)} rows\n"
    
    doc_content += "\n## T2 Delta Summary\n\n"
    
    # Add T2 statistics
    total_t2_rows = sum(len(df) for df in t2_data.values() if isinstance(df, pd.DataFrame))
    doc_content += f"**Total T2 delta rows:** {total_t2_rows}\n\n"
    
    for table_name, df in t2_data.items():
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            doc_content += f"- **{table_name}:** {len(df)} rows\n"
    
    doc_content += """
## Expected Bronze SCD2 Behavior

### SOURCE_PARTY Table

After T0:
```csv
source_party_id,source_record_id,rec_start_date,rec_end_date,is_active
SP_L001,L001,2024-01-25T10:00:00,NULL,True
```

After T1 (L001 phone changed):
```csv
source_party_id,source_record_id,rec_start_date,rec_end_date,is_active
SP_L001,L001,2024-01-25T10:00:00,2024-01-26T10:00:00,True  # Closed
SP_L001_v2,L001,2024-01-26T10:00:00,NULL,True              # New version
```

After T2 (L001 email changed):
```csv
source_party_id,source_record_id,rec_start_date,rec_end_date,is_active
SP_L001,L001,2024-01-25T10:00:00,2024-01-26T10:00:00,True     # V1 closed
SP_L001_v2,L001,2024-01-26T10:00:00,2024-01-27T10:00:00,True  # V2 closed
SP_L001_v3,L001,2024-01-27T10:00:00,NULL,True                 # V3 current
```

### RAW_ATTRIBUTE Table

After T0:
```csv
raw_attribute_id,source_party_id,column_id,raw_value,rec_start_date,rec_end_date
RA_L001_email,SP_L001,COL_EMAIL,john.smith@email.com,2024-01-25T10:00:00,NULL
RA_L001_phone,SP_L001,COL_PHONE,+852-9123-4567,2024-01-25T10:00:00,NULL
```

After T1 (phone changed):
```csv
raw_attribute_id,source_party_id,column_id,raw_value,rec_start_date,rec_end_date
RA_L001_email,SP_L001,COL_EMAIL,john.smith@email.com,2024-01-25T10:00:00,NULL  # Unchanged
RA_L001_phone,SP_L001,COL_PHONE,+852-9123-4567,2024-01-25T10:00:00,2024-01-26T10:00:00  # Closed
RA_L001_phone_v2,SP_L001_v2,COL_PHONE,+852-9999-9999,2024-01-26T10:00:00,NULL  # New
```

**Key Point:** Unchanged attributes (email) remain linked to original SOURCE_PARTY version.

## Validation Checklist

After running Bronze ingestion on T1 and T2, verify:

- [ ] All changed SOURCE_PARTY records have old version closed (rec_end_date populated)
- [ ] All changed SOURCE_PARTY records have new version created (rec_start_date = ingestion time)
- [ ] Only ONE current version per source_record_id (rec_end_date IS NULL)
- [ ] Changed RAW_ATTRIBUTE records have old version closed
- [ ] Unchanged RAW_ATTRIBUTE records have NOT been duplicated
- [ ] New FK relationships create RELATIONSHIP records with rec_start_date
- [ ] Broken FK relationships close RELATIONSHIP records (rec_end_date populated)
- [ ] Unicode characters preserved correctly (SCD2-27)
- [ ] Bulk inserts processed efficiently (SCD2-06)

## Prerequisites

Before running T1/T2 delta ingestion, ensure:

1. T0 baseline data exists in `sources/` folder
2. Bronze tables have SCD2 columns added:
   - `SOURCE_PARTY`: rec_start_date, rec_end_date
   - `RAW_ATTRIBUTE`: rec_start_date, rec_end_date
   - `RELATIONSHIP`: Already has rec_start_date, rec_end_date
3. Bronze ingestion scripts support `--incremental` mode
4. Change detection logic implemented (compare source snapshot with existing Bronze)

## Notes

- T1 and T2 contain **DELTA only** (not full snapshots)
- Some scenarios require baseline data in T0 (e.g., L009, L011, L012)
- If baseline records don't exist in current sources/, they need to be added manually
- See `uat_scenarios_scd2.py::generate_t0_additions_for_testing()` for required T0 records

## Next Steps

1. Review generated delta files in `sources_t1/` and `sources_t2/`
2. Manually add required T0 baseline records if needed
3. Implement Bronze SCD2 ingestion logic
4. Run T0 baseline ingestion
5. Run T1 incremental ingestion and validate
6. Run T2 incremental ingestion and validate
7. Compare actual vs. expected SCD2 behavior
"""
    
    # Write documentation
    doc_file = output_dir / 'scd2_test_scenarios.md'
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    return doc_file


def generate_t0_reference_data(output_dir):
    """
    Generate reference file listing T0 baseline records needed for testing.
    Does NOT create actual CSV files (to avoid overwriting existing sources/).
    """
    data = generate_t0_additions_for_testing()
    
    # Convert to DataFrames
    datasets = {}
    for key, records in data.items():
        if records:
            datasets[key] = pd.DataFrame(records)
    
    reference_content = """# T0 Baseline Records Required for SCD2 Testing

The following records should exist in T0 (sources/ folder) for SCD2 test scenarios to work properly.

**IMPORTANT:** This is a REFERENCE file only. Do NOT overwrite existing sources/ data.
If these records don't exist, manually add them to the appropriate source CSV files.

"""
    
    for table_name, df in datasets.items():
        if len(df) > 0:
            reference_content += f"\n## {table_name} ({len(df)} records needed)\n\n"
            reference_content += "Required records (key fields only):\n\n"
            
            # Show key fields depending on table type
            if table_name == 'leads':
                key_cols = ['lead_id', 'first_name', 'last_name', 'email', 'phone']
            elif table_name == 'quotes':
                key_cols = ['quote_id', 'lead_id', 'status']
            elif table_name == 'policy_members':
                key_cols = ['pm_id', 'first_name', 'last_name', 'gov_id_number']
            else:
                key_cols = df.columns[:5].tolist()  # First 5 columns
            
            display_cols = [col for col in key_cols if col in df.columns]
            
            # Simple table format (avoid tabulate dependency)
            reference_content += "```csv\n"
            reference_content += df[display_cols].to_csv(index=False)
            reference_content += "```\n"
    
    reference_file = output_dir / 't0_baseline_requirements.md'
    with open(reference_file, 'w', encoding='utf-8') as f:
        f.write(reference_content)
    
    return reference_file


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.parent
    base_dir = project_root / 'data' / 'uat_generation'
    
    # Output directories
    t1_dir = base_dir / 'sources_t1'
    t2_dir = base_dir / 'sources_t2'
    
    print("=" * 70)
    print("GENERATING BRONZE SCD2 UAT TEST DATA")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT:")
    print("  - T0 baseline: Existing sources/ folder (NOT modified)")
    print("  - T1 delta: New sources_t1/ folder (new + changed rows only)")
    print("  - T2 delta: New sources_t2/ folder (additional changes only)")
    print()
    
    # Generate T1 delta data
    print("\n" + "=" * 70)
    print("GENERATING T1 DELTA (First Change Batch)")
    print("=" * 70)
    
    t1_data_dict = generate_t1_delta()
    
    # Convert to DataFrames
    t1_datasets = {}
    for key, records in t1_data_dict.items():
        if records and key not in ['expected_clusters', 'expected_entities', 'expected_matches']:
            t1_datasets[key] = pd.DataFrame(records)
    
    # Export T1 delta files
    t1_files, t1_rows = export_delta_files(t1_datasets, t1_dir, 'T1')
    
    print(f"\n✓ T1 Delta: {t1_files} files, {t1_rows} total delta rows")
    
    # Generate T2 delta data
    print("\n" + "=" * 70)
    print("GENERATING T2 DELTA (Second Change Batch)")
    print("=" * 70)
    
    t2_data_dict = generate_t2_delta()
    
    # Convert to DataFrames
    t2_datasets = {}
    for key, records in t2_data_dict.items():
        if records and key not in ['expected_clusters', 'expected_entities', 'expected_matches']:
            t2_datasets[key] = pd.DataFrame(records)
    
    # Export T2 delta files
    t2_files, t2_rows = export_delta_files(t2_datasets, t2_dir, 'T2')
    
    print(f"\n✓ T2 Delta: {t2_files} files, {t2_rows} total delta rows")
    
    # Generate documentation
    print("\n" + "=" * 70)
    print("GENERATING DOCUMENTATION")
    print("=" * 70)
    
    doc_file = generate_scenario_documentation(t1_datasets, t2_datasets, base_dir)
    print(f"\n✓ Test scenarios documented: {doc_file}")
    
    # Generate T0 reference
    ref_file = generate_t0_reference_data(base_dir)
    print(f"✓ T0 baseline requirements: {ref_file}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ SCD2 UAT TEST DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nGenerated files:")
    print(f"  T1 Delta:  {t1_dir}/ ({t1_files} files, {t1_rows} rows)")
    print(f"  T2 Delta:  {t2_dir}/ ({t2_files} files, {t2_rows} rows)")
    print(f"  Docs:      {base_dir}/scd2_test_scenarios.md")
    print(f"  Reference: {base_dir}/t0_baseline_requirements.md")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. Review generated delta files in sources_t1/ and sources_t2/
2. Check t0_baseline_requirements.md - add missing T0 records if needed
3. Implement Bronze SCD2 ingestion logic:
   - Add rec_start_date, rec_end_date columns to SOURCE_PARTY, RAW_ATTRIBUTE
   - Implement change detection (compare source vs existing Bronze)
   - Implement SCD2 logic (close old records, insert new versions)
4. Test workflow:
   a. Run Bronze ingestion on sources/ (T0 baseline)
   b. Run Bronze ingestion on sources_t1/ --incremental (T1 delta)
   c. Verify SCD2 behavior (check rec_start_date/rec_end_date)
   d. Run Bronze ingestion on sources_t2/ --incremental (T2 delta)
   e. Verify cumulative SCD2 history
5. See scd2_test_scenarios.md for detailed validation checklist
""")


if __name__ == '__main__':
    main()
