"""
Entity Resolution - Gold Layer

Implements entity resolution with transitive conflict detection:

1. Build candidate entities from MATCH_EVIDENCE (graph clustering)
2. Check ALL pairs within each candidate for transitive conflicts
3. Resolve conflicts by splitting entities or flagging for review
4. Generate final MASTER_ENTITY and PARTY_TO_ENTITY_LINK tables

Transitive Conflict Example:
  Party A (HKID: X123456) ←→ Party B (HKID: null) ←→ Party C (HKID: Y123456)
  - A<>B: ✓ no conflict (B has null HKID)
  - B<>C: ✓ no conflict (B has null HKID)
  - A<>C: ✗ BLOCKED (different HKIDs) - TRANSITIVE CONFLICT
  
This algorithm catches the A<>C conflict even though they were never directly compared.

Algorithm:
1. Build graph from MATCH_EVIDENCE
2. Find connected components → candidate entities
3. For each candidate entity:
   - Get all parties in entity
   - Check ALL pairs against MATCH_BLOCKING (direct + transitive)
   - If conflict found:
     * Remove conflicting edge with lowest confidence
     * Re-cluster to split entity
   - Repeat until no conflicts
4. Generate MASTER_ENTITY and PARTY_TO_ENTITY_LINK
"""

import pandas as pd
import networkx as nx
from pathlib import Path
from datetime import datetime
import uuid
from itertools import combinations
from collections import defaultdict


def load_data():
    """Load Silver layer evidence and metadata for scoring"""
    project_root = Path(__file__).parent.parent.parent
    bronze_dir = project_root / 'data/bronze'
    silver_dir = project_root / 'data/silver'
    metadata_dir = project_root / 'data/uat_generation/metadata'
    
    print("Loading evidence and metadata...")
    
    source_party = pd.read_csv(bronze_dir / 'source_party.csv')
    match_evidence = pd.read_csv(silver_dir / 'match_evidence.csv')
    difference_evidence = pd.read_csv(silver_dir / 'difference_evidence.csv')
    standardized_attr = pd.read_csv(silver_dir / 'standardized_attribute.csv')
    relationships = pd.read_csv(bronze_dir / 'relationship.csv')
    evidence_rules = pd.read_csv(metadata_dir / 'metadata_evidence_rule.csv')
    metadata_relationship = pd.read_csv(metadata_dir / 'metadata_relationship.csv')
    
    print(f"  ✓ Loaded {len(source_party)} SOURCE_PARTY records")
    print(f"  ✓ Loaded {len(match_evidence)} MATCH_EVIDENCE records")
    print(f"  ✓ Loaded {len(difference_evidence)} DIFFERENCE_EVIDENCE records")
    print(f"  ✓ Loaded {len(standardized_attr)} STANDARDIZED_ATTRIBUTE records")
    print(f"  ✓ Loaded {len(relationships)} RELATIONSHIP records")
    print(f"  ✓ Loaded {len(evidence_rules)} METADATA_EVIDENCE_RULE records")
    print(f"  ✓ Loaded {len(metadata_relationship)} METADATA_RELATIONSHIP records")
    
    return (source_party, match_evidence, difference_evidence, standardized_attr, 
            relationships, evidence_rules, metadata_relationship)


