"""
Edge Cases and Data Quality Issues (S8.x, S9.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_8_1_missing_pii(data):
    """S8.1: Missing PII"""
    sid, cid = "S8.1", 'CLUSTER_012'
    
    data['quotes'].append({
        'quote_id': 'Q011', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C012', 'total_premium': 5000.00,
        'quote_date': date(2024, 11, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM015', 'quote_id': 'Q011', 'member_sequence': 1,
        'first_name': None, 'last_name': None, 'date_of_birth': None,
        'email': None, 'phone': None, 'gov_id_type': None, 'gov_id_number': None,
        'relationship_type': 'Primary', 'gender': None,
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P011', 'contract_number': 'C012', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2024, 12, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 5000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM013', 'policy_id': 'P011', 'contract_number': 'C012',
        'member_number': 1, 'first_name': 'Unknown', 'last_name': 'Unknown',
        'date_of_birth': None, 'email': None, 'phone': None,
        'gov_id_type': None, 'gov_id_number': None,
        'relationship_type': 'Primary', 'gender': None,
        'coverage_start_date': date(2024, 12, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q011'), ('smartplus_quote_member', 'QM015'),
                 ('smile_policy', 'P011'), ('smile_policy_member', 'PM013')]:
        add_cluster(data, sid, 'Missing PII', cid, t, p,
                   'Business link exists but no PII')
    
    add_match(data, sid, 'QM015', 'PM013', False,
             'NEGATIVE: No PII for matching', 0.0)
    
    # Single-party entities (cannot match due to missing PII)
    add_entity(data, sid, 'Missing PII', 'ENTITY_012A',
              'Unknown Person - Quote', ['QM015'], 'No PII - quote member')
    add_entity(data, sid, 'Missing PII', 'ENTITY_012B',
              'Unknown Person - Policy', ['PM013'], 'No PII - policy member')


def scenario_8_2_duplicate_members(data):
    """S8.2: Duplicate members"""
    sid, cid = "S8.2", 'CLUSTER_013'
    
    data['quotes'].append({
        'quote_id': 'Q012', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C013', 'total_premium': 9000.00,
        'quote_date': date(2024, 12, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Duplicates
    for i, qm_id in enumerate(['QM016', 'QM017']):
        data['quote_members'].append({
            'qm_id': qm_id, 'quote_id': 'Q012', 'member_sequence': i+1,
            'first_name': 'Peter', 'last_name': 'Johnson',
            'date_of_birth': date(1975, 9, 14), 'email': 'peter.johnson@email.com',
            'phone': '+852-9234-5678', 'gov_id_type': 'HKID', 'gov_id_number': 'M123456(7)',
            'relationship_type': 'Primary', 'gender': 'M',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
    
    data['policies'].append({
        'policy_id': 'P012', 'contract_number': 'C013', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2025, 1, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 9000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM014', 'policy_id': 'P012', 'contract_number': 'C013',
        'member_number': 1, 'first_name': 'Peter', 'last_name': 'Johnson',
        'date_of_birth': date(1975, 9, 14), 'email': 'peter.johnson@email.com',
        'phone': '+852-9234-5678', 'gov_id_type': 'HKID', 'gov_id_number': 'M123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2025, 1, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q012'), ('smartplus_quote_member', 'QM016'),
                 ('smartplus_quote_member', 'QM017'), ('smile_policy', 'P012'),
                 ('smile_policy_member', 'PM014')]:
        add_cluster(data, sid, 'Duplicate Members', cid, t, p)
    
    add_match(data, sid, 'QM016', 'QM017', True, 'Duplicate detection', 0.95)
    add_match(data, sid, 'QM016', 'PM014', True, 'Cross-system', 0.95)
    add_match(data, sid, 'QM017', 'PM014', True, 'Cross-system (dup)', 0.95)
    
    add_entity(data, sid, 'Duplicate Members', 'ENTITY_013',
              'Peter Johnson - 1975-09-14', ['QM016', 'QM017', 'PM014'],
              'All 3 merge into one entity')


def scenario_8_3_invalid_fk(data):
    """S8.3: Invalid FK"""
    sid, cid = "S8.3", 'CLUSTER_014'
    
    data['applications'].append({
        'app_id': 'A006', 'quote_id': None,
        'application_date': date(2025, 1, 1), 'status': 'Approved',
        'contract_number': 'C014',
        'applicant_first_name': 'Unknown', 'applicant_last_name': 'Person',
        'applicant_dob': None, 'applicant_email': None,
        'applicant_phone': None, 'applicant_gov_id': None,
        'spouse_first_name': None, 'spouse_last_name': None,
        'spouse_dob': None, 'spouse_email': None,
        'spouse_phone': None, 'spouse_gov_id': None,
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P013', 'contract_number': 'C014', 'application_id': 'A006',
        'policy_type': 'Individual', 'start_date': date(2025, 2, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 4000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM015', 'policy_id': 'P013', 'contract_number': 'C014',
        'member_number': 1, 'first_name': 'Nancy', 'last_name': 'White',
        'date_of_birth': date(1995, 4, 8), 'email': 'nancy.white@email.com',
        'phone': '+852-9345-6789', 'gov_id_type': 'HKID', 'gov_id_number': 'N123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2025, 2, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_application', 'A006'), ('smile_policy', 'P013'),
                 ('smile_policy_member', 'PM015')]:
        add_cluster(data, sid, 'Invalid FK', cid, t, p, 'NULL quote_id')
    
    add_entity(data, sid, 'Invalid FK', 'ENTITY_014',
              'Nancy White - 1995-04-08', ['PM015'], 'Policy member with NULL quote_id in application')


def scenario_9_1_large_family(data):
    """S9.1: Large family (12 members)"""
    sid, cid = "S9.1", 'CLUSTER_015'
    
    data['quotes'].append({
        'quote_id': 'Q013', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C015', 'total_premium': 50000.00,
        'quote_date': date(2025, 2, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P014', 'contract_number': 'C015', 'application_id': None,
        'policy_type': 'Family', 'start_date': date(2025, 3, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 50000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    rels = ['Primary', 'Spouse'] + ['Child'] * 10
    for i in range(12):
        qm_id, pm_id = f'QM{18 + i:03d}', f'PM{16 + i:03d}'
        
        data['quote_members'].append({
            'qm_id': qm_id, 'quote_id': 'Q013', 'member_sequence': i+1,
            'first_name': f'Member{i+1}', 'last_name': 'LargeFamily',
            'date_of_birth': date(1980 - i*5, 1, 1),
            'email': f'member{i+1}@largefamily.com', 'phone': '+852-9000-0000',
            'gov_id_type': 'HKID', 'gov_id_number': f'O{i+1:02d}3456(7)',
            'relationship_type': rels[i], 'gender': 'M' if i % 2 == 0 else 'F',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
        
        data['policy_members'].append({
            'pm_id': pm_id, 'policy_id': 'P014', 'contract_number': 'C015',
            'member_number': i+1, 'first_name': f'Member{i+1}',
            'last_name': 'LargeFamily', 'date_of_birth': date(1980 - i*5, 1, 1),
            'email': f'member{i+1}@largefamily.com', 'phone': '+852-9000-0000',
            'gov_id_type': 'HKID', 'gov_id_number': f'O{i+1:02d}3456(7)',
            'relationship_type': rels[i], 'gender': 'M' if i % 2 == 0 else 'F',
            'coverage_start_date': date(2025, 3, 1), 'coverage_end_date': None,
            'is_active': True, 'created_date': now(), 'source_system': 'Smile'
        })
        
        add_match(data, sid, qm_id, pm_id, True, f'Member {i+1} match', 0.95)
        add_entity(data, sid, 'Large Family', f'ENTITY_{15:03d}_{i+1}',
                  f'Member{i+1} LargeFamily - {date(1980 - i*5, 1, 1)}', [qm_id, pm_id],
                  f'Family member {i+1}')
        add_cluster(data, sid, 'Large Family', cid, 'smartplus_quote_member', qm_id)
        add_cluster(data, sid, 'Large Family', cid, 'smile_policy_member', pm_id)
    
    add_cluster(data, sid, 'Large Family', cid, 'smartplus_quote', 'Q013')
    add_cluster(data, sid, 'Large Family', cid, 'smile_policy', 'P014')


def scenario_9_3_special_characters(data):
    """S9.3: Special characters in names"""
    sid = "S9.3"
    
    special = [
        ('QM030', 'Q014', "O'Brien-Smith", "John", date(1985, 1, 1), 'P123456(7)', 
         'P015', 'PM028', 'C016', 'CLUSTER_016'),
        ('QM031', 'Q015', "García", "José", date(1990, 2, 2), 'Q123456(7)',
         'P016', 'PM029', 'C017', 'CLUSTER_017'),
        ('QM032', 'Q016', "李", "明", date(1988, 3, 3), 'R123456(7)',
         'P017', 'PM030', 'C018', 'CLUSTER_018'),
        ('QM033', 'Q017', "Müller", "Hans", date(1992, 4, 4), 'S123456(7)',
         'P018', 'PM031', 'C019', 'CLUSTER_019')
    ]
    
    for qm, qid, last, first, dob, gov, pid, pm, contract, cluster in special:
        data['quotes'].append({
            'quote_id': qid, 'lead_id': None, 'quote_type': 'Individual',
            'contract_number': contract, 'total_premium': 6000.00,
            'quote_date': date(2025, 3, 1), 'status': 'Accepted',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
        
        data['quote_members'].append({
            'qm_id': qm, 'quote_id': qid, 'member_sequence': 1,
            'first_name': first, 'last_name': last, 'date_of_birth': dob,
            'email': f'{first.lower()}.{last.lower()}@email.com'.replace("'", ""),
            'phone': '+852-9111-1111', 'gov_id_type': 'HKID', 'gov_id_number': gov,
            'relationship_type': 'Primary', 'gender': 'M',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
        
        data['policies'].append({
            'policy_id': pid, 'contract_number': contract, 'application_id': None,
            'policy_type': 'Individual', 'start_date': date(2025, 4, 1),
            'end_date': None, 'status': 'Active', 'annual_premium': 6000.00,
            'created_date': now(), 'source_system': 'Smile'
        })
        
        data['policy_members'].append({
            'pm_id': pm, 'policy_id': pid, 'contract_number': contract,
            'member_number': 1, 'first_name': first, 'last_name': last,
            'date_of_birth': dob, 
            'email': f'{first.lower()}.{last.lower()}@email.com'.replace("'", ""),
            'phone': '+852-9111-1111', 'gov_id_type': 'HKID', 'gov_id_number': gov,
            'relationship_type': 'Primary', 'gender': 'M',
            'coverage_start_date': date(2025, 4, 1), 'coverage_end_date': None,
            'is_active': True, 'created_date': now(), 'source_system': 'Smile'
        })
        
        for t, p in [('smartplus_quote', qid), ('smartplus_quote_member', qm),
                     ('smile_policy', pid), ('smile_policy_member', pm)]:
            add_cluster(data, sid, 'Special Characters', cluster, t, p)
        
        add_match(data, sid, qm, pm, True, f'Unicode: {first} {last}', 0.95)
        add_entity(data, sid, 'Special Characters', f'ENTITY_{cluster.split("_")[1]}',
                  f'{first} {last} - {dob}', [qm, pm],
                  f'Unicode name: {first} {last}')
