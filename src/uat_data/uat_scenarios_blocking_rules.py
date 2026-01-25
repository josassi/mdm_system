"""
Blocking Rules & Conflict Detection Scenarios (S12.x)
Tests edge cases for Silver/Gold layer matching decisions
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_12_1_conflicting_hkids(data):
    """S12.1: Conflicting HKIDs - Blocking rule test"""
    sid = "S12.1"
    
    # Quote and Policy with nearly identical PII but DIFFERENT HKIDs
    data['quotes'].append({
        'quote_id': 'Q024', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C025', 'total_premium': 8000.00,
        'quote_date': date(2025, 9, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM045', 'quote_id': 'Q024', 'member_sequence': 1,
        'first_name': 'Michael', 'last_name': 'Chan',
        'date_of_birth': date(1985, 4, 15), 'email': 'michael.chan@email.com',
        'phone': '+852-9111-1111', 'gov_id_type': 'HKID', 'gov_id_number': 'C123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P023', 'contract_number': 'C025', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2025, 10, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 8000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM037', 'policy_id': 'P023', 'contract_number': 'C025',
        'member_number': 1, 'first_name': 'Michael', 'last_name': 'Chan',
        'date_of_birth': date(1985, 4, 15), 'email': 'michael.chan@email.com',
        'phone': '+852-9111-1111', 'gov_id_type': 'HKID', 'gov_id_number': 'C999999(9)',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2025, 10, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    # Same cluster (business link)
    add_cluster(data, sid, 'HKID Conflict', 'CLUSTER_026',
               'smartplus_quote', 'Q024', 'Conflicting HKID test')
    add_cluster(data, sid, 'HKID Conflict', 'CLUSTER_026',
               'smartplus_quote_member', 'QM045')
    add_cluster(data, sid, 'HKID Conflict', 'CLUSTER_026',
               'smile_policy', 'P023')
    add_cluster(data, sid, 'HKID Conflict', 'CLUSTER_026',
               'smile_policy_member', 'PM037')
    
    # NEGATIVE match - blocking rule should prevent linking
    add_match(data, sid, 'QM045', 'PM037', False,
             'BLOCKING: Different HKIDs (C123456(7) vs C999999(9)) - same name/DOB/email suggests data error',
             0.0)
    
    # Separate entities despite same cluster
    add_entity(data, sid, 'HKID Conflict', 'ENTITY_027A',
              'Michael Chan - 1985-04-15 - HKID:C123456(7)', ['QM045'],
              'Quote member - potential data quality issue')
    add_entity(data, sid, 'HKID Conflict', 'ENTITY_027B',
              'Michael Chan - 1985-04-15 - HKID:C999999(9)', ['PM037'],
              'Policy member - potential data quality issue')


def scenario_12_2_name_change_over_time(data):
    """S12.2: Name change (maiden name) - Should match via stable identifiers"""
    sid, cid = "S12.2", 'CLUSTER_027'
    
    # Old quote with maiden name
    data['quotes'].append({
        'quote_id': 'Q025', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C026', 'total_premium': 6000.00,
        'quote_date': date(2020, 1, 15), 'status': 'Declined',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM046', 'quote_id': 'Q025', 'member_sequence': 1,
        'first_name': 'Emily', 'last_name': 'Thompson',
        'date_of_birth': date(1990, 8, 22), 'email': 'emily.t@email.com',
        'phone': '+852-9222-2222', 'gov_id_type': 'HKID', 'gov_id_number': 'D123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # New policy with married name
    data['policies'].append({
        'policy_id': 'P024', 'contract_number': 'C027', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2024, 6, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 7000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM038', 'policy_id': 'P024', 'contract_number': 'C027',
        'member_number': 1, 'first_name': 'Emily', 'last_name': 'Chen',
        'date_of_birth': date(1990, 8, 22), 'email': 'emily.t@email.com',
        'phone': '+852-9222-2222', 'gov_id_type': 'HKID', 'gov_id_number': 'D123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2024, 6, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q025'), ('smartplus_quote_member', 'QM046'),
                 ('smile_policy', 'P024'), ('smile_policy_member', 'PM038')]:
        add_cluster(data, sid, 'Name Change', cid, t, p,
                   'Different last name but same HKID/DOB/email')
    
    # Should match despite name change - stable identifiers (HKID, DOB, email)
    add_match(data, sid, 'QM046', 'PM038', True,
             'Name change detected: Thompson→Chen, but exact HKID/DOB/email match (marriage)',
             0.90)
    
    add_entity(data, sid, 'Name Change', 'ENTITY_028',
              'Emily Thompson/Chen - 1990-08-22', ['QM046', 'PM038'],
              'Name change over time - matched via stable identifiers')


def scenario_12_3_gender_conflict(data):
    """S12.3: Gender conflict - Blocking rule test"""
    sid = "S12.3"
    
    # Two separate quotes with same name/DOB but different gender
    data['quotes'].append({
        'quote_id': 'Q026', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': None, 'total_premium': 5000.00,
        'quote_date': date(2025, 10, 1), 'status': 'Declined',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM047', 'quote_id': 'Q026', 'member_sequence': 1,
        'first_name': 'Alex', 'last_name': 'Morgan',
        'date_of_birth': date(1988, 3, 10), 'email': 'alex.morgan@email.com',
        'phone': '+852-9333-3333', 'gov_id_type': 'Passport', 'gov_id_number': 'P1234567',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quotes'].append({
        'quote_id': 'Q027', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C028', 'total_premium': 5500.00,
        'quote_date': date(2025, 11, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM048', 'quote_id': 'Q027', 'member_sequence': 1,
        'first_name': 'Alex', 'last_name': 'Morgan',
        'date_of_birth': date(1988, 3, 10), 'email': 'alex.morgan@email.com',
        'phone': '+852-9333-3333', 'gov_id_type': 'Passport', 'gov_id_number': 'P1234567',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Two separate clusters (no business link)
    add_cluster(data, sid, 'Gender Conflict', 'CLUSTER_028A',
               'smartplus_quote', 'Q026', 'Gender=M')
    add_cluster(data, sid, 'Gender Conflict', 'CLUSTER_028A',
               'smartplus_quote_member', 'QM047')
    
    add_cluster(data, sid, 'Gender Conflict', 'CLUSTER_028B',
               'smartplus_quote', 'Q027', 'Gender=F')
    add_cluster(data, sid, 'Gender Conflict', 'CLUSTER_028B',
               'smartplus_quote_member', 'QM048')
    
    # NEGATIVE match - gender conflict should block or flag for review
    add_match(data, sid, 'QM047', 'QM048', False,
             'BLOCKING: Gender conflict (M vs F) - likely data entry error or different persons',
             0.0)
    
    # Separate entities
    add_entity(data, sid, 'Gender Conflict', 'ENTITY_029A',
              'Alex Morgan - 1988-03-10 - Male', ['QM047'],
              'Gender=M - potential data error')
    add_entity(data, sid, 'Gender Conflict', 'ENTITY_029B',
              'Alex Morgan - 1988-03-10 - Female', ['QM048'],
              'Gender=F - potential data error')


def scenario_12_4_multiple_id_types(data):
    """S12.4: Multiple ID types - Person with both HKID and Passport"""
    sid, cid = "S12.4", 'CLUSTER_029'
    
    # Quote with HKID
    data['quotes'].append({
        'quote_id': 'Q028', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C029', 'total_premium': 9000.00,
        'quote_date': date(2025, 11, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM049', 'quote_id': 'Q028', 'member_sequence': 1,
        'first_name': 'Kevin', 'last_name': 'Leung',
        'date_of_birth': date(1983, 12, 5), 'email': 'kevin.leung@email.com',
        'phone': '+852-9444-4444', 'gov_id_type': 'HKID', 'gov_id_number': 'E123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Policy with Passport (same person, different ID type)
    data['policies'].append({
        'policy_id': 'P025', 'contract_number': 'C029', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2025, 12, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 9000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM039', 'policy_id': 'P025', 'contract_number': 'C029',
        'member_number': 1, 'first_name': 'Kevin', 'last_name': 'Leung',
        'date_of_birth': date(1983, 12, 5), 'email': 'kevin.leung@email.com',
        'phone': '+852-9444-4444', 'gov_id_type': 'Passport', 'gov_id_number': 'K9876543',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2025, 12, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q028'), ('smartplus_quote_member', 'QM049'),
                 ('smile_policy', 'P025'), ('smile_policy_member', 'PM039')]:
        add_cluster(data, sid, 'Multiple ID Types', cid, t, p,
                   'HKID vs Passport for same person')
    
    # Should match - different ID types are allowed, match via name/DOB/email
    add_match(data, sid, 'QM049', 'PM039', True,
             'Different ID types (HKID vs Passport) but exact name/DOB/email/phone match',
             0.85)
    
    add_entity(data, sid, 'Multiple ID Types', 'ENTITY_030',
              'Kevin Leung - 1983-12-05', ['QM049', 'PM039'],
              'Same person with multiple ID types (HKID + Passport)')


def scenario_12_5_typo_in_critical_field(data):
    """S12.5: Typo in DOB - Near match that should be flagged for review"""
    sid, cid = "S12.5", 'CLUSTER_030'
    
    # Quote with correct DOB
    data['quotes'].append({
        'quote_id': 'Q029', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C030', 'total_premium': 7500.00,
        'quote_date': date(2025, 12, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM050', 'quote_id': 'Q029', 'member_sequence': 1,
        'first_name': 'Rachel', 'last_name': 'Wong',
        'date_of_birth': date(1992, 7, 15), 'email': 'rachel.wong@email.com',
        'phone': '+852-9555-5555', 'gov_id_type': 'HKID', 'gov_id_number': 'F123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Policy with typo in DOB (day off by 1)
    data['policies'].append({
        'policy_id': 'P026', 'contract_number': 'C030', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2026, 1, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 7500.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM040', 'policy_id': 'P026', 'contract_number': 'C030',
        'member_number': 1, 'first_name': 'Rachel', 'last_name': 'Wong',
        'date_of_birth': date(1992, 7, 16), 'email': 'rachel.wong@email.com',
        'phone': '+852-9555-5555', 'gov_id_type': 'HKID', 'gov_id_number': 'F123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2026, 1, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q029'), ('smartplus_quote_member', 'QM050'),
                 ('smile_policy', 'P026'), ('smile_policy_member', 'PM040')]:
        add_cluster(data, sid, 'DOB Typo', cid, t, p,
                   'DOB off by 1 day - likely typo')
    
    # Should match with flag for review - exact HKID but DOB differs by 1 day
    add_match(data, sid, 'QM050', 'PM040', True,
             'DOB typo suspected: 1992-07-15 vs 1992-07-16, but exact HKID/name/email - needs review',
             0.75)
    
    add_entity(data, sid, 'DOB Typo', 'ENTITY_031',
              'Rachel Wong - 1992-07-15/16', ['QM050', 'PM040'],
              'Likely same person with DOB data entry error')