def compute_pair_score(party1_id, party2_id, match_evidence_df, difference_evidence_df, 
                       relationships_df, evidence_rules_df, metadata_relationship_df):
    """
    Compute aggregate score for a pair based on all evidence types.
    
    Returns: (decision, score, reason)
    decision: 'MUST_NOT_MERGE' | 'MUST_MERGE' | 'MERGE' | 'NO_MERGE'
    """
    # Get evidence for this pair
    pair_matches = match_evidence_df[
        ((match_evidence_df['party_id_1'] == party1_id) & (match_evidence_df['party_id_2'] == party2_id)) |
        ((match_evidence_df['party_id_1'] == party2_id) & (match_evidence_df['party_id_2'] == party1_id))
    ]
    
    pair_differences = difference_evidence_df[
        ((difference_evidence_df['party_id_1'] == party1_id) & (difference_evidence_df['party_id_2'] == party2_id)) |
        ((difference_evidence_df['party_id_1'] == party2_id) & (difference_evidence_df['party_id_2'] == party1_id))
    ]
    
    pair_relationships = relationships_df[
        ((relationships_df['from_party_id'] == party1_id) & (relationships_df['to_party_id'] == party2_id)) |
        ((relationships_df['from_party_id'] == party2_id) & (relationships_df['to_party_id'] == party1_id))
    ]
    
    # Priority 1: Hard blocks (severity=1.0)
    hard_blocks = pair_differences[pair_differences['is_hard_block'] == True]
    if len(hard_blocks) > 0:
        attr = hard_blocks.iloc[0]['attribute_subtype_id']
        return ('MUST_NOT_MERGE', 0.0, f'Hard block: {attr}')
    
    # Priority 2: Hard links from match evidence (confidence=1.0)
    hard_matches = pair_matches[pair_matches['confidence_score'] == 1.0]
    if len(hard_matches) > 0:
        attr = hard_matches.iloc[0]['match_key']
        return ('MUST_MERGE', 1.0, f'Hard link: {attr}')
    
    # Priority 2b: Hard links from relationships (guarantees_same_party=True, confidence=1.0)
    for _, rel in pair_relationships.iterrows():
        rel_meta = metadata_relationship_df[
            metadata_relationship_df['relationship_id'] == rel['metadata_relationship_id']
        ]
        if len(rel_meta) > 0:
            meta = rel_meta.iloc[0]
            if meta.get('guarantees_same_party') and meta.get('confidence_score') == 1.0:
                return ('MUST_MERGE', 1.0, f'Hard link: Relationship {rel["metadata_relationship_id"]}')
    
    # Priority 3: Aggregate scoring
    rules_dict = {row['attribute_subtype_id']: row for _, row in evidence_rules_df.iterrows()}
    
    match_score = 0.0
    for _, match in pair_matches.iterrows():
        # Use match_weight from rules
        attr = match['match_key']
        if attr in rules_dict:
            weight = rules_dict[attr].get('match_weight', 0.0)
            match_score += match['confidence_score'] * weight
    
    # Add relationship score if exists
    for _, rel in pair_relationships.iterrows():
        rel_meta = metadata_relationship_df[
            metadata_relationship_df['relationship_id'] == rel['metadata_relationship_id']
        ]
        if len(rel_meta) > 0:
            meta = rel_meta.iloc[0]
            conf = meta.get('confidence_score', 0.0)
            if conf < 1.0:  # Soft relationships
                match_score += conf * 0.3  # Relationship weight
    
    penalty_score = 0.0
    for _, diff in pair_differences.iterrows():
        attr = diff['attribute_subtype_id']
        if attr in rules_dict:
            severity = diff['severity_score']
            penalty_score += severity
    
    # Normalize to [0, 1]
    max_possible = sum(rules_dict[attr]['match_weight'] for attr in rules_dict if rules_dict[attr]['match_weight'] > 0)
    if max_possible == 0:
        max_possible = 1.0
    
    raw_score = (match_score - penalty_score) / max_possible
    final_score = max(0.0, min(1.0, raw_score))
    
    # Decision based on threshold
    MERGE_THRESHOLD = 0.5  # Configurable
    
    if final_score >= MERGE_THRESHOLD:
        return ('MERGE', final_score, f'Score {final_score:.2f} >= threshold')
    else:
        return ('NO_MERGE', final_score, f'Score {final_score:.2f} < threshold')


