"""
PII Matching Scenarios (S4.x, S5.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_4_1_same_person_no_link(data):
    """S4.1: Same person, NO business link - NEGATIVE TEST"""
    sid = "S4.1"
    
    data['quotes'].append({
        'quote_id': 'Q005', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': None, 'total_premium': 5500.00,
        'quote_date': date(2024, 6, 1), 'status': 'Declined',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM009', 'quote_id': 'Q005', 'member_sequence': 1,
        'first_name': 'James', 'last_name': 'Wilson',
        'date_of_birth': date(1985, 3, 15), 'email': 'james.w@email.com',
        'phone': '+852-9789-0123', 'gov_id_type': 'HKID', 'gov_id_number': 'H123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P007', 'contract_number': 'C007', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2024, 6, 15),
        'end_date': None, 'status': 'Active', 'annual_premium': 5500.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM009', 'policy_id': 'P007', 'contract_number': 'C007',
        'member_number': 1, 'first_name': 'James', 'last_name': 'Wilson',
        'date_of_birth': date(1985, 3, 15), 'email': 'james.w@email.com',
        'phone': '+852-9789-0123', 'gov_id_type': 'HKID', 'gov_id_number': 'H123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2024, 6, 15), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    # Two separate clusters
    add_cluster(data, sid, 'Same Person No Link', 'CLUSTER_007A',
               'smartplus_quote', 'Q005', 'Declined quote cluster')
    add_cluster(data, sid, 'Same Person No Link', 'CLUSTER_007A',
               'smartplus_quote_member', 'QM009')
    add_cluster(data, sid, 'Same Person No Link', 'CLUSTER_007B',
               'smile_policy', 'P007', 'Separate policy cluster')
    add_cluster(data, sid, 'Same Person No Link', 'CLUSTER_007B',
               'smile_policy_member', 'PM009')
    
    # Should NOT match
    add_match(data, sid, 'QM009', 'PM009', False,
             'NEGATIVE: Same PII but different clusters - NO match', 0.0)
    
    # Single-party entities (negative test - should NOT merge)
    add_entity(data, sid, 'Same Person No Link', 'ENTITY_008A',
              'James Wilson - 1985-03-15', ['QM009'], 'Declined quote - single party')
    add_entity(data, sid, 'Same Person No Link', 'ENTITY_008B',
              'James Wilson - 1985-03-15', ['PM009'], 'Active policy - single party')


def scenario_4_2_same_name_different(data):
    """S4.2: Same name, different person"""
    sid, cid = "S4.2", 'CLUSTER_008'
    
    data['quotes'].append({
        'quote_id': 'Q006', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C008', 'total_premium': 18000.00,
        'quote_date': date(2024, 7, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for seq, suffix, dob in [(1, 'Sr', date(1960, 5, 20)), (2, 'Jr', date(1990, 5, 20))]:
        data['quote_members'].append({
            'qm_id': f'QM{9 + seq:03d}', 'quote_id': 'Q006', 'member_sequence': seq,
            'first_name': f'John {suffix}', 'last_name': 'Smith',
            'date_of_birth': dob, 'email': f'john.smith.{suffix.lower()}@email.com',
            'phone': '+852-9890-1234', 'gov_id_type': 'HKID',
            'gov_id_number': f'I{seq}23456(7)',
            'relationship_type': 'Primary' if seq == 1 else 'Child',
            'gender': 'M', 'created_date': now(), 'source_system': 'SmartPlus'
        })
        add_cluster(data, sid, 'Same Name Different Person', cid,
                   'smartplus_quote_member', f'QM{9 + seq:03d}')
    
    add_cluster(data, sid, 'Same Name Different Person', cid, 'smartplus_quote', 'Q006')
    add_match(data, sid, 'QM010', 'QM011', False,
             'NEGATIVE: Same name but 30-year DOB gap', 0.0)
    
    # Single-party entities (different persons)
    add_entity(data, sid, 'Same Name Different Person', 'ENTITY_009A',
              'John Sr Smith - 1960-05-20', ['QM010'], 'Father')
    add_entity(data, sid, 'Same Name Different Person', 'ENTITY_009B',
              'John Jr Smith - 1990-05-20', ['QM011'], 'Son')


def scenario_5_1_name_variations(data):
    """S5.1: Name variations"""
    sid, cid = "S5.1", 'CLUSTER_009'
    
    data['quotes'].append({
        'quote_id': 'Q007', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C009', 'total_premium': 7000.00,
        'quote_date': date(2024, 8, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM012', 'quote_id': 'Q007', 'member_sequence': 1,
        'first_name': 'Catherine', 'last_name': 'Smith',
        'date_of_birth': date(1978, 11, 10), 'email': 'catherine.smith@email.com',
        'phone': '+852-9901-2345', 'gov_id_type': 'HKID', 'gov_id_number': 'J123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P008', 'contract_number': 'C009', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2024, 9, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 7000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM010', 'policy_id': 'P008', 'contract_number': 'C009',
        'member_number': 1, 'first_name': 'Cathy', 'last_name': 'Smith',
        'date_of_birth': date(1978, 11, 10), 'email': 'catherine.smith@email.com',
        'phone': '+852-9901-2345', 'gov_id_type': 'HKID', 'gov_id_number': 'J123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2024, 9, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q007'), ('smartplus_quote_member', 'QM012'),
                 ('smile_policy', 'P008'), ('smile_policy_member', 'PM010')]:
        add_cluster(data, sid, 'Name Variations', cid, t, p)
    
    add_match(data, sid, 'QM012', 'PM010', True,
             'Catherine vs Cathy - fuzzy name but exact HKID', 0.95)
    add_entity(data, sid, 'Name Variations', 'ENTITY_009',
              'Catherine Smith - 1978-11-10', ['QM012', 'PM010'],
              'Fuzzy name matching - Catherine/Cathy')


def scenario_5_2_name_transposition(data):
    """S5.2: Name transposition"""
    sid, cid = "S5.2", 'CLUSTER_010'
    
    data['quotes'].append({
        'quote_id': 'Q008', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C010', 'total_premium': 6500.00,
        'quote_date': date(2024, 9, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM013', 'quote_id': 'Q008', 'member_sequence': 1,
        'first_name': 'Wei', 'last_name': 'Zhang',
        'date_of_birth': date(1982, 7, 25), 'email': 'wei.zhang@email.com',
        'phone': '+852-9012-3456', 'gov_id_type': 'HKID', 'gov_id_number': 'K123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P009', 'contract_number': 'C010', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2024, 10, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 6500.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM011', 'policy_id': 'P009', 'contract_number': 'C010',
        'member_number': 1, 'first_name': 'Zhang', 'last_name': 'Wei',
        'date_of_birth': date(1982, 7, 25), 'email': 'wei.zhang@email.com',
        'phone': '+852-9012-3456', 'gov_id_type': 'HKID', 'gov_id_number': 'K123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2024, 10, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q008'), ('smartplus_quote_member', 'QM013'),
                 ('smile_policy', 'P009'), ('smile_policy_member', 'PM011')]:
        add_cluster(data, sid, 'Name Transposition', cid, t, p)
    
    add_match(data, sid, 'QM013', 'PM011', True,
             'Wei Zhang vs Zhang Wei - transposed but exact HKID', 0.90)
    add_entity(data, sid, 'Name Transposition', 'ENTITY_010',
              'Wei Zhang - 1982-07-25', ['QM013', 'PM011'],
              'Name transposition match')
