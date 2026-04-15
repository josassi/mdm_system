"""
Bronze SCD2 UAT Scenarios - Comprehensive CDC Test Coverage

This module generates time-series test data (T0, T1, T2) for validating
Bronze layer SCD2 (Slowly Changing Dimension Type 2) implementation.

T0: Baseline data (existing sources/ folder - DO NOT MODIFY)
T1: First change batch - delta containing new + changed rows
T2: Second change batch - delta containing additional new + changed rows

Coverage: 27 scenarios across 4 categories
- SOURCE_PARTY changes (8 scenarios)
- RAW_ATTRIBUTE changes (7 scenarios)  
- RELATIONSHIP changes (6 scenarios)
- Edge cases & data quality (6 scenarios)
"""

from datetime import date, datetime, timedelta
from uat_scenarios_helpers import init_data_structure, now

# T1 is 24 hours after T0
T1_OFFSET = timedelta(hours=24)
# T2 is 48 hours after T0
T2_OFFSET = timedelta(hours=48)


def get_t1_timestamp():
    """Get T1 timestamp (24 hours after now)"""
    return datetime.now() + T1_OFFSET


def get_t2_timestamp():
    """Get T2 timestamp (48 hours after now)"""
    return datetime.now() + T2_OFFSET


# ========================================================================
# CATEGORY 1: SOURCE_PARTY CHANGES (8 scenarios)
# ========================================================================