def build_candidate_entities(match_evidence_df, difference_evidence_df, relationships_df,
                             evidence_rules_df, metadata_relationship_df, all_party_ids):
    """
    Build candidate entities using scoring-based graph clustering.
    Only create edges for pairs that should merge based on aggregate scores.
    
    Returns: dict of {entity_id: [party_ids]}
    """
    print("\n" + "="*70)
    print("BUILDING ENTITIES WITH SCORING-BASED CLUSTERING")
    print("="*70)
    
    # Create graph
    G = nx.Graph()
    
    # Add all parties as nodes (ensures singletons are included)
    G.add_nodes_from(all_party_ids)
    
    # Get all unique pairs with any evidence (only for parties with attributes)
    all_party_ids_set = set(all_party_ids)
    pairs_with_evidence = set()
    
    for _, row in match_evidence_df.iterrows():
        p1, p2 = row['party_id_1'], row['party_id_2']
        if p1 in all_party_ids_set and p2 in all_party_ids_set:
            pair = tuple(sorted([p1, p2]))
            pairs_with_evidence.add(pair)
    
    for _, row in difference_evidence_df.iterrows():
        p1, p2 = row['party_id_1'], row['party_id_2']
        if p1 in all_party_ids_set and p2 in all_party_ids_set:
            pair = tuple(sorted([p1, p2]))
            pairs_with_evidence.add(pair)
    
    for _, row in relationships_df.iterrows():
        p1, p2 = row['from_party_id'], row['to_party_id']
        # Only include if BOTH parties have attributes (exclude business objects)
        if p1 in all_party_ids_set and p2 in all_party_ids_set:
            pair = tuple(sorted([p1, p2]))
            pairs_with_evidence.add(pair)
    
    # Score each pair and decide whether to create edge
    decision_stats = defaultdict(int)
    
    for party1_id, party2_id in pairs_with_evidence:
        decision, score, reason = compute_pair_score(
            party1_id, party2_id, match_evidence_df, difference_evidence_df,
            relationships_df, evidence_rules_df, metadata_relationship_df
        )
        
        decision_stats[decision] += 1
        
        # Only create edge if should merge
        if decision in ['MUST_MERGE', 'MERGE']:
            G.add_edge(party1_id, party2_id, weight=score, decision=decision, reason=reason)
    
    # Find connected components (includes isolated nodes as singletons)
    components = list(nx.connected_components(G))
    
    # Create candidate entities
    candidate_entities = {}
    for i, component in enumerate(components):
        entity_id = f"ENTITY_{i+1:04d}"
        candidate_entities[entity_id] = sorted(list(component))
    
    print(f"\n✓ Scoring decisions:")
    print(f"  MUST_MERGE (hard links): {decision_stats.get('MUST_MERGE', 0)}")
    print(f"  MERGE (scored >= threshold): {decision_stats.get('MERGE', 0)}")
    print(f"  NO_MERGE (scored < threshold): {decision_stats.get('NO_MERGE', 0)}")
    print(f"  MUST_NOT_MERGE (hard blocks): {decision_stats.get('MUST_NOT_MERGE', 0)}")
    
    print(f"\n✓ Created {len(candidate_entities)} entities")
    print(f"  Total parties in entities: {sum(len(parties) for parties in candidate_entities.values())}")
    print(f"  Largest entity: {max(len(parties) for parties in candidate_entities.values())} parties")
    print(f"  Singleton entities: {sum(1 for parties in candidate_entities.values() if len(parties) == 1)}")
    
    return candidate_entities, G, decision_stats


def get_party_attributes(party_id, std_attr_df):
    """Get all attributes for a party as dict"""
    party_attrs = std_attr_df[std_attr_df['source_party_id'] == party_id]
    attr_dict = {}
    for _, row in party_attrs.iterrows():
        attr_dict[row['attribute_subtype_id']] = row['standardized_value']
    return attr_dict


def check_blocking_pair(party1_id, party2_id, std_attr_df, blocking_rules_df):
    """
    Check if a specific pair should be blocked based on blocking rules.
    Returns: (is_blocked, blocking_rule_id, blocking_reason, conflict_details)
    """
    attrs1 = get_party_attributes(party1_id, std_attr_df)
    attrs2 = get_party_attributes(party2_id, std_attr_df)
    
    # Check active blocking rules
    active_rules = blocking_rules_df[blocking_rules_df['is_active'] == True].sort_values('priority', ascending=False)
    
    for _, rule in active_rules.iterrows():
        attribute_subtype = rule['attribute_subtype_id']
        blocking_logic = rule['blocking_logic']
        
        value1 = attrs1.get(attribute_subtype)
        value2 = attrs2.get(attribute_subtype)
        
        if not value1 or not value2:
            continue
        
        if blocking_logic == 'DIFFERENT_VALUES':
            if value1 != value2:
                # Special handling for gender - need matching names
                if attribute_subtype == 'SUB_GENDER':
                    fname1 = attrs1.get('SUB_FIRST_NAME')
                    fname2 = attrs2.get('SUB_FIRST_NAME')
                    lname1 = attrs1.get('SUB_LAST_NAME')
                    lname2 = attrs2.get('SUB_LAST_NAME')
                    
                    if (fname1 and fname2 and fname1 == fname2 and
                        lname1 and lname2 and lname1 == lname2):
                        return True, rule['blocking_rule_id'], 'GENDER_CONFLICT', {
                            'party1_gender': value1,
                            'party2_gender': value2,
                            'shared_name': f"{fname1} {lname1}"
                        }
                else:
                    return True, rule['blocking_rule_id'], rule['rule_name'].upper().replace('_BLOCKS_MATCH', ''), {
                        f'party1_{attribute_subtype}': value1,
                        f'party2_{attribute_subtype}': value2
                    }
    
    return False, None, None, None


