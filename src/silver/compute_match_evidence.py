"""
MATCH_EVIDENCE Computation - Silver Layer

Implements two-phase matching strategy:
1. Phase 1: Within-cluster blocking (PRIMARY) - compare all pairs in same cluster
2. Phase 2: Cross-cluster blocking (SECONDARY) - strong PII keys across clusters

Also implements MATCH_BLOCKING rules to prevent merges when conflicts exist
(e.g., two parties with different valid HKIDs cannot be the same person).

Algorithm:
Phase 1 - Within Cluster:
  For each cluster:
    Get all parties in cluster
    Generate all pairs (cartesian product)
    For each pair:
      Check if pair is blocked (MATCH_BLOCKING rules)
      If not blocked:
        Run match rules
        Generate MATCH_EVIDENCE if confidence > threshold
      If blocked:
        Record in MATCH_BLOCKING table

Phase 2 - Cross Cluster (future):
  For each strong PII blocking key (HKID, Passport, Email):
    Get candidate pairs across clusters
    Skip if already compared in Phase 1
    Apply same matching logic

Match Rules:
- Exact HKID match (deterministic, confidence=1.0)
- Exact Passport match (deterministic, confidence=1.0)
- Exact email match (deterministic, confidence=0.95)
- Exact phone match (deterministic, confidence=0.9)
- Fuzzy name + DOB match (probabilistic, confidence varies)

Blocking Rules:
- Conflicting HKIDs: Different valid HKIDs = block
- Gender conflict: Same name/DOB but different gender = block or review
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
from itertools import combinations
from collections import defaultdict


def load_data():
    """Load Silver layer data"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / 'data/silver'
    bronze_dir = project_root / 'data/bronze'
    
    print("Loading Silver and Bronze data...")
    
    party_cluster = pd.read_csv(silver_dir / 'party_cluster.csv')
    standardized_attribute = pd.read_csv(silver_dir / 'standardized_attribute.csv')
    source_party = pd.read_csv(bronze_dir / 'source_party.csv')
    
    print(f"  ✓ Loaded {len(party_cluster)} PARTY_CLUSTER records")
    print(f"  ✓ Loaded {len(standardized_attribute)} STANDARDIZED_ATTRIBUTE records")
    print(f"  ✓ Loaded {len(source_party)} SOURCE_PARTY records")
    
    return party_cluster, standardized_attribute, source_party


def get_party_attributes(party_id, std_attr_df):
    """
    Get all standardized attributes for a party as a dictionary.
    
    Returns: dict with attribute_subtype_id as key and standardized_value as value
    """
    party_attrs = std_attr_df[std_attr_df['source_party_id'] == party_id]
    
    attr_dict = {}
    for _, row in party_attrs.iterrows():
        subtype_id = row['attribute_subtype_id']
        value = row['standardized_value']
        attr_dict[subtype_id] = value
    
    return attr_dict


def check_blocking_rules(party1_id, party2_id, attrs1, attrs2):
    """
    Check if two parties should be blocked from matching.
    
    Returns: (is_blocked, blocking_reason, blocking_details)
    """
    
    # Rule 1: Conflicting HKIDs
    hkid1 = attrs1.get('SUB_HKID')
    hkid2 = attrs2.get('SUB_HKID')
    
    if hkid1 and hkid2 and hkid1 != hkid2:
        # Both have HKIDs and they're different = definitely different people
        return True, 'CONFLICTING_HKID', {
            'party1_hkid': hkid1,
            'party2_hkid': hkid2
        }
    
    # Rule 2: Conflicting Passports (if both are non-null and different)
    passport1 = attrs1.get('SUB_PASSPORT')
    passport2 = attrs2.get('SUB_PASSPORT')
    
    if passport1 and passport2 and passport1 != passport2:
        return True, 'CONFLICTING_PASSPORT', {
            'party1_passport': passport1,
            'party2_passport': passport2
        }
    
    # Rule 3: Gender conflict (if names similar but gender different)
    # This is more nuanced - could be review rather than hard block
    gender1 = attrs1.get('SUB_GENDER')
    gender2 = attrs2.get('SUB_GENDER')
    fname1 = attrs1.get('SUB_FIRST_NAME')
    fname2 = attrs2.get('SUB_FIRST_NAME')
    lname1 = attrs1.get('SUB_LAST_NAME')
    lname2 = attrs2.get('SUB_LAST_NAME')
    
    if (gender1 and gender2 and gender1 != gender2 and
        fname1 and fname2 and fname1 == fname2 and
        lname1 and lname2 and lname1 == lname2):
        # Same name but different gender = suspicious, block
        return True, 'GENDER_CONFLICT', {
            'party1_gender': gender1,
            'party2_gender': gender2,
            'shared_name': f"{fname1} {lname1}"
        }
    
    return False, None, None