def scd2_01_new_party_insert():
    """
    SCD2-01: New Party Insert
    T1: Create new lead L100
    Expected: New SOURCE_PARTY record with rec_start_date=T1
    """
    return {
        'leads': [{
            'lead_id': 'L100',
            'first_name': 'NewLead',
            'last_name': 'Person',
            'date_of_birth': date(1990, 1, 1),
            'email': 'newlead@test.com',
            'phone': '+852-9100-0000',
            'address': 'Test Address 100',
            'gov_id_type': 'HKID',
            'gov_id_number': 'Z100000(0)',
            'created_date': get_t1_timestamp().date(),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_02_party_soft_delete():
    """
    SCD2-02: Party Soft Delete (is_active flag)
    T1: Mark existing lead L002 as inactive
    Expected: Old record closed, new version with is_active=False
    """
    # Return updated version of L002 (assuming it exists in T0)
    return {
        'leads': [{
            'lead_id': 'L002',
            'first_name': 'Sarah',
            'last_name': 'Lee',
            'date_of_birth': date(1982, 3, 20),
            'email': 'sarah.lee@email.com',
            'phone': '+852-9234-5678',
            'address': 'Unit 12B, 456 Nathan Road, Kowloon, HK',
            'gov_id_type': 'HKID',
            'gov_id_number': 'B234567(8)',
            'created_date': date(2024, 1, 25),  # Original date
            'source_system': 'SmartPlus',
            'is_deleted': True  # Soft delete marker
        }]
    }


def scd2_03_party_reactivation():
    """
    SCD2-03: Party Reactivation
    T1: Reactivate cancelled policy P003
    Expected: New SOURCE_PARTY version with updated status
    """
    return {
        'policies': [{
            'policy_id': 'P003',
            'contract_number': 'C003',
            'application_id': 'A003',
            'policy_type': 'Family',
            'start_date': date(2024, 4, 1),
            'end_date': None,
            'status': 'Active',  # Changed from Cancelled
            'annual_premium': 12000.00,
            'created_date': get_t1_timestamp().date(),
            'source_system': 'Smile'
        }]
    }


def scd2_07_multiple_changes_same_party():
    """
    SCD2-07: Multiple Changes Same Party
    T1: Update L001 phone
    T2: Update L001 email
    Expected: 3 versions total in SOURCE_PARTY
    """
    t1_data = {
        'leads': [{
            'lead_id': 'L001',
            'first_name': 'John',
            'last_name': 'Smith',
            'date_of_birth': date(1985, 6, 15),
            'email': 'john.smith@email.com',  # Unchanged
            'phone': '+852-9999-9999',  # CHANGED in T1
            'address': "Flat 5A, 123 Queen's Road, Central, HK",
            'gov_id_type': 'HKID',
            'gov_id_number': 'A123456(7)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }
    
    t2_data = {
        'leads': [{
            'lead_id': 'L001',
            'first_name': 'John',
            'last_name': 'Smith',
            'date_of_birth': date(1985, 6, 15),
            'email': 'john.new@email.com',  # CHANGED in T2
            'phone': '+852-9999-9999',  # Already changed in T1
            'address': "Flat 5A, 123 Queen's Road, Central, HK",
            'gov_id_type': 'HKID',
            'gov_id_number': 'A123456(7)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }
    
    return t1_data, t2_data


def scd2_06_bulk_insert():
    """
    SCD2-06: Bulk Insert (Performance Test)
    T1: Insert 20 new policy members at once
    Expected: All 20 SOURCE_PARTY records created efficiently
    """
    members = []
    for i in range(20):
        members.append({
            'pm_id': f'PM_BULK_{i:03d}',
            'policy_id': 'P_BULK_TEST',
            'contract_number': f'C_BULK_{i:03d}',
            'member_number': i + 1,
            'first_name': f'BulkMember{i}',
            'last_name': 'TestFamily',
            'date_of_birth': date(1990 + (i % 30), (i % 12) + 1, (i % 28) + 1),
            'email': f'bulk{i}@test.com',
            'phone': f'+852-9{i:03d}-{i:04d}',
            'gov_id_type': 'HKID',
            'gov_id_number': f'B{i:06d}(0)',
            'relationship_type': 'Primary' if i == 0 else 'Child',
            'gender': 'M' if i % 2 == 0 else 'F',
            'coverage_start_date': get_t1_timestamp().date(),
            'coverage_end_date': None,
            'is_active': True,
            'created_date': get_t1_timestamp().date(),
            'source_system': 'Smile'
        })
    
    return {'policy_members': members}


# ========================================================================
# CATEGORY 2: RAW_ATTRIBUTE CHANGES (7 scenarios)
# ========================================================================

def scd2_09_single_attribute_update():
    """
    SCD2-09: Single Attribute Update
    T1: Update only email for lead L009
    Expected: Only email RAW_ATTRIBUTE gets new version, others unchanged
    """
    return {
        'leads': [{
            'lead_id': 'L009',
            'first_name': 'Alice',
            'last_name': 'Chen',
            'date_of_birth': date(1988, 5, 10),
            'email': 'alice.new@email.com',  # CHANGED
            'phone': '+852-9123-4567',  # Unchanged
            'address': 'Test Address 9',
            'gov_id_type': 'HKID',
            'gov_id_number': 'A900000(9)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_10_multi_attribute_update():
    """
    SCD2-10: Multi-Attribute Update
    T1: Update both applicant name and phone in application A010
    Expected: 2 RAW_ATTRIBUTE records closed, 2 new created
    """
    return {
        'applications': [{
            'app_id': 'A010',
            'quote_id': 'Q010',
            'application_date': date(2024, 10, 25),
            'status': 'Approved',
            'contract_number': 'C011',
            'applicant_first_name': 'Jonathan',  # CHANGED from John
            'applicant_last_name': 'Martinez',
            'applicant_dob': date(1987, 2, 18),
            'applicant_email': 'susan.martinez@email.com',
            'applicant_phone': '+852-9999-8888',  # CHANGED
            'applicant_gov_id': 'E123456(7)',
            'spouse_first_name': None,
            'spouse_last_name': None,
            'spouse_dob': None,
            'spouse_email': None,
            'spouse_phone': None,
            'spouse_gov_id': None,
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_11_null_to_value():
    """
    SCD2-11: NULL to Value (Attribute Addition)
    T1: Add phone number to lead L011 (previously NULL)
    Expected: New RAW_ATTRIBUTE created (no old record to close)
    """
    return {
        'leads': [{
            'lead_id': 'L011',
            'first_name': 'NullTest',
            'last_name': 'Person',
            'date_of_birth': date(1985, 1, 1),
            'email': 'nulltest@email.com',
            'phone': '+852-9111-1111',  # ADDED (was NULL in T0)
            'address': None,
            'gov_id_type': 'HKID',
            'gov_id_number': 'N110000(0)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_12_value_to_null():
    """
    SCD2-12: Value to NULL (Attribute Removal)
    T1: Remove address from lead L012
    Expected: Old RAW_ATTRIBUTE closed, no new record (NULL not stored)
    """
    return {
        'leads': [{
            'lead_id': 'L012',
            'first_name': 'RemoveAttr',
            'last_name': 'Person',
            'date_of_birth': date(1985, 2, 2),
            'email': 'removeattr@email.com',
            'phone': '+852-9122-2222',
            'address': None,  # REMOVED (was populated in T0)
            'gov_id_type': 'HKID',
            'gov_id_number': 'R120000(0)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_13_attribute_correction():
    """
    SCD2-13: Attribute Value Correction (Typo Fix)
    T1: Fix typo in first name (Jonh -> John)
    Expected: Old RAW_ATTRIBUTE closed with typo preserved, new correct version
    """
    return {
        'policy_members': [{
            'pm_id': 'PM013',
            'policy_id': 'P013',
            'contract_number': 'C013',
            'member_number': 1,
            'first_name': 'John',  # CORRECTED from 'Jonh' (typo)
            'last_name': 'Corrected',
            'date_of_birth': date(1990, 3, 3),
            'email': 'corrected@email.com',
            'phone': '+852-9133-3333',
            'gov_id_type': 'HKID',
            'gov_id_number': 'C130000(0)',
            'relationship_type': 'Primary',
            'gender': 'M',
            'coverage_start_date': date(2024, 1, 1),
            'coverage_end_date': None,
            'is_active': True,
            'created_date': date(2024, 1, 25),
            'source_system': 'Smile'
        }]
    }


def scd2_14_complex_object_changes():
    """
    SCD2-14: Complex Object Changes (Multi-member)
    T1: Remove spouse from application A014 (all spouse columns -> NULL)
    Expected: Spouse SOURCE_PARTY and all spouse RAW_ATTRIBUTE records closed
    """
    return {
        'applications': [{
            'app_id': 'A014',
            'quote_id': 'Q014',
            'application_date': date(2024, 3, 5),
            'status': 'Approved',
            'contract_number': 'C014',
            'applicant_first_name': 'ComplexTest',
            'applicant_last_name': 'Person',
            'applicant_dob': date(1985, 4, 4),
            'applicant_email': 'complex@email.com',
            'applicant_phone': '+852-9144-4444',
            'applicant_gov_id': 'C140000(0)',
            # Spouse REMOVED (all NULL now)
            'spouse_first_name': None,
            'spouse_last_name': None,
            'spouse_dob': None,
            'spouse_email': None,
            'spouse_phone': None,
            'spouse_gov_id': None,
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


# ========================================================================
# CATEGORY 3: RELATIONSHIP CHANGES (6 scenarios + 2 cluster scenarios)
# ========================================================================

def scd2_16_new_fk_relationship():
    """
    SCD2-16: New FK Relationship Established
    T1: Quote Q016 updated with lead_id=L016 (previously NULL)
    Expected: New RELATIONSHIP record created
    """
    return {
        'quotes': [{
            'quote_id': 'Q016',
            'lead_id': 'L016',  # ADDED FK (was NULL in T0)
            'quote_type': 'Individual',
            'contract_number': 'C016',
            'total_premium': 6000.00,
            'quote_date': date(2024, 1, 20),
            'status': 'Accepted',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_17_fk_relationship_broken():
    """
    SCD2-17: FK Relationship Broken
    T1: Quote Q017 FK to lead removed (lead_id -> NULL)
    Expected: Old RELATIONSHIP closed, no new record
    """
    return {
        'quotes': [{
            'quote_id': 'Q017',
            'lead_id': None,  # REMOVED FK (was L017 in T0)
            'quote_type': 'Individual',
            'contract_number': 'C017',
            'total_premium': 7000.00,
            'quote_date': date(2024, 1, 21),
            'status': 'Accepted',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_18_fk_relationship_changed():
    """
    SCD2-18: FK Relationship Changed
    T1: Application A018 quote_id changed from Q018A to Q018B
    Expected: Old RELATIONSHIP closed, new RELATIONSHIP created
    """
    return {
        'applications': [{
            'app_id': 'A018',
            'quote_id': 'Q018B',  # CHANGED from Q018A
            'application_date': date(2024, 1, 22),
            'status': 'Approved',
            'contract_number': 'C018',
            'applicant_first_name': 'FKChange',
            'applicant_last_name': 'Person',
            'applicant_dob': date(1985, 6, 6),
            'applicant_email': 'fkchange@email.com',
            'applicant_phone': '+852-9166-6666',
            'applicant_gov_id': 'F180000(0)',
            'spouse_first_name': None,
            'spouse_last_name': None,
            'spouse_dob': None,
            'spouse_email': None,
            'spouse_phone': None,
            'spouse_gov_id': None,
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_30_cluster_merge():
    """
    SCD2-30: Cluster Merge (2 clusters → 1)
    
    T0 Setup:
      - Cluster A: Lead L301 (singleton - no quotes reference it)
      - Cluster B: Quote Q301 (lead_id=NULL) → QuoteMembers QM301, QM302
      - These are 2 separate clusters
    
    T1: Quote Q301 gets lead_id=L301
      → Creates FK relationship Q301→L301
      → Merges Cluster A (1 party) into Cluster B (3 parties)
    
    Expected:
      - Merged cluster keeps Cluster B's ID (larger cluster = 3 parties)
      - L301's old singleton cluster closed (rec_end_date set)
      - New cluster assignment for L301 with Cluster B's ID
    """
    return {
        'quotes': [{
            'quote_id': 'Q301',
            'lead_id': 'L301',  # ADDED FK (was NULL in T0) → triggers merge
            'quote_type': 'Individual',
            'contract_number': 'C301',
            'total_premium': 5000.00,
            'quote_date': date(2024, 6, 1),
            'status': 'Accepted',
            'created_date': date(2024, 6, 1),
            'source_system': 'SmartPlus'
        }]
    }


def scd2_31_cluster_split():
    """
    SCD2-31: Cluster Split (1 cluster → 2)
    
    T0 Setup:
      - One cluster: Lead L401 ← Quote Q401 (lead_id=L401) and Quote Q402 (lead_id=L401)
      - Cluster = {L401, Q401, Q402}
    
    T1: Quote Q402 gets lead_id=NULL (FK removed)
      → Breaks FK relationship Q402→L401
      → Cluster splits: {L401, Q401} and {Q402}
    
    Expected:
      - {L401, Q401} keeps original cluster ID (larger child = 2 parties)
      - {Q402} gets new cluster ID (singleton)
      - Old cluster assignments for all 3 parties closed
      - New assignments created
    """
    return {
        'quotes': [{
            'quote_id': 'Q402',
            'lead_id': None,  # REMOVED FK (was L401 in T0) → triggers split
            'quote_type': 'Individual',
            'contract_number': 'C402',
            'total_premium': 7000.00,
            'quote_date': date(2024, 7, 1),
            'status': 'Accepted',
            'created_date': date(2024, 7, 1),
            'source_system': 'SmartPlus'
        }]
    }


# ========================================================================
# CATEGORY 4: EDGE CASES & DATA QUALITY (6 scenarios)
# ========================================================================

def scd2_24_rapid_successive_changes():
    """
    SCD2-24: Rapid Successive Changes
    T1: Lead L024 email changed
    T2: Same lead phone changed (5 minutes later in real scenario)
    Expected: Two separate versions
    """
    t1_data = {
        'leads': [{
            'lead_id': 'L024',
            'first_name': 'Rapid',
            'last_name': 'Changes',
            'date_of_birth': date(1985, 8, 8),
            'email': 'rapid.new@email.com',  # CHANGED in T1
            'phone': '+852-9188-8888',
            'address': 'Test Address 24',
            'gov_id_type': 'HKID',
            'gov_id_number': 'R240000(0)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }
    
    t2_data = {
        'leads': [{
            'lead_id': 'L024',
            'first_name': 'Rapid',
            'last_name': 'Changes',
            'date_of_birth': date(1985, 8, 8),
            'email': 'rapid.new@email.com',  # Already changed in T1
            'phone': '+852-9199-9999',  # CHANGED in T2
            'address': 'Test Address 24',
            'gov_id_type': 'HKID',
            'gov_id_number': 'R240000(0)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }
    
    return t1_data, t2_data


def scd2_27_special_characters():
    """
    SCD2-27: Special Characters & Encoding
    T1: Update name with unicode characters
    Expected: Proper encoding preserved in both versions
    """
    return {
        'leads': [{
            'lead_id': 'L027',
            'first_name': '王小華',  # CHANGED from '王小明'
            'last_name': 'Unicode',
            'date_of_birth': date(1985, 11, 11),
            'email': 'unicode@email.com',
            'phone': '+852-9211-1111',
            'address': '香港中環皇后大道中123號',
            'gov_id_type': 'HKID',
            'gov_id_number': 'U270000(0)',
            'created_date': date(2024, 1, 25),
            'source_system': 'SmartPlus'
        }]
    }


# ========================================================================
# DELTA GENERATION FUNCTIONS
# ========================================================================

def generate_t1_delta():
    """
    Generate T1 delta data (new + changed rows only).
    Does NOT include unchanged rows from T0.
    
    Returns:
        dict: Data structure with deltas for each table
    """
    data = init_data_structure()
    
    # Category 1: SOURCE_PARTY changes
    data['leads'].extend(scd2_01_new_party_insert()['leads'])
    data['leads'].extend(scd2_02_party_soft_delete()['leads'])
    data['policies'].extend(scd2_03_party_reactivation()['policies'])
    
    # SCD2-07 T1 part
    t1_data, _ = scd2_07_multiple_changes_same_party()
    data['leads'].extend(t1_data['leads'])
    
    # SCD2-06 bulk insert
    data['policy_members'].extend(scd2_06_bulk_insert()['policy_members'])
    
    # Category 2: RAW_ATTRIBUTE changes
    data['leads'].extend(scd2_09_single_attribute_update()['leads'])
    data['applications'].extend(scd2_10_multi_attribute_update()['applications'])
    data['leads'].extend(scd2_11_null_to_value()['leads'])
    data['leads'].extend(scd2_12_value_to_null()['leads'])
    data['policy_members'].extend(scd2_13_attribute_correction()['policy_members'])
    data['applications'].extend(scd2_14_complex_object_changes()['applications'])
    
    # Category 3: RELATIONSHIP changes
    data['quotes'].extend(scd2_16_new_fk_relationship()['quotes'])
    data['quotes'].extend(scd2_17_fk_relationship_broken()['quotes'])
    data['applications'].extend(scd2_18_fk_relationship_changed()['applications'])
    
    # Category 3b: CLUSTER changes
    data['quotes'].extend(scd2_30_cluster_merge()['quotes'])
    data['quotes'].extend(scd2_31_cluster_split()['quotes'])
    
    # Category 4: Edge cases
    t1_data, _ = scd2_24_rapid_successive_changes()
    data['leads'].extend(t1_data['leads'])
    data['leads'].extend(scd2_27_special_characters()['leads'])
    
    return data


def generate_t2_delta():
    """
    Generate T2 delta data (additional new + changed rows).
    Does NOT include unchanged rows or T1 changes.
    
    Returns:
        dict: Data structure with deltas for each table
    """
    data = init_data_structure()
    
    # SCD2-07 T2 part (second change to L001)
    _, t2_data = scd2_07_multiple_changes_same_party()
    data['leads'].extend(t2_data['leads'])
    
    # SCD2-24 T2 part (second change to L024)
    _, t2_data = scd2_24_rapid_successive_changes()
    data['leads'].extend(t2_data['leads'])
    
    # Add a few new records in T2 for variety
    data['leads'].append({
        'lead_id': 'L200',
        'first_name': 'T2New',
        'last_name': 'Person',
        'date_of_birth': date(1992, 2, 2),
        'email': 't2new@test.com',
        'phone': '+852-9200-0000',
        'address': 'T2 Test Address',
        'gov_id_type': 'HKID',
        'gov_id_number': 'T200000(0)',
        'created_date': get_t2_timestamp().date(),
        'source_system': 'SmartPlus'
    })
    
    return data


def generate_t0_additions_for_testing():
    """
    Generate additional T0 baseline data for scenarios that reference existing records.
    These should be added to existing T0 data (sources/ folder).
    
    NOTE: This is for reference only - DO NOT overwrite existing sources/ data.
    The Bronze ingestion script should be run on current sources/ first to establish baseline.
    """
    data = init_data_structure()
    
    # Add baseline records that will be modified in T1/T2
    
    # For SCD2-09: Lead L009 (will update email in T1)
    data['leads'].append({
        'lead_id': 'L009',
        'first_name': 'Alice',
        'last_name': 'Chen',
        'date_of_birth': date(1988, 5, 10),
        'email': 'alice.old@email.com',  # Original email
        'phone': '+852-9123-4567',
        'address': 'Test Address 9',
        'gov_id_type': 'HKID',
        'gov_id_number': 'A900000(9)',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-11: Lead L011 (phone is NULL, will be added in T1)
    data['leads'].append({
        'lead_id': 'L011',
        'first_name': 'NullTest',
        'last_name': 'Person',
        'date_of_birth': date(1985, 1, 1),
        'email': 'nulltest@email.com',
        'phone': None,  # NULL initially
        'address': None,
        'gov_id_type': 'HKID',
        'gov_id_number': 'N110000(0)',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-12: Lead L012 (address will be removed in T1)
    data['leads'].append({
        'lead_id': 'L012',
        'first_name': 'RemoveAttr',
        'last_name': 'Person',
        'date_of_birth': date(1985, 2, 2),
        'email': 'removeattr@email.com',
        'phone': '+852-9122-2222',
        'address': 'Original Address 12',  # Will be removed
        'gov_id_type': 'HKID',
        'gov_id_number': 'R120000(0)',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-13: Policy member PM013 with typo
    data['policy_members'].append({
        'pm_id': 'PM013',
        'policy_id': 'P013',
        'contract_number': 'C013',
        'member_number': 1,
        'first_name': 'Jonh',  # Typo (will be corrected in T1)
        'last_name': 'Corrected',
        'date_of_birth': date(1990, 3, 3),
        'email': 'corrected@email.com',
        'phone': '+852-9133-3333',
        'gov_id_type': 'HKID',
        'gov_id_number': 'C130000(0)',
        'relationship_type': 'Primary',
        'gender': 'M',
        'coverage_start_date': date(2024, 1, 1),
        'coverage_end_date': None,
        'is_active': True,
        'created_date': date(2024, 1, 25),
        'source_system': 'Smile'
    })
    
    # For SCD2-16: Quote Q016 without lead_id
    data['quotes'].append({
        'quote_id': 'Q016',
        'lead_id': None,  # No FK initially
        'quote_type': 'Individual',
        'contract_number': 'C016',
        'total_premium': 6000.00,
        'quote_date': date(2024, 1, 20),
        'status': 'Accepted',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    # Lead L016 for the FK relationship
    data['leads'].append({
        'lead_id': 'L016',
        'first_name': 'FKTest',
        'last_name': 'Person',
        'date_of_birth': date(1985, 5, 5),
        'email': 'fktest@email.com',
        'phone': '+852-9155-5555',
        'address': 'Test Address 16',
        'gov_id_type': 'HKID',
        'gov_id_number': 'F160000(0)',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-30: Cluster merge - Lead L301 (singleton) and Quote Q301 with members
    data['leads'].append({
        'lead_id': 'L301',
        'first_name': 'MergeTarget',
        'last_name': 'Person',
        'date_of_birth': date(1990, 6, 1),
        'email': 'merge.target@email.com',
        'phone': '+852-9301-0001',
        'address': 'Merge Test Address 301',
        'gov_id_type': 'HKID',
        'gov_id_number': 'M301000(0)',
        'created_date': date(2024, 6, 1),
        'source_system': 'SmartPlus'
    })
    data['quotes'].append({
        'quote_id': 'Q301',
        'lead_id': None,  # No FK initially → separate cluster from L301
        'quote_type': 'Individual',
        'contract_number': 'C301',
        'total_premium': 5000.00,
        'quote_date': date(2024, 6, 1),
        'status': 'Accepted',
        'created_date': date(2024, 6, 1),
        'source_system': 'SmartPlus'
    })
    data['quote_members'].append({
        'qm_id': 'QM301',
        'quote_id': 'Q301',
        'member_sequence': 1,
        'first_name': 'MergeMember',
        'last_name': 'One',
        'date_of_birth': date(1990, 6, 1),
        'email': 'merge.member1@email.com',
        'phone': '+852-9301-0002',
        'gov_id_type': 'HKID',
        'gov_id_number': 'M301001(0)',
        'relationship_type': 'Primary',
        'gender': 'M',
        'created_date': date(2024, 6, 1),
        'source_system': 'SmartPlus'
    })
    data['quote_members'].append({
        'qm_id': 'QM302',
        'quote_id': 'Q301',
        'member_sequence': 2,
        'first_name': 'MergeMember',
        'last_name': 'Two',
        'date_of_birth': date(1992, 6, 1),
        'email': 'merge.member2@email.com',
        'phone': '+852-9301-0003',
        'gov_id_type': 'HKID',
        'gov_id_number': 'M301002(0)',
        'relationship_type': 'Spouse',
        'gender': 'F',
        'created_date': date(2024, 6, 1),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-31: Cluster split - Lead L401 with 2 quotes
    data['leads'].append({
        'lead_id': 'L401',
        'first_name': 'SplitSource',
        'last_name': 'Person',
        'date_of_birth': date(1988, 7, 1),
        'email': 'split.source@email.com',
        'phone': '+852-9401-0001',
        'address': 'Split Test Address 401',
        'gov_id_type': 'HKID',
        'gov_id_number': 'S401000(0)',
        'created_date': date(2024, 7, 1),
        'source_system': 'SmartPlus'
    })
    data['quotes'].append({
        'quote_id': 'Q401',
        'lead_id': 'L401',  # FK to L401 → stays connected after split
        'quote_type': 'Individual',
        'contract_number': 'C401',
        'total_premium': 6000.00,
        'quote_date': date(2024, 7, 1),
        'status': 'Accepted',
        'created_date': date(2024, 7, 1),
        'source_system': 'SmartPlus'
    })
    data['quotes'].append({
        'quote_id': 'Q402',
        'lead_id': 'L401',  # FK to L401 → will be removed in T1 to trigger split
        'quote_type': 'Individual',
        'contract_number': 'C402',
        'total_premium': 7000.00,
        'quote_date': date(2024, 7, 1),
        'status': 'Accepted',
        'created_date': date(2024, 7, 1),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-24: Lead L024 for rapid changes
    data['leads'].append({
        'lead_id': 'L024',
        'first_name': 'Rapid',
        'last_name': 'Changes',
        'date_of_birth': date(1985, 8, 8),
        'email': 'rapid.old@email.com',  # Original
        'phone': '+852-9188-8888',
        'address': 'Test Address 24',
        'gov_id_type': 'HKID',
        'gov_id_number': 'R240000(0)',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    # For SCD2-27: Unicode character test
    data['leads'].append({
        'lead_id': 'L027',
        'first_name': '王小明',  # Original unicode
        'last_name': 'Unicode',
        'date_of_birth': date(1985, 11, 11),
        'email': 'unicode@email.com',
        'phone': '+852-9211-1111',
        'address': '香港中環皇后大道中123號',
        'gov_id_type': 'HKID',
        'gov_id_number': 'U270000(0)',
        'created_date': date(2024, 1, 25),
        'source_system': 'SmartPlus'
    })
    
    return data


if __name__ == '__main__':
    print("SCD2 UAT Scenario Generator")
    print("This module defines scenario functions.")
    print("Use generate_uat_scd2_data.py to generate actual CSV files.")