def detect_transitive_conflicts(candidate_id, party_ids, std_attr_df, blocking_rules_df, match_blocking_df):
    """
    Check ALL pairs within a candidate entity for conflicts (direct + transitive).
    
    Returns: list of (party1_id, party2_id, conflict_type, blocking_rule_id, conflict_details)
    """
    conflicts = []
    
    # Check all pairs in entity
    all_pairs = list(combinations(party_ids, 2))
    
    for party1_id, party2_id in all_pairs:
        # Normalize pair order for matching
        pair_key = tuple(sorted([party1_id, party2_id]))
        
        # Check if already in MATCH_BLOCKING (direct conflict)
        existing_block = match_blocking_df[
            (((match_blocking_df['party_id_1'] == pair_key[0]) & (match_blocking_df['party_id_2'] == pair_key[1])) |
             ((match_blocking_df['party_id_1'] == pair_key[1]) & (match_blocking_df['party_id_2'] == pair_key[0]))) &
            (match_blocking_df['is_active'] == True)
        ]
        
        if len(existing_block) > 0:
            # Direct conflict (already detected during match evidence)
            block = existing_block.iloc[0]
            conflicts.append((
                party1_id,
                party2_id,
                'DIRECT',
                block['blocking_rule_id'],
                block['conflict_details']
            ))
        else:
            # Check for transitive conflict (not yet in MATCH_BLOCKING)
            is_blocked, blocking_rule_id, blocking_reason, conflict_details = check_blocking_pair(
                party1_id, party2_id, std_attr_df, blocking_rules_df
            )
            
            if is_blocked:
                conflicts.append((
                    party1_id,
                    party2_id,
                    'TRANSITIVE',
                    blocking_rule_id,
                    conflict_details
                ))
    
    return conflicts


def resolve_conflicts(candidate_id, party_ids, conflicts, entity_graph):
    """
    Resolve conflicts by removing edges and splitting entity.
    
    Strategy: Remove edge with lowest confidence that participates in conflict.
    """
    if not conflicts:
        return [party_ids]  # No conflicts, entity is valid
    
    # Create subgraph for this entity
    subgraph = entity_graph.subgraph(party_ids).copy()
    
    # Remove edges involved in conflicts (lowest confidence first)
    for party1, party2, conflict_type, rule_id, details in conflicts:
        if subgraph.has_edge(party1, party2):
            # Direct edge in conflict
            subgraph.remove_edge(party1, party2)
        else:
            # Transitive conflict - need to break path
            # Find shortest path and remove lowest confidence edge in path
            try:
                path = nx.shortest_path(subgraph, party1, party2)
                # Find edge in path with lowest confidence
                min_weight = float('inf')
                min_edge = None
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    if subgraph.has_edge(u, v):
                        weight = subgraph[u][v]['weight']
                        if weight < min_weight:
                            min_weight = weight
                            min_edge = (u, v)
                
                if min_edge:
                    subgraph.remove_edge(*min_edge)
            except nx.NetworkXNoPath:
                # Already disconnected
                pass
    
    # Re-cluster after removing edges
    new_components = list(nx.connected_components(subgraph))
    split_entities = [sorted(list(comp)) for comp in new_components]
    
    return split_entities


