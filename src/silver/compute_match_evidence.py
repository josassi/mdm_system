"""
MATCH_EVIDENCE & DIFFERENCE_EVIDENCE Computation - Silver Layer

Implements evidence-based scoring with two-phase strategy:
1. Phase 1: Within-cluster comparison - compare all pairs in same cluster
2. Phase 2: Cross-cluster comparison - strong PII keys across clusters

Generates two types of evidence:
- MATCH_EVIDENCE: Attributes that match (with confidence scores)
- DIFFERENCE_EVIDENCE: Attributes that differ (with severity scores)

Algorithm:
Phase 1 - Within Cluster:
  For each cluster:
    Get all parties in cluster
    Generate all pairs (cartesian product)
    For each pair:
      Check for hard blocks (severity=1.0) FIRST
      If hard block found:
        Generate DIFFERENCE_EVIDENCE for blocking attribute
        Set evaluation_complete=False
        SKIP remaining attributes (early exit)
      Else:
        Compare ALL attributes
        Generate MATCH_EVIDENCE for matches
        Generate DIFFERENCE_EVIDENCE for differences
        Set evaluation_complete=True

Phase 2 - Cross Cluster:
  For each strong PII blocking key (HKID, Passport, Email, DOB):
    Get candidate pairs across clusters
    Skip if already compared in Phase 1
    Apply same evidence collection logic

Evidence Rules (from metadata_evidence_rule.csv):
- Hard links (confidence=1.0): HKID, Passport, Gov ID
- Hard blocks (severity=1.0): Conflicting HKID, Passport, Gov ID
- Soft evidence (0.0-0.9): Email, phone, name, DOB, gender, address
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
from itertools import combinations
from collections import defaultdict


def load_data():
    """Load Silver layer data and metadata"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / 'data/silver'
    bronze_dir = project_root / 'data/bronze'
    metadata_dir = project_root / 'data/uat_generation/metadata'
    
    print("Loading Silver and Bronze data...")
    
    party_cluster = pd.read_csv(silver_dir / 'party_cluster.csv')
    standardized_attribute = pd.read_csv(silver_dir / 'standardized_attribute.csv')
    raw_attribute = pd.read_csv(bronze_dir / 'raw_attribute.csv')
    source_party = pd.read_csv(bronze_dir / 'source_party.csv')
    evidence_rules = pd.read_csv(metadata_dir / 'metadata_evidence_rule.csv')
    metadata_column = pd.read_csv(metadata_dir / 'metadata_column.csv')
    
    print(f"  ✓ Loaded {len(party_cluster)} PARTY_CLUSTER records")
    print(f"  ✓ Loaded {len(standardized_attribute)} STANDARDIZED_ATTRIBUTE records")
    print(f"  ✓ Loaded {len(raw_attribute)} RAW_ATTRIBUTE records")
    print(f"  ✓ Loaded {len(source_party)} SOURCE_PARTY records")
    print(f"  ✓ Loaded {len(evidence_rules)} METADATA_EVIDENCE_RULE records")
    print(f"  ✓ Loaded {len(metadata_column)} METADATA_COLUMN records")
    
    return party_cluster, standardized_attribute, raw_attribute, source_party, evidence_rules, metadata_column


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


