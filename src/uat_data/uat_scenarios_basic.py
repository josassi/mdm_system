"""
Basic Happy Path Scenarios (S1.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_1_1_perfect_happy_path(data):
    """S1.1: Single person complete sales funnel"""
    sid, cid = "S1.1", 'CLUSTER_001'
    
    data['leads'].append({
        'lead_id': 'L001', 'first_name': 'John', 'last_name': 'Smith',
        'date_of_birth': date(1985, 6, 15), 'email': 'john.smith@email.com',
        'phone': '+852-9123-4567', 'address': "Flat 5A, 123 Queen's Road, Central, HK",
        'gov_id_type': 'HKID', 'gov_id_number': 'A123456(7)',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quotes'].append({
        'quote_id': 'Q001', 'lead_id': 'L001', 'quote_type': 'Individual',
        'contract_number': 'C001', 'total_premium': 5000.00,
        'quote_date': date(2024, 1, 15), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM001', 'quote_id': 'Q001', 'member_sequence': 1,
        'first_name': 'John', 'last_name': 'Smith', 'date_of_birth': date(1985, 6, 15),
        'email': 'john.smith@email.com', 'phone': '+852-9123-4567',
        'gov_id_type': 'HKID', 'gov_id_number': 'A123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['applications'].append({
        'app_id': 'A001', 'quote_id': 'Q001',
        'application_date': date(2024, 1, 20), 'status': 'Approved',
        'contract_number': 'C001',
        'applicant_first_name': 'John', 'applicant_last_name': 'Smith',
        'applicant_dob': date(1985, 6, 15), 'applicant_email': 'john.smith@email.com',
        'applicant_phone': '+852-9123-4567', 'applicant_gov_id': 'A123456(7)',
        'spouse_first_name': None, 'spouse_last_name': None,
        'spouse_dob': None, 'spouse_email': None,
        'spouse_phone': None, 'spouse_gov_id': None,
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P001', 'contract_number': 'C001', 'application_id': 'A001',
        'policy_type': 'Individual', 'start_date': date(2024, 2, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 5000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM001', 'policy_id': 'P001', 'contract_number': 'C001',
        'member_number': 1, 'first_name': 'John', 'last_name': 'Smith',
        'date_of_birth': date(1985, 6, 15), 'email': 'john.smith@email.com',
        'phone': '+852-9123-4567', 'gov_id_type': 'HKID',
        'gov_id_number': 'A123456(7)', 'relationship_type': 'Primary',
        'gender': 'M', 'coverage_start_date': date(2024, 2, 1),
        'coverage_end_date': None, 'is_active': True,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_lead', 'L001'), ('smartplus_quote', 'Q001'),
                 ('smartplus_quote_member', 'QM001'), ('smartplus_application', 'A001'),
                 ('smile_policy', 'P001'), ('smile_policy_member', 'PM001')]:
        add_cluster(data, sid, 'Perfect Happy Path', cid, t, p, 'Complete sales funnel')
    
    add_entity(data, sid, 'Perfect Happy Path', 'ENTITY_001',
               'John Smith - 1985-06-15', ['L001', 'QM001', 'PM001'], 'Single master entity')
    add_match(data, sid, 'L001', 'QM001', True, 'Lead to Quote - Exact name, DOB, email', 0.95)
    add_match(data, sid, 'QM001', 'PM001', True, 'Exact HKID, name, DOB', 0.95)
    add_match(data, sid, 'L001', 'PM001', True, 'Lead to Policy - Exact name, DOB, email', 0.95)


def scenario_1_2_family_quote(data):
    """S1.2: Family of 3"""
    sid, cid = "S1.2", 'CLUSTER_002'
    
    data['leads'].append({
        'lead_id': 'L002', 'first_name': 'Sarah', 'last_name': 'Lee',
        'date_of_birth': date(1982, 3, 20), 'email': 'sarah.lee@email.com',
        'phone': '+852-9234-5678', 'address': 'Unit 12B, 456 Nathan Road, Kowloon, HK',
        'gov_id_type': 'HKID', 'gov_id_number': 'B234567(8)',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quotes'].append({
        'quote_id': 'Q002', 'lead_id': 'L002', 'quote_type': 'Family',
        'contract_number': 'C002', 'total_premium': 15000.00,
        'quote_date': date(2024, 2, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    family = [
        ('QM002', 'Sarah', date(1982, 3, 20), 'sarah.lee@email.com', 'B234567(8)', 'Primary', 'F', 1, 'PM002', 'ENTITY_002A'),
        ('QM003', 'David', date(1980, 7, 10), 'david.lee@email.com', 'B345678(9)', 'Spouse', 'M', 2, 'PM003', 'ENTITY_002B'),
        ('QM004', 'Emma', date(2010, 11, 5), None, 'C456789(0)', 'Child', 'F', 3, 'PM004', 'ENTITY_002C')
    ]
    
    for qm, fname, dob, email, gov, rel, gender, seq, pm, eid in family:
        data['quote_members'].append({
            'qm_id': qm, 'quote_id': 'Q002', 'member_sequence': seq,
            'first_name': fname, 'last_name': 'Lee', 'date_of_birth': dob,
            'email': email, 'phone': '+852-9234-5678',
            'gov_id_type': 'HKID', 'gov_id_number': gov,
            'relationship_type': rel, 'gender': gender,
            'created_date': now(), 'source_system': 'SmartPlus'
        })
        
        data['policy_members'].append({
            'pm_id': pm, 'policy_id': 'P002', 'contract_number': 'C002',
            'member_number': seq, 'first_name': fname, 'last_name': 'Lee',
            'date_of_birth': dob, 'email': email, 'phone': '+852-9234-5678',
            'gov_id_type': 'HKID', 'gov_id_number': gov,
            'relationship_type': rel, 'gender': gender,
            'coverage_start_date': date(2024, 3, 1), 'coverage_end_date': None,
            'is_active': True, 'created_date': now(), 'source_system': 'Smile'
        })
        
        add_match(data, sid, qm, pm, True, f'{fname} Lee - exact HKID', 0.95)
        party_ids = [qm, pm]
        if fname == 'Sarah':
            party_ids.insert(0, 'L002')
            add_match(data, sid, 'L002', qm, True, 'Lead to Quote - Primary member exact name, DOB, email', 0.95)
        add_entity(data, sid, 'Family Quote', eid, f'{fname} Lee - {dob}', party_ids, 'Family member')
    
    data['applications'].append({
        'app_id': 'A002', 'quote_id': 'Q002',
        'application_date': date(2024, 2, 10), 'status': 'Approved',
        'contract_number': 'C002',
        'applicant_first_name': 'Sarah', 'applicant_last_name': 'Lee',
        'applicant_dob': date(1982, 3, 20), 'applicant_email': 'sarah.lee@email.com',
        'applicant_phone': '+852-9234-5678', 'applicant_gov_id': 'B234567(8)',
        'spouse_first_name': 'David', 'spouse_last_name': 'Lee',
        'spouse_dob': date(1980, 7, 10), 'spouse_email': 'david.lee@email.com',
        'spouse_phone': '+852-9234-5678', 'spouse_gov_id': 'B345678(9)',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['policies'].append({
        'policy_id': 'P002', 'contract_number': 'C002', 'application_id': 'A002',
        'policy_type': 'Family', 'start_date': date(2024, 3, 1), 'end_date': None,
        'status': 'Active', 'annual_premium': 15000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_lead', 'L002'), ('smartplus_quote', 'Q002'),
                 ('smartplus_quote_member', 'QM002'), ('smartplus_quote_member', 'QM003'),
                 ('smartplus_quote_member', 'QM004'), ('smartplus_application', 'A002'),
                 ('smile_policy', 'P002'), ('smile_policy_member', 'PM002'),
                 ('smile_policy_member', 'PM003'), ('smile_policy_member', 'PM004')]:
        add_cluster(data, sid, 'Family Quote', cid, t, p)