def resolve_entities_with_conflicts(candidate_entities, entity_graph, std_attr_df, blocking_rules_df, match_blocking_df):
    """
    Resolve all candidate entities, handling transitive conflicts.
    
    Returns: (resolved_entities, conflict_stats, new_blocking_records)
    """
    print("\n" + "="*70)
    print("DETECTING AND RESOLVING TRANSITIVE CONFLICTS")
    print("="*70)
    
    resolved_entities = {}
    conflict_stats = defaultdict(int)
    new_blocking_records = []
    entity_counter = 1
    
    for candidate_id, party_ids in candidate_entities.items():
        if len(party_ids) == 1:
            # Singleton - no conflicts possible
            entity_id = f"ENTITY_{entity_counter:04d}"
            resolved_entities[entity_id] = party_ids
            entity_counter += 1
            conflict_stats['singleton_entities'] += 1
            continue
        
        # Detect conflicts (direct + transitive)
        conflicts = detect_transitive_conflicts(
            candidate_id, party_ids, std_attr_df, blocking_rules_df, match_blocking_df
        )
        
        if not conflicts:
            # No conflicts - entity is valid
            entity_id = f"ENTITY_{entity_counter:04d}"
            resolved_entities[entity_id] = party_ids
            entity_counter += 1
            conflict_stats['clean_entities'] += 1
        else:
            # Has conflicts - resolve by splitting
            conflict_stats['entities_with_conflicts'] += 1
            conflict_stats['total_conflicts'] += len(conflicts)
            
            # Count transitive vs direct
            for _, _, conflict_type, _, _ in conflicts:
                if conflict_type == 'TRANSITIVE':
                    conflict_stats['transitive_conflicts'] += 1
                else:
                    conflict_stats['direct_conflicts'] += 1
            
            # Record new transitive blocking records
            for party1, party2, conflict_type, blocking_rule_id, conflict_details in conflicts:
                if conflict_type == 'TRANSITIVE':
                    new_blocking_records.append({
                        'blocking_id': str(uuid.uuid4()),
                        'party_id_1': party1,
                        'party_id_2': party2,
                        'blocking_reason_code': 'TRANSITIVE_CONFLICT',
                        'blocking_rule_id': blocking_rule_id,
                        'blocking_source': 'AUTOMATIC_TRANSITIVE',
                        'conflicting_attribute_subtype_id': list(conflict_details.keys())[0].replace('party1_', '').replace('party2_', '') if conflict_details else None,
                        'conflict_details': str(conflict_details),
                        'created_at': datetime.now().isoformat(),
                        'is_active': True,
                        'created_by': 'ENTITY_RESOLUTION'
                    })
            
            # Resolve by splitting
            split_entities = resolve_conflicts(candidate_id, party_ids, conflicts, entity_graph)
            
            for split_parties in split_entities:
                entity_id = f"ENTITY_{entity_counter:04d}"
                resolved_entities[entity_id] = split_parties
                entity_counter += 1
            
            conflict_stats['entities_after_split'] += len(split_entities)
    
    print(f"\n✓ Entity Resolution Complete:")
    print(f"  Candidate entities: {len(candidate_entities)}")
    print(f"  Final entities: {len(resolved_entities)}")
    print(f"  Singleton entities: {conflict_stats.get('singleton_entities', 0)}")
    print(f"  Clean multi-party entities: {conflict_stats.get('clean_entities', 0)}")
    print(f"  Entities with conflicts: {conflict_stats.get('entities_with_conflicts', 0)}")
    print(f"  Total conflicts detected: {conflict_stats.get('total_conflicts', 0)}")
    print(f"    - Direct conflicts: {conflict_stats.get('direct_conflicts', 0)}")
    print(f"    - Transitive conflicts: {conflict_stats.get('transitive_conflicts', 0)}")
    print(f"  Entities after splitting: {conflict_stats.get('entities_after_split', 0)}")
    print(f"  New transitive blocking records: {len(new_blocking_records)}")
    
    return resolved_entities, conflict_stats, new_blocking_records


