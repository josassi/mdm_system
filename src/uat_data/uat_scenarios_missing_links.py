"""
Missing Links and Orphaned Records (S3.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, now


def scenario_3_1_orphaned_policy(data):
    """S3.1: Orphaned policy"""
    sid, cid = "S3.1", 'CLUSTER_005'
    
    data['policies'].append({
        'policy_id': 'P005', 'contract_number': 'C005', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2020, 1, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 6000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM007', 'policy_id': 'P005', 'contract_number': 'C005',
        'member_number': 1, 'first_name': 'Robert', 'last_name': 'Taylor',
        'date_of_birth': date(1970, 5, 22), 'email': 'robert.taylor@email.com',
        'phone': '+852-9567-8901', 'gov_id_type': 'HKID', 'gov_id_number': 'F123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2020, 1, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smile_policy', 'P005'), ('smile_policy_member', 'PM007')]:
        add_cluster(data, sid, 'Orphaned Policy', cid, t, p, 'Legacy policy, no SmartPlus records')
    
    add_entity(data, sid, 'Orphaned Policy', 'ENTITY_006',
              'Robert Taylor - 1970-05-22', ['PM007'], 'Orphaned policy member')


def scenario_3_2_broken_link(data):
    """S3.2: Broken FK link"""
    sid, cid = "S3.2", 'CLUSTER_006'
    
    data['applications'].append({
        'app_id': 'A004', 'quote_id': 'Q999',
        'application_date': date(2024, 5, 1), 'status': 'Approved',
        'contract_number': 'C006',
        'applicant_first_name': 'Grace', 'applicant_last_name': 'Park',
        'applicant_dob': date(1990, 9, 25), 'applicant_email': 'grace.park@email.com',
        'applicant_phone': '+852-9456-7890', 'applicant_gov_id': 'D123456(7)',
        'spouse_first_name': None, 'spouse_last_name': None,
        'spouse_dob': None, 'spouse_email': None,
        'spouse_phone': None, 'spouse_gov_id': None,
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P006', 'contract_number': 'C006', 'application_id': 'A004',
        'policy_type': 'Individual', 'start_date': date(2024, 6, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 4500.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM008', 'policy_id': 'P006', 'contract_number': 'C006',
        'member_number': 1, 'first_name': 'Grace', 'last_name': 'Park',
        'date_of_birth': date(1992, 8, 14), 'email': 'grace.park@email.com',
        'phone': '+852-9678-9012', 'gov_id_type': 'HKID', 'gov_id_number': 'G123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2024, 6, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_application', 'A004'), ('smile_policy', 'P006'),
                 ('smile_policy_member', 'PM008')]:
        add_cluster(data, sid, 'Broken Link', cid, t, p, 'App references non-existent Q999')
    
    add_entity(data, sid, 'Broken Link', 'ENTITY_007_BROKEN',
              'Grace Park - 1992-08-14', ['PM008'], 'Policy member with broken upstream link')