def collect_pair_evidence(party1_id, party2_id, attrs1, attrs2, std_attr_df, raw_attr_df, 
                          evidence_rules_df, metadata_column_df):
    """
    Collect all evidence (matches and differences) for a pair of parties.
    Implements early exit for hard blocks (severity=1.0).
    
    Returns: (match_evidences, difference_evidences, evaluation_complete)
    """
    match_evidences = []
    difference_evidences = []
    evaluation_complete = True
    
    # Get all unique attributes present for either party
    all_attributes = set(attrs1.keys()) | set(attrs2.keys())
    
    # Get evidence rules and sort by priority (check hard blocks first)
    active_rules = evidence_rules_df[evidence_rules_df['is_active'] == True].sort_values(
        'priority', ascending=False
    )
    
    # Create attribute lookup for evidence rules
    rules_by_attr = {row['attribute_subtype_id']: row for _, row in active_rules.iterrows()}
    
    # STEP 1: Check for hard blocks first (early exit optimization)
    for attribute_subtype in all_attributes:
        if attribute_subtype not in rules_by_attr:
            continue
        
        rule = rules_by_attr[attribute_subtype]
        hard_block_threshold = rule.get('hard_block_threshold')
        
        # Skip if not a potential hard block
        if pd.isna(hard_block_threshold) or hard_block_threshold != 1.0:
            continue
        
        value1 = attrs1.get(attribute_subtype)
        value2 = attrs2.get(attribute_subtype)
        
        # Both values must exist to be a hard block
        if value1 and value2 and value1 != value2:
            # HARD BLOCK FOUND - create difference evidence and exit
            difference_evidences.append({
                'evidence_id': str(uuid.uuid4()),
                'party_id_1': party1_id,
                'party_id_2': party2_id,
                'attribute_subtype_id': attribute_subtype,
                'value_1': value1,
                'value_2': value2,
                'severity_score': 1.0,
                'is_hard_block': True,
                'difference_type': 'HARD_CONFLICT',
                'created_at': datetime.now().isoformat()
            })
            evaluation_complete = False
            return match_evidences, difference_evidences, evaluation_complete
    
    # STEP 2: No hard blocks - evaluate all attributes fully
    for attribute_subtype in all_attributes:
        if attribute_subtype not in rules_by_attr:
            continue
        
        rule = rules_by_attr[attribute_subtype]
        value1 = attrs1.get(attribute_subtype)
        value2 = attrs2.get(attribute_subtype)
        
        # Skip if both values are null
        if not value1 and not value2:
            continue
        
        # Case 1: Both values exist - compare them
        if value1 and value2:
            if value1 == value2:
                # MATCH - create match evidence
                match_weight = rule.get('match_weight', 0.0)
                if match_weight > 0:
                    match_evidences.append({
                        'evidence_id': str(uuid.uuid4()),
                        'party_id_1': party1_id,
                        'party_id_2': party2_id,
                        'match_type': 'EXACT_MATCH',
                        'match_rule_id': f"RULE_EXACT_{attribute_subtype}",
                        'match_key': attribute_subtype,
                        'evidence_value': value1,
                        'confidence_score': 1.0 if rule.get('hard_link_threshold') == 1.0 else 0.95,
                        'created_at': datetime.now().isoformat(),
                        'blocking_keys': 'PHASE_1'
                    })
            else:
                # DIFFERENCE - create difference evidence
                difference_weight = rule.get('difference_weight', 0.0)
                if difference_weight > 0:
                    difference_evidences.append({
                        'evidence_id': str(uuid.uuid4()),
                        'party_id_1': party1_id,
                        'party_id_2': party2_id,
                        'attribute_subtype_id': attribute_subtype,
                        'value_1': value1,
                        'value_2': value2,
                        'severity_score': difference_weight,
                        'is_hard_block': False,
                        'difference_type': 'SOFT_CONFLICT',
                        'created_at': datetime.now().isoformat()
                    })
    
    return match_evidences, difference_evidences, evaluation_complete


def generate_phase1_evidence(cluster_df, std_attr_df, raw_attr_df, source_party_df, 
                             evidence_rules_df, metadata_column_df):
    """
    Phase 1: Generate match and difference evidence within clusters.
    For each cluster, compare all pairs of parties.
    """
    print("\n" + "="*70)
    print("PHASE 1: WITHIN-CLUSTER EVIDENCE COLLECTION")
    print("="*70)
    
    match_records = []
    difference_records = []
    seen_pairs = set()
    
    cluster_stats = defaultdict(int)
    
    # Group by cluster_id
    clusters = cluster_df.groupby('cluster_id')
    
    for cluster_id, cluster_group in clusters:
        party_ids = cluster_group['party_id'].tolist()
        
        if len(party_ids) < 2:
            cluster_stats['singleton_clusters'] += 1
            continue
        
        cluster_stats['multi_party_clusters'] += 1
        
        # Generate all pairs in cluster
        pairs = list(combinations(party_ids, 2))
        cluster_stats['total_pairs'] += len(pairs)
        
        for party1_id, party2_id in pairs:
            # Normalize pair order
            pair_key = tuple(sorted([party1_id, party2_id]))
            
            if pair_key in seen_pairs:
                continue
            
            seen_pairs.add(pair_key)
            
            # Get attributes for both parties
            attrs1 = get_party_attributes(party1_id, std_attr_df)
            attrs2 = get_party_attributes(party2_id, std_attr_df)
            
            # Collect all evidence (matches and differences)
            match_evs, diff_evs, eval_complete = collect_pair_evidence(
                party1_id, party2_id, attrs1, attrs2, 
                std_attr_df, raw_attr_df, evidence_rules_df, metadata_column_df
            )
            
            # Track statistics
            if diff_evs and any(d['is_hard_block'] for d in diff_evs):
                cluster_stats['hard_blocked_pairs'] += 1
            elif match_evs:
                cluster_stats['pairs_with_matches'] += 1
            if diff_evs:
                cluster_stats['pairs_with_differences'] += 1
            if not match_evs and not diff_evs:
                cluster_stats['no_evidence_pairs'] += 1
            
            # Store evidence
            match_records.extend(match_evs)
            difference_records.extend(diff_evs)
    
    print(f"\n✓ Phase 1 Complete:")
    print(f"  Multi-party clusters: {cluster_stats['multi_party_clusters']}")
    print(f"  Singleton clusters: {cluster_stats['singleton_clusters']}")
    print(f"  Total pairs compared: {cluster_stats['total_pairs']}")
    print(f"  Pairs with matches: {cluster_stats.get('pairs_with_matches', 0)}")
    print(f"  Pairs with differences: {cluster_stats.get('pairs_with_differences', 0)}")
    print(f"  Hard blocked pairs: {cluster_stats.get('hard_blocked_pairs', 0)}")
    print(f"  No evidence pairs: {cluster_stats.get('no_evidence_pairs', 0)}")
    print(f"  Total match evidence: {len(match_records)}")
    print(f"  Total difference evidence: {len(difference_records)}")
    
    return match_records, difference_records, seen_pairs