def compute_entity_analytics(entity_id, party_ids, std_attr_df, match_evidence_df, difference_evidence_df):
    """
    Compute entity analytics with dual scoring views.
    
    Attribute-based metrics (analytics & sanity checks):
    - Entity size: party_count, total_pairs
    - Attribute coverage: unique_attributes, total_attribute_instances
    - Attribute quality: fully_matching_attributes, contradicting_attributes
    - Score distribution: avg_pair_score, min_pair_score, max_pair_score
    
    Evidence-based metrics (audit trail for decision logic):
    - Evidence counts: total_match_evidence, total_difference_evidence
    - Evidence quality: evidence_match_ratio, avg_evidence_ratio_per_pair
    """
    analytics = {
        # Attribute-based metrics
        'total_pairs': 0,
        'unique_attributes': 0,
        'total_attribute_instances': 0,
        'fully_matching_attributes': 0,
        'contradicting_attributes': 0,
        'avg_pair_score': 0.0,
        'min_pair_score': 1.0,
        'max_pair_score': 0.0,
        # Evidence-based metrics
        'total_match_evidence': 0,
        'total_difference_evidence': 0,
        'evidence_match_ratio': 0.0,
        'avg_evidence_ratio_per_pair': 0.0
    }
    
    if len(party_ids) == 1:
        # Singleton entity - no pairs to analyze
        party_attrs = std_attr_df[std_attr_df['source_party_id'] == party_ids[0]]
        analytics['unique_attributes'] = party_attrs['attribute_subtype_id'].nunique()
        analytics['total_attribute_instances'] = len(party_attrs)
        return analytics
    
    # Get all attributes for all parties in entity (vectorized)
    entity_attrs = std_attr_df[std_attr_df['source_party_id'].isin(party_ids)]
    analytics['unique_attributes'] = entity_attrs['attribute_subtype_id'].nunique()
    analytics['total_attribute_instances'] = len(entity_attrs)
    
    # Build attribute map: {party_id: {attr_subtype: value}}
    party_attr_map = {}
    for party_id in party_ids:
        party_attrs = entity_attrs[entity_attrs['source_party_id'] == party_id]
        party_attr_map[party_id] = {
            row['attribute_subtype_id']: row['standardized_value']
            for _, row in party_attrs.iterrows()
        }
    
    # Analyze all pairs
    pair_scores = []
    pair_evidence_ratios = []
    from itertools import combinations
    
    for party1_id, party2_id in combinations(party_ids, 2):
        analytics['total_pairs'] += 1
        
        # ATTRIBUTE-BASED: Compute attribute-level match score for this pair
        attrs1 = party_attr_map.get(party1_id, {})
        attrs2 = party_attr_map.get(party2_id, {})
        
        # Common attributes (both parties have)
        common_attrs = set(attrs1.keys()) & set(attrs2.keys())
        
        if len(common_attrs) > 0:
            matching = sum(1 for attr in common_attrs if attrs1[attr] == attrs2[attr])
            pair_score = matching / len(common_attrs)
            pair_scores.append(pair_score)
        
        # EVIDENCE-BASED: Count match and difference evidence for this pair
        pair_matches = match_evidence_df[
            (((match_evidence_df['party_id_1'] == party1_id) & (match_evidence_df['party_id_2'] == party2_id)) |
             ((match_evidence_df['party_id_1'] == party2_id) & (match_evidence_df['party_id_2'] == party1_id)))
        ]
        pair_diffs = difference_evidence_df[
            (((difference_evidence_df['party_id_1'] == party1_id) & (difference_evidence_df['party_id_2'] == party2_id)) |
             ((difference_evidence_df['party_id_1'] == party2_id) & (difference_evidence_df['party_id_2'] == party1_id)))
        ]
        
        num_matches = len(pair_matches)
        num_diffs = len(pair_diffs)
        analytics['total_match_evidence'] += num_matches
        analytics['total_difference_evidence'] += num_diffs
        
        # Calculate evidence ratio for this pair
        if num_matches + num_diffs > 0:
            pair_evidence_ratio = num_matches / (num_matches + num_diffs)
            pair_evidence_ratios.append(pair_evidence_ratio)
    
    # Compute aggregate attribute-based scores
    if pair_scores:
        analytics['avg_pair_score'] = sum(pair_scores) / len(pair_scores)
        analytics['min_pair_score'] = min(pair_scores)
        analytics['max_pair_score'] = max(pair_scores)
    
    # Compute aggregate evidence-based scores
    total_evidence = analytics['total_match_evidence'] + analytics['total_difference_evidence']
    if total_evidence > 0:
        analytics['evidence_match_ratio'] = analytics['total_match_evidence'] / total_evidence
    
    if pair_evidence_ratios:
        analytics['avg_evidence_ratio_per_pair'] = sum(pair_evidence_ratios) / len(pair_evidence_ratios)
    
    # Compute attribute-level metrics across all parties
    # For each attribute type, check if all parties agree
    attribute_stats = defaultdict(lambda: {'values': set(), 'count': 0})
    
    for party_id in party_ids:
        attrs = party_attr_map.get(party_id, {})
        for attr_type, value in attrs.items():
            attribute_stats[attr_type]['values'].add(value)
            attribute_stats[attr_type]['count'] += 1
    
    # Count fully matching vs contradicting attributes
    for attr_type, stats in attribute_stats.items():
        if len(stats['values']) == 1:
            # All parties agree on this attribute
            analytics['fully_matching_attributes'] += 1
        elif len(stats['values']) > 1:
            # Contradiction - different values for same attribute type
            analytics['contradicting_attributes'] += 1
    
    return analytics


