# Bronze SCD2 UAT Test Scenarios

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

**Total T1 delta rows:** 37

- **leads:** 8 rows
- **quotes:** 4 rows
- **applications:** 3 rows
- **policies:** 1 rows
- **policy_members:** 21 rows

## T2 Delta Summary

**Total T2 delta rows:** 3

- **leads:** 3 rows

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