def generate_phase2_evidence(cluster_df, std_attr_df, raw_attr_df, match_records, 
                             difference_records, seen_pairs, evidence_rules_df, metadata_column_df):
    """
    Phase 2: Generate evidence across clusters using strong PII blocking keys.
    
    Only compares pairs that:
    - Were NOT already compared in Phase 1
    - Are in DIFFERENT clusters
    - Share a strong PII attribute (HKID, Passport, Email, DOB)
    """
    print("\n" + "="*70)
    print("PHASE 2: CROSS-CLUSTER EVIDENCE COLLECTION (STRONG PII)")
    print("="*70)
    
    phase2_stats = defaultdict(int)
    
    # Create party to cluster mapping for quick lookup
    party_to_cluster = dict(zip(cluster_df['party_id'], cluster_df['cluster_id']))
    
    # Define strong PII blocking keys
    blocking_keys = [
        ('SUB_HKID', 'EXACT_HKID'),
        ('SUB_PASSPORT', 'EXACT_PASSPORT'),
        ('ATTR_EMAIL', 'EXACT_EMAIL'),  # Use ATTR_EMAIL not SUB_EMAIL (generic subtype)
        ('ATTR_DOB', 'EXACT_DOB')  # Added for cross-cluster matching on date of birth
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
                
                # Collect all evidence
                match_evs, diff_evs, eval_complete = collect_pair_evidence(
                    party1_id, party2_id, attrs1, attrs2,
                    std_attr_df, raw_attr_df, evidence_rules_df, metadata_column_df
                )
                
                # Update blocking keys for phase 2
                for match_ev in match_evs:
                    match_ev['blocking_keys'] = blocking_key_name
                
                # Track statistics
                if diff_evs and any(d['is_hard_block'] for d in diff_evs):
                    phase2_stats[f'{blocking_key_name}_hard_blocked'] += 1
                elif match_evs:
                    phase2_stats[f'{blocking_key_name}_matches'] += 1
                if diff_evs:
                    phase2_stats[f'{blocking_key_name}_differences'] += 1
                
                # Store evidence
                match_records.extend(match_evs)
                difference_records.extend(diff_evs)
        
        print(f"    Candidate pairs: {candidates_found}")
        print(f"    Skipped (same cluster): {pairs_skipped_same_cluster}")
        print(f"    Skipped (already seen): {pairs_skipped_seen}")
        print(f"    New pairs compared: {pairs_compared}")
    
    # Overall Phase 2 stats
    total_matches = sum(v for k, v in phase2_stats.items() if '_matches' in k)
    total_differences = sum(v for k, v in phase2_stats.items() if '_differences' in k)
    total_hard_blocked = sum(v for k, v in phase2_stats.items() if '_hard_blocked' in k)
    
    print(f"\n✓ Phase 2 Complete:")
    print(f"  Pairs with matches: {total_matches}")
    print(f"  Pairs with differences: {total_differences}")
    print(f"  Hard blocked pairs: {total_hard_blocked}")
    
    return match_records, difference_records


def export_evidence_data(match_evidence_df, difference_evidence_df, output_dir='data/silver'):
    """Export MATCH_EVIDENCE and DIFFERENCE_EVIDENCE to CSV"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / output_dir
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    match_file = silver_dir / 'match_evidence.csv'
    diff_file = silver_dir / 'difference_evidence.csv'
    
    match_evidence_df.to_csv(match_file, index=False)
    difference_evidence_df.to_csv(diff_file, index=False)
    
    print(f"\n✓ Exported to:")
    print(f"  {match_file}")
    print(f"  {diff_file}")


def main():
    print("="*70)
    print("EVIDENCE COLLECTION - MATCH & DIFFERENCE")
    print("="*70)
    
    # Load data
    cluster_df, std_attr_df, raw_attr_df, source_party_df, evidence_rules_df, metadata_column_df = load_data()
    
    # Phase 1: Within-cluster evidence collection
    match_records, difference_records, seen_pairs = generate_phase1_evidence(
        cluster_df, std_attr_df, raw_attr_df, source_party_df, evidence_rules_df, metadata_column_df
    )
    
    # Phase 2: Cross-cluster evidence collection (strong PII)
    match_records, difference_records = generate_phase2_evidence(
        cluster_df, std_attr_df, raw_attr_df, match_records, difference_records, 
        seen_pairs, evidence_rules_df, metadata_column_df
    )
    
    # Convert to DataFrames
    match_evidence_df = pd.DataFrame(match_records)
    difference_evidence_df = pd.DataFrame(difference_records)
    
    print(f"\n✓ Total Evidence Collected:")
    print(f"  Match evidence: {len(match_evidence_df)}")
    print(f"  Difference evidence: {len(difference_evidence_df)}")
    print(f"  Hard blocks: {len(difference_evidence_df[difference_evidence_df['is_hard_block'] == True]) if len(difference_evidence_df) > 0 else 0}")
    
    # Export
    export_evidence_data(match_evidence_df, difference_evidence_df)
    
    print("\n" + "="*70)
    print("✅ EVIDENCE COLLECTION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