def run_match_rules(party1_id, party2_id, attrs1, attrs2):
    """
    Run match rules and return list of evidence records.
    
    Returns: list of (match_rule_id, match_key, evidence_value, confidence_score)
    """
    evidence = []
    
    # Rule 1: Exact HKID match (highest confidence)
    hkid1 = attrs1.get('SUB_HKID')
    hkid2 = attrs2.get('SUB_HKID')
    if hkid1 and hkid2 and hkid1 == hkid2:
        evidence.append(('RULE_EXACT_HKID', 'HKID', hkid1, 1.0))
    
    # Rule 2: Exact Passport match
    passport1 = attrs1.get('SUB_PASSPORT')
    passport2 = attrs2.get('SUB_PASSPORT')
    if passport1 and passport2 and passport1 == passport2:
        evidence.append(('RULE_EXACT_PASSPORT', 'PASSPORT', passport1, 1.0))
    
    # Rule 3: Exact Email match
    email1 = attrs1.get('SUB_EMAIL')
    email2 = attrs2.get('SUB_EMAIL')
    if email1 and email2 and email1 == email2:
        evidence.append(('RULE_EXACT_EMAIL', 'EMAIL', email1, 0.95))
    
    # Rule 4: Exact Phone match
    phone1 = attrs1.get('SUB_PHONE')
    phone2 = attrs2.get('SUB_PHONE')
    if phone1 and phone2 and phone1 == phone2:
        evidence.append(('RULE_EXACT_PHONE', 'PHONE', phone1, 0.9))
    
    # Rule 5: Exact Name + DOB match
    fname1 = attrs1.get('SUB_FIRST_NAME')
    fname2 = attrs2.get('SUB_FIRST_NAME')
    lname1 = attrs1.get('SUB_LAST_NAME')
    lname2 = attrs2.get('SUB_LAST_NAME')
    dob1 = attrs1.get('SUB_DOB')
    dob2 = attrs2.get('SUB_DOB')
    
    if (fname1 and fname2 and fname1 == fname2 and
        lname1 and lname2 and lname1 == lname2 and
        dob1 and dob2 and dob1 == dob2):
        evidence.append(('RULE_EXACT_NAME_DOB', 'NAME_DOB', f"{fname1}|{lname1}|{dob1}", 0.95))
    
    # Rule 6: Exact Full Name + Email match
    if (fname1 and fname2 and fname1 == fname2 and
        lname1 and lname2 and lname1 == lname2 and
        email1 and email2 and email1 == email2):
        evidence.append(('RULE_EXACT_NAME_EMAIL', 'NAME_EMAIL', f"{fname1}|{lname1}|{email1}", 0.92))
    
    return evidence