def generate_master_entities(resolved_entities, std_attr_df, match_evidence_df, difference_evidence_df):
    """Generate MASTER_ENTITY table with comprehensive analytics"""
    master_entities = []
    
    print("\nComputing entity analytics...")
    
    for entity_id, party_ids in resolved_entities.items():
        # Compute analytics for this entity
        analytics = compute_entity_analytics(
            entity_id, party_ids, std_attr_df, match_evidence_df, difference_evidence_df
        )
        
        master_entities.append({
            'master_entity_id': entity_id,
            'party_count': len(party_ids),
            'total_pairs': analytics['total_pairs'],
            # Attribute-based analytics (sanity checks)
            'unique_attributes': analytics['unique_attributes'],
            'total_attribute_instances': analytics['total_attribute_instances'],
            'fully_matching_attributes': analytics['fully_matching_attributes'],
            'contradicting_attributes': analytics['contradicting_attributes'],
            'avg_pair_score': round(analytics['avg_pair_score'], 4),
            'min_pair_score': round(analytics['min_pair_score'], 4),
            'max_pair_score': round(analytics['max_pair_score'], 4),
            # Evidence-based analytics (decision audit)
            'total_match_evidence': analytics['total_match_evidence'],
            'total_difference_evidence': analytics['total_difference_evidence'],
            'evidence_match_ratio': round(analytics['evidence_match_ratio'], 4),
            'avg_evidence_ratio_per_pair': round(analytics['avg_evidence_ratio_per_pair'], 4),
            # Metadata
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True
        })
    
    print(f"  ✓ Computed analytics for {len(master_entities)} entities")
    
    return pd.DataFrame(master_entities)


def generate_party_to_entity_links(resolved_entities, entity_graph, match_evidence_df, 
                                    difference_evidence_df, relationships_df,
                                    evidence_rules_df, metadata_relationship_df):
    """Generate PARTY_TO_ENTITY_LINK table with actual scoring information"""
    links = []
    
    for entity_id, party_ids in resolved_entities.items():
        for party_id in party_ids:
            # For singleton entities
            if len(party_ids) == 1:
                links.append({
                    'link_id': str(uuid.uuid4()),
                    'party_id': party_id,
                    'master_entity_id': entity_id,
                    'link_type': 'SINGLETON',
                    'link_decision': 'SINGLETON',
                    'confidence_score': 1.0,
                    'avg_score_with_peers': None,
                    'best_score_with_peer': None,
                    'num_matches': 0,
                    'num_differences': 0,
                    'num_hard_blocks': 0,
                    'attribute_match_ratio': None,
                    'created_at': datetime.now().isoformat(),
                    'rec_start_date': datetime.now().isoformat(),
                    'rec_end_date': None,
                    'is_current': True
                })
                continue
            
            # For multi-party entities: compute scores with all peers
            peer_scores = []
            peer_decisions = []
            num_matches = 0
            num_differences = 0
            num_hard_blocks = 0
            
            for peer_id in party_ids:
                if peer_id == party_id:
                    continue
                
                # Compute score with this peer
                decision, score, reason = compute_pair_score(
                    party_id, peer_id, match_evidence_df, difference_evidence_df,
                    relationships_df, evidence_rules_df, metadata_relationship_df
                )
                
                peer_scores.append(score)
                peer_decisions.append(decision)
                
                # Count evidence
                pair_matches = match_evidence_df[
                    (((match_evidence_df['party_id_1'] == party_id) & (match_evidence_df['party_id_2'] == peer_id)) |
                     ((match_evidence_df['party_id_1'] == peer_id) & (match_evidence_df['party_id_2'] == party_id)))
                ]
                num_matches += len(pair_matches)
                
                pair_diffs = difference_evidence_df[
                    (((difference_evidence_df['party_id_1'] == party_id) & (difference_evidence_df['party_id_2'] == peer_id)) |
                     ((difference_evidence_df['party_id_1'] == peer_id) & (difference_evidence_df['party_id_2'] == party_id)))
                ]
                num_differences += len(pair_diffs)
                num_hard_blocks += len(pair_diffs[pair_diffs['is_hard_block'] == True])
            
            # Determine primary link decision
            if 'MUST_MERGE' in peer_decisions:
                link_decision = 'MUST_MERGE'
                link_type = 'HARD_LINK'
            elif 'MERGE' in peer_decisions:
                link_decision = 'MERGE'
                link_type = 'SCORED'
            else:
                link_decision = 'UNKNOWN'
                link_type = 'MATCH_EVIDENCE'
            
            # Calculate aggregate confidence
            avg_score = sum(peer_scores) / len(peer_scores) if peer_scores else 0.0
            best_score = max(peer_scores) if peer_scores else 0.0
            
            # Calculate attribute match ratio (data quality indicator)
            total_evidence = num_matches + num_differences
            attribute_match_ratio = num_matches / total_evidence if total_evidence > 0 else None
            
            links.append({
                'link_id': str(uuid.uuid4()),
                'party_id': party_id,
                'master_entity_id': entity_id,
                'link_type': link_type,
                'link_decision': link_decision,
                'confidence_score': round(best_score, 4),  # Best score with any peer
                'avg_score_with_peers': round(avg_score, 4),
                'best_score_with_peer': round(best_score, 4),
                'num_matches': num_matches,
                'num_differences': num_differences,
                'num_hard_blocks': num_hard_blocks,
                'attribute_match_ratio': round(attribute_match_ratio, 4) if attribute_match_ratio is not None else None,
                'created_at': datetime.now().isoformat(),
                'rec_start_date': datetime.now().isoformat(),
                'rec_end_date': None,
                'is_current': True
            })
    
    return pd.DataFrame(links)


