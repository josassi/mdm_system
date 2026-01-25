"""
Negative Test Cases (S10.x)
"""

from datetime import date
from uat_scenarios_helpers import add_cluster, add_match, now


def scenario_10_2_cross_cluster(data):
    """S10.2: Cross-cluster validation - CRITICAL NEGATIVE TEST"""
    sid = "S10.2"
    
    # Cluster A - Declined quote
    data['quotes'].append({
        'quote_id': 'Q018', 'lead_id': None, 'quote_type': 'Individual',
        'contract_number': None, 'total_premium': 5000.00,
        'quote_date': date(2025, 4, 1), 'status': 'Declined',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    data['quote_members'].append({
        'qm_id': 'QM034', 'quote_id': 'Q018', 'member_sequence': 1,
        'first_name': 'Tom', 'last_name': 'Brown',
        'date_of_birth': date(1980, 1, 1), 'email': 'tom@email.com',
        'phone': '+852-9222-2222', 'gov_id_type': 'HKID', 'gov_id_number': 'T123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'created_date': now(), 'source_system': 'SmartPlus'
    })
    
    # Cluster B - Separate policy (NO business link to Cluster A)
    data['policies'].append({
        'policy_id': 'P019', 'contract_number': 'C020', 'application_id': None,
        'policy_type': 'Individual', 'start_date': date(2025, 5, 1),
        'end_date': None, 'status': 'Active', 'annual_premium': 5000.00,
        'created_date': now(), 'source_system': 'Smile'
    })
    
    data['policy_members'].append({
        'pm_id': 'PM032', 'policy_id': 'P019', 'contract_number': 'C020',
        'member_number': 1, 'first_name': 'Tom', 'last_name': 'Brown',
        'date_of_birth': date(1980, 1, 1), 'email': 'tom@email.com',
        'phone': '+852-9222-2222', 'gov_id_type': 'HKID', 'gov_id_number': 'T123456(7)',
        'relationship_type': 'Primary', 'gender': 'M',
        'coverage_start_date': date(2025, 5, 1), 'coverage_end_date': None,
        'is_active': True, 'created_date': now(), 'source_system': 'Smile'
    })
    
    # Two separate clusters - NO business link
    add_cluster(data, sid, 'Cross-Cluster Validation', 'CLUSTER_020A',
               'smartplus_quote', 'Q018', 'CRITICAL: Declined quote - separate cluster')
    add_cluster(data, sid, 'Cross-Cluster Validation', 'CLUSTER_020A',
               'smartplus_quote_member', 'QM034')
    
    add_cluster(data, sid, 'Cross-Cluster Validation', 'CLUSTER_020B',
               'smile_policy', 'P019', 'CRITICAL: Separate policy - no link to cluster A')
    add_cluster(data, sid, 'Cross-Cluster Validation', 'CLUSTER_020B',
               'smile_policy_member', 'PM032')
    
    # NEGATIVE TEST: Should NOT match across clusters
    add_match(data, sid, 'QM034', 'PM032', False,
             'CRITICAL NEGATIVE: Identical PII but different clusters - MUST NOT MATCH', 0.0)
    
    # Single-party entities (CRITICAL negative test - should NOT merge)
    from uat_scenarios_helpers import add_entity
    add_entity(data, sid, 'Cross-Cluster Validation', 'ENTITY_020A',
              'Tom Brown - 1980-01-01', ['QM034'], 'Declined quote - separate entity')
    add_entity(data, sid, 'Cross-Cluster Validation', 'ENTITY_020B',
              'Tom Brown - 1980-01-01', ['PM032'], 'Active policy - separate entity')