def generate_phase1_evidence(cluster_df, std_attr_df, source_party_df):
    """
    Phase 1: Generate match evidence within clusters.
    
    For each cluster, compare all pairs of parties.
    """
    print("\n" + "="*70)
    print("PHASE 1: WITHIN-CLUSTER MATCHING")
    print("="*70)
    
    evidence_records = []
    blocking_records = []
    seen_pairs = set()
    
    cluster_stats = defaultdict(int)
    
    # Group by cluster_id
    clusters = cluster_df.groupby('cluster_id')
    
    for cluster_id, cluster_group in clusters:
        party_ids = cluster_group['party_id'].tolist()
        
        if len(party_ids) < 2:
            # Singleton cluster, no pairs to compare
            cluster_stats['singleton_clusters'] += 1
            continue
        
        cluster_stats['multi_party_clusters'] += 1
        
        # Generate all pairs in cluster
        pairs = list(combinations(party_ids, 2))
        cluster_stats['total_pairs'] += len(pairs)
        
        for party1_id, party2_id in pairs:
            # Normalize pair order (always smaller ID first)
            pair_key = tuple(sorted([party1_id, party2_id]))
            
            if pair_key in seen_pairs:
                continue
            
            seen_pairs.add(pair_key)
            
            # Get attributes for both parties
            attrs1 = get_party_attributes(party1_id, std_attr_df)
            attrs2 = get_party_attributes(party2_id, std_attr_df)
            
            # Check blocking rules
            is_blocked, blocking_reason, blocking_details = check_blocking_rules(
                party1_id, party2_id, attrs1, attrs2
            )
            
            if is_blocked:
                # Create blocking record
                blocking_records.append({
                    'blocking_id': str(uuid.uuid4()),
                    'party_id_1': party1_id,
                    'party_id_2': party2_id,
                    'blocking_reason_code': blocking_reason,
                    'blocking_rule_id': f"RULE_{blocking_reason}",
                    'blocking_source': 'AUTOMATIC',
                    'conflicting_attribute_subtype_id': 'SUB_HKID' if 'HKID' in blocking_reason else None,
                    'conflict_details': str(blocking_details),
                    'created_at': datetime.now().isoformat(),
                    'is_active': True,
                    'created_by': 'SYSTEM'
                })
                cluster_stats['blocked_pairs'] += 1
                continue
            
            # Run match rules
            match_evidence = run_match_rules(party1_id, party2_id, attrs1, attrs2)
            
            if not match_evidence:
                # No evidence found
                cluster_stats['no_evidence_pairs'] += 1
                continue
            
            # Create evidence records (one per match rule that fired)
            for rule_id, match_key, evidence_value, confidence in match_evidence:
                evidence_records.append({
                    'evidence_id': str(uuid.uuid4()),
                    'party_id_1': party1_id,
                    'party_id_2': party2_id,
                    'match_type': 'PII',
                    'match_rule_id': rule_id,
                    'match_key': match_key,
                    'evidence_value': evidence_value,
                    'confidence_score': confidence,
                    'created_at': datetime.now().isoformat(),
                    'blocking_keys': f'CLUSTER:{cluster_id}'
                })
            
            cluster_stats['evidence_pairs'] += 1
    
    print(f"\n✓ Phase 1 Complete:")
    print(f"  Multi-party clusters: {cluster_stats['multi_party_clusters']}")
    print(f"  Singleton clusters: {cluster_stats['singleton_clusters']}")
    print(f"  Total pairs compared: {cluster_stats['total_pairs']}")
    print(f"  Pairs with evidence: {cluster_stats['evidence_pairs']}")
    print(f"  Pairs blocked: {cluster_stats['blocked_pairs']}")
    print(f"  Pairs with no evidence: {cluster_stats['no_evidence_pairs']}")
    print(f"  Total evidence records: {len(evidence_records)}")
    print(f"  Total blocking records: {len(blocking_records)}")
    
    return evidence_records, blocking_records, seen_pairs


