"""
UAT Scenario Data Generation - Main Orchestrator
Imports all scenario modules and generates complete test dataset.
"""

from uat_scenarios_helpers import init_data_structure
from uat_scenarios_basic import scenario_1_1_perfect_happy_path, scenario_1_2_family_quote
from uat_scenarios_granularity import scenario_2_1_quote_level_link, scenario_2_2_membership_number
from uat_scenarios_missing_links import scenario_3_1_orphaned_policy, scenario_3_2_broken_link
from uat_scenarios_matching import (
    scenario_4_1_same_person_no_link, 
    scenario_4_2_same_name_different,
    scenario_5_1_name_variations, 
    scenario_5_2_name_transposition
)
from uat_scenarios_complex import scenario_7_1_multi_touch
from uat_scenarios_edge_cases import (
    scenario_8_1_missing_pii, 
    scenario_8_2_duplicate_members,
    scenario_8_3_invalid_fk, 
    scenario_9_1_large_family, 
    scenario_9_3_special_characters
)
from uat_scenarios_negative import scenario_10_2_cross_cluster
from uat_scenarios_metadata_driven import (
    scenario_11_1_conditional_party_types,
    scenario_11_2_length_based_routing,
    scenario_11_3_bidirectional_relationship,
    scenario_11_4_guarantees_same_party_false,
    scenario_11_5_priority_quality_conflict,
    scenario_11_6_composite_key_relationship
)
from uat_scenarios_blocking_rules import (
    scenario_12_1_conflicting_hkids,
    scenario_12_2_name_change_over_time,
    scenario_12_3_gender_conflict,
    scenario_12_4_multiple_id_types,
    scenario_12_5_typo_in_critical_field
)


def generate_all_scenarios():
    """
    Generate data for all test scenarios and return as dictionaries.
    
    Returns:
        dict: Dictionary containing lists for each table type:
            - leads, quotes, quote_members, applications
            - policies, policy_members, claims
            - expected_clusters, expected_entities, expected_matches
    """
    
    # Initialize data structure
    data = init_data_structure()
    
    # Generate all scenarios
    print("\n[S1.1] Perfect Happy Path - Single person full journey")
    scenario_1_1_perfect_happy_path(data)
    
    print("[S1.2] Family Quote - 3 members")
    scenario_1_2_family_quote(data)
    
    print("[S2.1] Quote Level Link - Granularity loss")
    scenario_2_1_quote_level_link(data)
    
    print("[S2.2] Membership Number Granularity")
    scenario_2_2_membership_number(data)
    
    print("[S3.1] Orphaned Policy - Missing upstream records")
    scenario_3_1_orphaned_policy(data)
    
    print("[S3.2] Broken Link - Missing FK reference")
    scenario_3_2_broken_link(data)
    
    print("[S4.1] Same Person No Link - NEGATIVE TEST")
    scenario_4_1_same_person_no_link(data)
    
    print("[S4.2] Same Name Different Person")
    scenario_4_2_same_name_different(data)
    
    print("[S5.1] Name Variations - Fuzzy matching")
    scenario_5_1_name_variations(data)
    
    print("[S5.2] Name Transposition")
    scenario_5_2_name_transposition(data)
    
    print("[S7.1] Multi-Touch Journey - Multiple quotes")
    scenario_7_1_multi_touch(data)
    
    print("[S8.1] Missing PII - NULL values")
    scenario_8_1_missing_pii(data)
    
    print("[S8.2] Duplicate Members - Data quality bug")
    scenario_8_2_duplicate_members(data)
    
    print("[S8.3] Invalid FK - NULL quote_id")
    scenario_8_3_invalid_fk(data)
    
    print("[S9.1] Large Family - 12 members (performance test)")
    scenario_9_1_large_family(data)
    
    print("[S9.3] Special Characters - Unicode")
    scenario_9_3_special_characters(data)
    
    print("[S10.2] Cross-Cluster Validation - CRITICAL TEST")
    scenario_10_2_cross_cluster(data)
    
    print("\n--- METADATA-DRIVEN SCENARIOS ---")
    print("[S11.1] Conditional Party Types - relationship_type based routing")
    scenario_11_1_conditional_party_types(data)
    
    print("[S11.2] Length-Based Routing - 8-digit vs 16-digit membership")
    scenario_11_2_length_based_routing(data)
    
    print("[S11.3] Bidirectional Relationship - Spouse-to-spouse")
    scenario_11_3_bidirectional_relationship(data)
    
    print("[S11.4] guarantees_same_party=FALSE - Broker scenario")
    scenario_11_4_guarantees_same_party_false(data)
    
    print("[S11.5] Priority/Quality Conflict - Survivorship rules")
    scenario_11_5_priority_quality_conflict(data)
    
    print("[S11.6] Composite Key Relationship - contract|member")
    scenario_11_6_composite_key_relationship(data)
    
    print("\n--- BLOCKING RULES & CONFLICT DETECTION SCENARIOS ---")
    print("[S12.1] Conflicting HKIDs - Blocking rule test")
    scenario_12_1_conflicting_hkids(data)
    
    print("[S12.2] Name Change Over Time - Maiden name scenario")
    scenario_12_2_name_change_over_time(data)
    
    print("[S12.3] Gender Conflict - Blocking rule test")
    scenario_12_3_gender_conflict(data)
    
    print("[S12.4] Multiple ID Types - HKID and Passport for same person")
    scenario_12_4_multiple_id_types(data)
    
    print("[S12.5] DOB Typo - Near match requiring review")
    scenario_12_5_typo_in_critical_field(data)
    
    return data