def export_gold_tables(master_entity_df, party_link_df, output_dir='data/gold'):
    """Export Gold layer tables"""
    project_root = Path(__file__).parent.parent.parent
    gold_dir = project_root / output_dir
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    master_entity_file = gold_dir / 'master_entity.csv'
    party_link_file = gold_dir / 'party_to_entity_link.csv'
    
    master_entity_df.to_csv(master_entity_file, index=False)
    party_link_df.to_csv(party_link_file, index=False)
    
    print(f"\n✓ Exported to:")
    print(f"  {master_entity_file}")
    print(f"  {party_link_file}")


def main():
    print("="*70)
    print("ENTITY RESOLUTION WITH SCORING-BASED CLUSTERING")
    print("="*70)
    
    # Load data
    (source_party_df, match_evidence_df, difference_evidence_df, std_attr_df,
     relationships_df, evidence_rules_df, metadata_relationship_df) = load_data()
    
    # Get only parties with attributes (exclude business objects)
    parties_with_attrs = std_attr_df['source_party_id'].unique().tolist()
    all_party_ids = source_party_df['source_party_id'].unique().tolist()
    
    print(f"\n  Total parties in SOURCE_PARTY: {len(all_party_ids)}")
    print(f"  Parties with attributes (persons): {len(parties_with_attrs)}")
    print(f"  Parties without attributes (business objects): {len(all_party_ids) - len(parties_with_attrs)}")
    print(f"  → Creating entities only for parties with attributes")
    
    # Build entities using scoring-based clustering (only for parties with attributes)
    entities, entity_graph, decision_stats = build_candidate_entities(
        match_evidence_df, difference_evidence_df, relationships_df,
        evidence_rules_df, metadata_relationship_df, parties_with_attrs
    )
    
    # Generate Gold layer tables with analytics
    master_entity_df = generate_master_entities(
        entities, std_attr_df, match_evidence_df, difference_evidence_df
    )
    party_link_df = generate_party_to_entity_links(
        entities, entity_graph, match_evidence_df, difference_evidence_df,
        relationships_df, evidence_rules_df, metadata_relationship_df
    )
    
    print(f"\n  Verification: {len(party_link_df)} party-to-entity links for {len(parties_with_attrs)} parties with attributes")
    if len(party_link_df) != len(parties_with_attrs):
        print(f"  ⚠️  WARNING: Missing {len(parties_with_attrs) - len(party_link_df)} parties!")
    else:
        print(f"  ✅ All parties with attributes have entity assignments")
    
    # Export
    export_gold_tables(master_entity_df, party_link_df)
    
    print("\n" + "="*70)
    print("✅ ENTITY RESOLUTION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