def generate_phase2_evidence(cluster_df, std_attr_df, evidence_records, blocking_records, seen_pairs):
    """
    Phase 2: Generate match evidence across clusters using strong PII blocking keys.
    
    Only compares pairs that:
    - Were NOT already compared in Phase 1
    - Are in DIFFERENT clusters
    - Share a strong PII attribute (HKID, Passport, Email)
    """
    print("\n" + "="*70)
    print("PHASE 2: CROSS-CLUSTER MATCHING (STRONG PII)")
    print("="*70)
    
    phase2_stats = defaultdict(int)
    
    # Create party to cluster mapping for quick lookup
    party_to_cluster = dict(zip(cluster_df['party_id'], cluster_df['cluster_id']))
    
    # Define strong PII blocking keys
    blocking_keys = [
        ('SUB_HKID', 'EXACT_HKID'),
        ('SUB_PASSPORT', 'EXACT_PASSPORT'),
        ('SUB_EMAIL', 'EXACT_EMAIL')
    ]
    
    for subtype_id, blocking_key_name in blocking_keys:
        print(f"\n  Processing blocking key: {blocking_key_name}")
        
        # Get all parties with this attribute
        parties_with_attr = std_attr_df[std_attr_df['attribute_subtype_id'] == subtype_id]
        
        if len(parties_with_attr) == 0:
            print(f"    No parties with {subtype_id}")
            continue
        
        # Group by standardized_value to find potential matches
        value_groups = parties_with_attr.groupby('standardized_value')['source_party_id'].apply(list)
        
        candidates_found = 0
        pairs_skipped_same_cluster = 0
        pairs_skipped_seen = 0
        pairs_compared = 0
        
        for value, party_list in value_groups.items():
            if len(party_list) < 2:
                continue
            
            # Generate all pairs with this value
            pairs = list(combinations(party_list, 2))
            candidates_found += len(pairs)
            
            for party1_id, party2_id in pairs:
                # Normalize pair order
                pair_key = tuple(sorted([party1_id, party2_id]))
                
                # Skip if already compared in Phase 1
                if pair_key in seen_pairs:
                    pairs_skipped_seen += 1
                    continue
                
                # Skip if same cluster (should have been in Phase 1)
                cluster1 = party_to_cluster.get(party1_id)
                cluster2 = party_to_cluster.get(party2_id)
                if cluster1 == cluster2:
                    pairs_skipped_same_cluster += 1
                    continue
                
                # Mark as seen
                seen_pairs.add(pair_key)
                pairs_compared += 1
                
                # Get attributes for both parties
                attrs1 = get_party_attributes(party1_id, std_attr_df)
                attrs2 = get_party_attributes(party2_id, std_attr_df)
                
                # Check blocking rules
                is_blocked, blocking_reason, blocking_details = check_blocking_rules(
                    party1_id, party2_id, attrs1, attrs2
                )
                
                if is_blocked:
                    # Create blocking record
                    blocking_records.append({
                        'blocking_id': str(uuid.uuid4()),
                        'party_id_1': party1_id,
                        'party_id_2': party2_id,
                        'blocking_reason_code': blocking_reason,
                        'blocking_rule_id': f"RULE_{blocking_reason}",
                        'blocking_source': 'AUTOMATIC',
                        'conflicting_attribute_subtype_id': 'SUB_HKID' if 'HKID' in blocking_reason else None,
                        'conflict_details': str(blocking_details),
                        'created_at': datetime.now().isoformat(),
                        'is_active': True,
                        'created_by': 'SYSTEM'
                    })
                    phase2_stats[f'{blocking_key_name}_blocked'] += 1
                    continue
                
                # Run match rules
                match_evidence = run_match_rules(party1_id, party2_id, attrs1, attrs2)
                
                if not match_evidence:
                    phase2_stats[f'{blocking_key_name}_no_evidence'] += 1
                    continue
                
                # Create evidence records
                for rule_id, match_key, evidence_value, confidence in match_evidence:
                    evidence_records.append({
                        'evidence_id': str(uuid.uuid4()),
                        'party_id_1': party1_id,
                        'party_id_2': party2_id,
                        'match_type': 'PII',
                        'match_rule_id': rule_id,
                        'match_key': match_key,
                        'evidence_value': evidence_value,
                        'confidence_score': confidence,
                        'created_at': datetime.now().isoformat(),
                        'blocking_keys': blocking_key_name
                    })
                
                phase2_stats[f'{blocking_key_name}_evidence'] += 1
        
        print(f"    Candidate pairs: {candidates_found}")
        print(f"    Skipped (same cluster): {pairs_skipped_same_cluster}")
        print(f"    Skipped (already seen): {pairs_skipped_seen}")
        print(f"    New pairs compared: {pairs_compared}")
        print(f"    Pairs with evidence: {phase2_stats.get(f'{blocking_key_name}_evidence', 0)}")
        print(f"    Pairs blocked: {phase2_stats.get(f'{blocking_key_name}_blocked', 0)}")
    
    # Overall Phase 2 stats
    total_evidence = sum(v for k, v in phase2_stats.items() if '_evidence' in k)
    total_blocked = sum(v for k, v in phase2_stats.items() if '_blocked' in k)
    
    print(f"\n✓ Phase 2 Complete:")
    print(f"  Total new evidence records: {total_evidence}")
    print(f"  Total new blocking records: {total_blocked}")
    
    return evidence_records, blocking_records


def export_match_data(evidence_df, blocking_df, output_dir='data/silver'):
    """Export MATCH_EVIDENCE and MATCH_BLOCKING to CSV"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / output_dir
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    evidence_file = silver_dir / 'match_evidence.csv'
    blocking_file = silver_dir / 'match_blocking.csv'
    
    evidence_df.to_csv(evidence_file, index=False)
    blocking_df.to_csv(blocking_file, index=False)
    
    print(f"\n✓ Exported to:")
    print(f"  {evidence_file}")
    print(f"  {blocking_file}")


def main():
    print("="*70)
    print("MATCH EVIDENCE COMPUTATION")
    print("="*70)
    
    # Load data
    cluster_df, std_attr_df, source_party_df = load_data()
    
    # Phase 1: Within-cluster matching
    evidence_records, blocking_records, seen_pairs = generate_phase1_evidence(
        cluster_df, std_attr_df, source_party_df
    )
    
    # Phase 2: Cross-cluster matching (strong PII)
    evidence_records, blocking_records = generate_phase2_evidence(
        cluster_df, std_attr_df, evidence_records, blocking_records, seen_pairs
    )
    
    # Convert to DataFrames
    evidence_df = pd.DataFrame(evidence_records)
    blocking_df = pd.DataFrame(blocking_records)
    
    # Export
    export_match_data(evidence_df, blocking_df)
    
    print("\n" + "="*70)
    print("✅ MATCH EVIDENCE COMPUTATION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
