"""
Metadata-Driven Scenarios (S11.x)
Tests Excel metadata capabilities not covered by other scenarios.
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_entity, add_match, now


def scenario_11_1_conditional_party_types(data):
    """S11.1: Conditional party type assignment based on relationship_type field"""
    sid, cid = "S11.1", 'CLUSTER_021'
    
    # Family with explicit party type differentiation
    data['quotes'].append({
        'quote_id': 'Q019', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C021', 'total_premium': 20000.00,
        'quote_date': date(2025, 5, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Applicant (Primary) - party_type: smartplus.quote_member.applicant
    data['quote_members'].append({
        'qm_id': 'QM035', 'quote_id': 'Q019', 'member_sequence': 1,
        'first_name': 'Mary', 'last_name': 'Johnson',
        'date_of_birth': date(1985, 1, 15), 'email': 'mary.j@email.com',
        'phone': '+852-9333-3333', 'gov_id_type': 'HKID', 'gov_id_number': 'U123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Spouse - party_type: smartplus.quote_member.spouse
    data['quote_members'].append({
        'qm_id': 'QM036', 'quote_id': 'Q019', 'member_sequence': 2,
        'first_name': 'Paul', 'last_name': 'Johnson',
        'date_of_birth': date(1983, 4, 20), 'email': 'paul.j@email.com',
        'phone': '+852-9333-3333', 'gov_id_type': 'HKID', 'gov_id_number': 'V123456(7)',
        'relationship_type': 'Spouse', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Dependent (Child) - party_type: smartplus.quote_member.dependent
    data['quote_members'].append({
        'qm_id': 'QM037', 'quote_id': 'Q019', 'member_sequence': 3,
        'first_name': 'Lily', 'last_name': 'Johnson',
        'date_of_birth': date(2015, 8, 10), 'email': None,
        'phone': None, 'gov_id_type': 'HKID', 'gov_id_number': 'W123456(7)',
        'relationship_type': 'Child', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for t, p in [('smartplus_quote', 'Q019'), ('smartplus_quote_member', 'QM035'),
                 ('smartplus_quote_member', 'QM036'), ('smartplus_quote_member', 'QM037')]:
        add_cluster(data, sid, 'Conditional Party Types', cid, t, p,
                   'Tests condition_logic: Primary→applicant, Spouse→spouse, Child→dependent')
    
    # Single-party entities (no matching across systems for this test)
    add_entity(data, sid, 'Conditional Party Types', 'ENTITY_021A',
              'Mary Johnson - 1985-01-15', ['QM035'], 'Primary/Applicant')
    add_entity(data, sid, 'Conditional Party Types', 'ENTITY_021B',
              'Paul Johnson - 1983-04-20', ['QM036'], 'Spouse')
    add_entity(data, sid, 'Conditional Party Types', 'ENTITY_021C',
              'Lily Johnson - 2015-08-10', ['QM037'], 'Child/Dependent')


def scenario_11_2_length_based_routing(data):
    """S11.2: Length-based conditional routing (8-digit contract vs 16-digit membership)"""
    sid, cid = "S11.2", 'CLUSTER_022'
    
    # SmartPlus: 8-digit contract_number (relationship field)
    data['quotes'].append({
        'quote_id': 'Q020', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': 'C0220001', 'total_premium': 8000.00,
        'quote_date': date(2025, 6, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM038', 'quote_id': 'Q020', 'member_sequence': 1,
        'first_name': 'Helen', 'last_name': 'Wong',
        'date_of_birth': date(1990, 3, 5), 'email': 'helen.wong@email.com',
        'phone': '+852-9444-4444', 'gov_id_type': 'HKID', 'gov_id_number': 'X123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Smile: 16-digit membership_id (attribute field)
    # Format: C0220001-00000001 (contract + member)
    data['policies'].append({
        'policy_id': 'P020', 'contract_number': 'C0220001', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2025, 7, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 8000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM033', 'policy_id': 'P020', 'contract_number': 'C0220001',
        'member_number': 1, 'first_name': 'Helen', 'last_name': 'Wong',
        'date_of_birth': date(1990, 3, 5), 'email': 'helen.wong@email.com',
        'phone': '+852-9444-4444', 'gov_id_type': 'HKID', 'gov_id_number': 'X123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2025, 7, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    for t, p in [('smartplus_quote', 'Q020'), ('smartplus_quote_member', 'QM038'),
                 ('smile_policy', 'P020'), ('smile_policy_member', 'PM033')]:
        add_cluster(data, sid, 'Length-Based Routing', cid, t, p,
                   'Tests: LEN(contract)=8→relationship, LEN(membership)=16→attribute')
    
    # Single-party entities for S11.2 (note: these could match but testing length-based routing)
    add_entity(data, sid, 'Length-Based Routing', 'ENTITY_022A',
              'Helen Wong - 1990-03-05', ['QM038'], 'Quote member')
    add_entity(data, sid, 'Length-Based Routing', 'ENTITY_022B',
              'Helen Wong - 1990-03-05', ['PM033'], 'Policy member')


def scenario_11_3_bidirectional_relationship(data):
    """S11.3: Bidirectional relationship (spouse-to-spouse)"""
    sid, cid = "S11.3", 'CLUSTER_023'
    
    data['quotes'].append({
        'quote_id': 'Q021', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C023', 'total_premium': 12000.00,
        'quote_date': date(2025, 7, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Two spouses (bidirectional relationship)
    data['quote_members'].append({
        'qm_id': 'QM039', 'quote_id': 'Q021', 'member_sequence': 1,
        'first_name': 'Anna', 'last_name': 'Kim',
        'date_of_birth': date(1988, 5, 12), 'email': 'anna.kim@email.com',
        'phone': '+852-9555-5555', 'gov_id_type': 'HKID', 'gov_id_number': 'Y123456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM040', 'quote_id': 'Q021', 'member_sequence': 2,
        'first_name': 'Brian', 'last_name': 'Kim',
        'date_of_birth': date(1986, 9, 8), 'email': 'brian.kim@email.com',
        'phone': '+852-9555-5555', 'gov_id_type': 'HKID', 'gov_id_number': 'Z123456(7)',
        'relationship_type': 'Spouse', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for t, p in [('smartplus_quote', 'Q021'), ('smartplus_quote_member', 'QM039'),
                 ('smartplus_quote_member', 'QM040')]:
        add_cluster(data, sid, 'Bidirectional Relationship', cid, t, p,
                   'Tests is_bidirectional=TRUE for spouse relationships')
    
    # Single-party entities for S11.3
    add_entity(data, sid, 'Bidirectional Relationship', 'ENTITY_023A',
              'Anna Kim - 1988-05-12', ['QM039'], 'Primary member')
    add_entity(data, sid, 'Bidirectional Relationship', 'ENTITY_023B',
              'Brian Kim - 1986-09-08', ['QM040'], 'Spouse member')


def scenario_11_4_guarantees_same_party_false(data):
    """S11.4: guarantees_same_party=FALSE with business link"""
    sid, cid = "S11.4", 'CLUSTER_024'
    
    # Quote with lead_id link (guarantees_same_party=FALSE)
    # Lead might be a broker, quote_member is the actual insured person
    data['leads'].append({
        'lead_id': 'L004', 'first_name': 'Broker', 'last_name': 'Agency',
        'date_of_birth': None, 'email': 'broker@agency.com',
        'phone': '+852-9666-6666', 'address': 'Office Tower, HK',
        'gov_id_type': None, 'gov_id_number': None,
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quotes'].append({
        'quote_id': 'Q022', 'lead_id': 'L004', 'quote_type': 'Individual',
        'contract_number': 'C024', 'total_premium': 10000.00,
        'quote_date': date(2025, 8, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM041', 'quote_id': 'Q022', 'member_sequence': 1,
        'first_name': 'Daniel', 'last_name': 'Brown',
        'date_of_birth': date(1992, 11, 22), 'email': 'daniel.brown@email.com',
        'phone': '+852-9777-7777', 'gov_id_type': 'HKID', 'gov_id_number': 'AA23456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for t, p in [('smartplus_lead', 'L004'), ('smartplus_quote', 'Q022'),
                 ('smartplus_quote_member', 'QM041')]:
        add_cluster(data, sid, 'guarantees_same_party=FALSE', cid, t, p,
                   'Tests: Quote→Lead link exists but Lead≠QuoteMember (broker scenario)')
    
    # Single-party entities for S11.4 (broker ≠ insured person)
    add_entity(data, sid, 'guarantees_same_party=FALSE', 'ENTITY_024A',
              'Broker Agency', ['L004'], 'Broker lead - not an individual person')
    add_entity(data, sid, 'guarantees_same_party=FALSE', 'ENTITY_024B',
              'Daniel Brown - 1992-11-22', ['QM041'], 'Actual insured person')


def scenario_11_5_priority_quality_conflict(data):
    """S11.5: Same person in multiple systems with different priority/quality_score"""
    sid, cid = "S11.5", 'CLUSTER_025'
    
    # SmartPlus: Lower quality (priority=2, quality=0.75)
    data['quote_members'].append({
        'qm_id': 'QM042', 'quote_id': None, 'member_sequence': 1,
        'first_name': 'jennifer', 'last_name': 'LEE',  # Bad formatting
        'date_of_birth': date(1987, 6, 15), 'email': 'jlee@email.com',
        'phone': '85299998888',  # Missing + and hyphens
        'gov_id_type': 'HKID', 'gov_id_number': 'AB23456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Smile: Higher quality (priority=1, quality=0.95)
    data['policies'].append({
        'policy_id': 'P021', 'contract_number': 'C025', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2025, 9, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 9000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM034', 'policy_id': 'P021', 'contract_number': 'C025',
        'member_number': 1, 'first_name': 'Jennifer', 'last_name': 'Lee',  # Proper formatting
        'date_of_birth': date(1987, 6, 15), 'email': 'jennifer.lee@email.com',
        'phone': '+852-9999-8888',  # Properly formatted
        'gov_id_type': 'HKID', 'gov_id_number': 'AB23456(7)',
        'relationship_type': 'Primary', 'gender': 'F',
        'coverage_start_date': date(2025, 9, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    add_cluster(data, sid, 'Priority/Quality Conflict', cid,
               'smartplus_quote_member', 'QM042',
               'SmartPlus: priority=2, quality=0.75 (lower quality data)')
    add_cluster(data, sid, 'Priority/Quality Conflict', cid,
               'smile_policy', 'P021')
    add_cluster(data, sid, 'Priority/Quality Conflict', cid,
               'smile_policy_member', 'PM034',
               'Smile: priority=1, quality=0.95 (higher quality - SHOULD WIN survivorship)')
    
    add_match(data, sid, 'QM042', 'PM034', True, 'Exact HKID match', 0.95)
    add_entity(data, sid, 'Priority/Quality Conflict', 'ENTITY_025',
              'Jennifer Lee - 1987-06-15', ['QM042', 'PM034'],
              'Golden record should use Smile data (higher priority/quality)')


def scenario_11_6_composite_key_relationship(data):
    """S11.6: Composite key relationship (contract_number|member_number)"""
    sid, cid = "S11.6", 'CLUSTER_026'
    
    # This tests the pipe-delimited composite keys in relationships.csv
    data['quotes'].append({
        'quote_id': 'Q023', 'lead_id': None, 'quote_type': 'Family',
        'contract_number': 'C026', 'total_premium': 16000.00,
        'quote_date': date(2025, 10, 1), 'status': 'Accepted',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    for seq in [1, 2]:
        data['quote_members'].append({
            'qm_id': f'QM{42 + seq:03d}', 'quote_id': 'Q023', 'member_sequence': seq,
            'first_name': f'Person{seq}', 'last_name': 'Composite',
            'date_of_birth': date(1985 + seq, 1, 1),
            'email': f'person{seq}@composite.com',
            'phone': '+852-9000-0000', 'gov_id_type': 'HKID',
            'gov_id_number': f'AC{seq}3456(7)',
            'relationship_type': 'Primary' if seq == 1 else 'Spouse',
            'gender': 'F' if seq == 1 else 'M',
            'created_date': now(), 'source_system': 'SmartPlus'
        })
    
    data['policies'].append({
        'policy_id': 'P022', 'contract_number': 'C026', 'application_id': None,
        'policy_type': 'Family', 'start_date': date(2025, 11, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 16000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    for seq in [1, 2]:
        data['policy_members'].append({
            'pm_id': f'PM{34 + seq:03d}', 'policy_id': 'P022',
            'contract_number': 'C026', 'member_number': seq,
            'first_name': f'Person{seq}', 'last_name': 'Composite',
            'date_of_birth': date(1985 + seq, 1, 1),
            'email': f'person{seq}@composite.com',
            'phone': '+852-9000-0000', 'gov_id_type': 'HKID',
            'gov_id_number': f'AC{seq}3456(7)',
            'relationship_type': 'Primary' if seq == 1 else 'Spouse',
            'gender': 'F' if seq == 1 else 'M',
            'coverage_start_date': date(2025, 11, 1), 'coverage_end_date': None,
            'is_active': True, 'created_date': now(), 'source_system': 'Smile'
        })
        
        add_match(data, sid, f'QM{42 + seq:03d}', f'PM{34 + seq:03d}', True,
                 f'Composite key: contract|member={seq}', 1.0)
        add_entity(data, sid, 'Composite Key Relationship', f'ENTITY_026_{seq}',
                  f'Person{seq} Composite - {date(1985 + seq, 1, 1)}', 
                  [f'QM{42 + seq:03d}', f'PM{34 + seq:03d}'],
                  f'Composite key match: member {seq}')
    
    for t, p in [('smartplus_quote', 'Q023'), ('smartplus_quote_member', 'QM043'),
                 ('smartplus_quote_member', 'QM044'), ('smile_policy', 'P022'),
                 ('smile_policy_member', 'PM035'), ('smile_policy_member', 'PM036')]:
        add_cluster(data, sid, 'Composite Key Relationship', cid, t, p,
                   'Tests: contract_number|member_number composite key matching')
