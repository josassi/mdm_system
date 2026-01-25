"""
Granularity Scenarios (S2.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_2_1_quote_level_link(data):
    """S2.1: Quote-level link (granularity loss)"""
    sid, cid = "S2.1", 'CLUSTER_003'
    
    data['quotes'].append({
        'quote_id': 'Q003', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C003', 'total_premium': 12000.00,
        'quote_date': date(2024, 3, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for seq, fname, dob in [(1, 'Alice', date(1988, 4, 12)), (2, 'Bob', date(1986, 8, 25))]:
        data['quote_members'].append({
            'qm_id': f'QM{4 + seq:03d}', 'quote_id': 'Q003', 'member_sequence': seq,
            'first_name': fname, 'last_name': 'Wong', 'date_of_birth': dob,
            'email': f'{fname.lower()}.wong@email.com', 'phone': '+852-9345-6789',
            'gov_id_type': 'HKID', 'gov_id_number': f'D{seq}23456(7)',
            'relationship_type': 'Primary' if seq == 1 else 'Spouse',
            'gender': 'F' if fname == 'Alice' else 'M',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
    
    data['applications'].append({
        'app_id': 'A003', 'quote_id': 'Q003',
        'application_date': date(2024, 3, 5), 'status': 'Approved',
        'contract_number': 'C003',
        'applicant_first_name': 'Alice', 'applicant_last_name': 'Wong',
        'applicant_dob': date(1988, 4, 15), 'applicant_email': 'alice.wong@email.com',
        'applicant_phone': '+852-9345-6789', 'applicant_gov_id': 'C123456(7)',
        'spouse_first_name': 'Bob', 'spouse_last_name': 'Wong',
        'spouse_dob': date(1986, 8, 22), 'spouse_email': 'bob.wong@email.com',
        'spouse_phone': '+852-9345-6789', 'spouse_gov_id': 'C234567(8)',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for t, p in [('smartplus_quote', 'Q003'), ('smartplus_quote_member', 'QM005'),
                 ('smartplus_quote_member', 'QM006'), ('smartplus_application', 'A003')]:
        add_cluster(data, sid, 'Quote Level Link', cid, t, p,
                   'App→Quote but not to specific member (keeping_granularity_when_used=FALSE)')
    
    # Single-party entities (no matching across systems)
    add_entity(data, sid, 'Quote Level Link', 'ENTITY_004',
              'Alice Wong - 1988-04-12', ['QM005'], 'Single quote member')
    add_entity(data, sid, 'Quote Level Link', 'ENTITY_005',
              'Bob Wong - 1986-08-25', ['QM006'], 'Single quote member')


def scenario_2_2_membership_number(data):
    """S2.2: Contract + member number preserves granularity"""
    sid, cid = "S2.2", 'CLUSTER_004'
    
    data['quotes'].append({
        'quote_id': 'Q004', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C004', 'total_premium': 10000.00,
        'quote_date': date(2024, 4, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P004', 'contract_number': 'C004', 'application_id': None,
        'policy_type': 'Family', 'start_date': date(2024, 5, 1), 'end_date': None,
        'status': 'Active', 'annual_premium': 10000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    for seq, fname, dob, gov in [(1, 'Michael', date(1975, 9, 8), 'E123456(7)'),
                                   (2, 'Linda', date(1977, 12, 3), 'E234567(8)')]:
        qm, pm = f'QM{6 + seq:03d}', f'PM{4 + seq:03d}'
        
        data['quote_members'].append({
            'qm_id': qm, 'quote_id': 'Q004', 'member_sequence': seq,
            'first_name': fname, 'last_name': 'Chen', 'date_of_birth': dob,
            'email': f'{fname.lower()}.chen@email.com', 'phone': '+852-9456-7890',
            'gov_id_type': 'HKID', 'gov_id_number': gov,
            'relationship_type': 'Primary' if seq == 1 else 'Spouse',
            'gender': 'M' if fname == 'Michael' else 'F',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
        
        data['policy_members'].append({
            'pm_id': pm, 'policy_id': 'P004', 'contract_number': 'C004',
            'member_number': seq, 'first_name': fname, 'last_name': 'Chen',
            'date_of_birth': dob, 'email': f'{fname.lower()}.chen@email.com',
            'phone': '+852-9456-7890', 'gov_id_type': 'HKID', 'gov_id_number': gov,
            'relationship_type': 'Primary' if seq == 1 else 'Spouse',
            'gender': 'M' if fname == 'Michael' else 'F',
            'coverage_start_date': date(2024, 5, 1), 'coverage_end_date': None,
            'is_active': True, 'created_date': now(), 'source_system': 'Smile'
        })
        
        add_match(data, sid, qm, pm, True,
                 'Contract+Member number (guarantees_same_party=TRUE)', 1.0)
        add_entity(data, sid, 'Membership Number Granularity', f'ENTITY_{6 + seq:03d}',
                  f'{fname} Chen - {dob}', [qm, pm], 
                  'Guaranteed match via composite key')
        add_cluster(data, sid, 'Membership Number Granularity', cid,
                   'smartplus_quote_member', qm)
        add_cluster(data, sid, 'Membership Number Granularity', cid,
                   'smile_policy_member', pm)
    
    add_cluster(data, sid, 'Membership Number Granularity', cid, 'smartplus_quote', 'Q004')
    add_cluster(data, sid, 'Membership Number Granularity', cid, 'smile_policy', 'P004')
