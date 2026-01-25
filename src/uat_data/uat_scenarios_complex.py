"""
Complex Multi-System Scenarios (S7.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_7_1_multi_touch(data):
    """S7.1: Multi-touch journey"""
    sid, cid = "S7.1", 'CLUSTER_011'
    
    data['leads'].append({
        'lead_id': 'L003', 'first_name': 'Susan', 'last_name': 'Martinez',
        'date_of_birth': date(1987, 2, 18), 'email': 'susan.martinez@email.com',
        'phone': '+852-9123-4567', 'address': 'Flat 8C, 789 Hennessy Road, Wan Chai, HK',
        'gov_id_type': 'HKID', 'gov_id_number': 'L123456(7)',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Declined quote
    data['quotes'].append({
        'quote_id': 'Q009', 'lead_id': 'L003', 'quote_type': 'Individual',
        'contract_number': None, 'total_premium': 8000.00,
        'quote_date': date(2024, 10, 1), 'status': 'Declined',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Accepted quote
    data['quotes'].append({
        'quote_id': 'Q010', 'lead_id': 'L003', 'quote_type': 'Individual',
        'contract_number': 'C011', 'total_premium': 7500.00,
        'quote_date': date(2024, 10, 15), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM014', 'quote_id': 'Q010', 'member_sequence': 1,
        'first_name': 'Susan', 'last_name': 'Martinez',
        'date_of_birth': date(1987, 2, 18), 'email': 'susan.martinez@email.com',
        'phone': '+852-9123-4567', 'gov_id_type': 'HKID', 'gov_id_number': 'L123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['applications'].append({
        'app_id': 'A005', 'quote_id': 'Q010',
        'application_date': date(2024, 10, 20), 'status': 'Approved',
        'contract_number': 'C011',
        'applicant_first_name': 'Susan', 'applicant_last_name': 'Martinez',
        'applicant_dob': date(1987, 2, 18), 'applicant_email': 'susan.martinez@email.com',
        'applicant_phone': '+852-9567-8901', 'applicant_gov_id': 'E123456(7)',
        'spouse_first_name': None, 'spouse_last_name': None,
        'spouse_dob': None, 'spouse_email': None,
        'spouse_phone': None, 'spouse_gov_id': None,
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P010', 'contract_number': 'C011', 'application_id': 'A005',
        'policy_type': 'Individual', 'start_date': date(2024, 11, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 7500.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM012', 'policy_id': 'P010', 'contract_number': 'C011',
        'member_number': 1, 'first_name': 'Susan', 'last_name': 'Martinez',
        'date_of_birth': date(1987, 2, 18), 'email': 'susan.martinez@email.com',
        'phone': '+852-9123-4567', 'gov_id_type': 'HKID', 'gov_id_number': 'L123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2024, 11, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    data['claims'].append({
        'claim_id': 'CL001', 'policy_id': 'P010', 'claimant_member_number': 1,
        'claim_date': date(2024, 12, 1), 'claim_amount': 1500.00,
        'claim_type': 'Medical', 'status': 'Approved',
        'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_lead', 'L003'), ('smartplus_quote', 'Q009'),
                 ('smartplus_quote', 'Q010'), ('smartplus_quote_member', 'QM014'),
                 ('smartplus_application', 'A005'), ('smile_policy', 'P010'),
                 ('smile_policy_member', 'PM012'), ('smile_claim', 'CL001')]:
        add_cluster(data, sid, 'Multi-Touch Journey', cid, t, p)
    
    add_entity(data, sid, 'Multi-Touch Journey', 'ENTITY_011',
              'Susan Martinez - 1987-02-18', ['L003', 'QM014', 'PM012'],
              'Multi-touch with declined and accepted quotes')
    add_match(data, sid, 'L003', 'QM014', True, 'Lead to Quote - Exact name, DOB, email, HKID', 0.95)
    add_match(data, sid, 'QM014', 'PM012', True, 'Exact HKID match', 0.95)
