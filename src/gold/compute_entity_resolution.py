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
    """Load Silver layer match evidence and blocking data"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / 'data/silver'
    metadata_dir = project_root / 'data/uat_generation/metadata'
    
    print("Loading match evidence and blocking data...")
    
    match_evidence = pd.read_csv(silver_dir / 'match_evidence.csv')
    match_blocking = pd.read_csv(silver_dir / 'match_blocking.csv')
    standardized_attr = pd.read_csv(silver_dir / 'standardized_attribute.csv')
    blocking_rules = pd.read_csv(metadata_dir / 'metadata_blocking_rule.csv')
    
    print(f"  ✓ Loaded {len(match_evidence)} MATCH_EVIDENCE records")
    print(f"  ✓ Loaded {len(match_blocking)} MATCH_BLOCKING records")
    print(f"  ✓ Loaded {len(standardized_attr)} STANDARDIZED_ATTRIBUTE records")
    print(f"  ✓ Loaded {len(blocking_rules)} METADATA_BLOCKING_RULE records")
    
    return match_evidence, match_blocking, standardized_attr, blocking_rules


def build_candidate_entities(match_evidence_df):
    """
    Build candidate entities from match evidence using graph clustering.
    
    Returns: dict of {entity_id: [party_ids]}
    """
    print("\n" + "="*70)
    print("BUILDING CANDIDATE ENTITIES FROM MATCH EVIDENCE")
    print("="*70)
    
    # Create graph
    G = nx.Graph()
    
    # Add edges from match evidence
    for _, row in match_evidence_df.iterrows():
        party1 = row['party_id_1']
        party2 = row['party_id_2']
        confidence = row['confidence_score']
        rule_id = row['match_rule_id']
        
        # Add edge with weight = confidence
        if G.has_edge(party1, party2):
            # Multiple evidence for same pair - keep highest confidence
            current_weight = G[party1][party2]['weight']
            if confidence > current_weight:
                G[party1][party2]['weight'] = confidence
                G[party1][party2]['rule_id'] = rule_id
        else:
            G.add_edge(party1, party2, weight=confidence, rule_id=rule_id)
    
    # Find connected components
    components = list(nx.connected_components(G))
    
    # Create candidate entities
    candidate_entities = {}
    for i, component in enumerate(components):
        entity_id = f"CANDIDATE_{i+1:04d}"
        candidate_entities[entity_id] = sorted(list(component))
    
    print(f"\n✓ Created {len(candidate_entities)} candidate entities")
    print(f"  Total parties in entities: {sum(len(parties) for parties in candidate_entities.values())}")
    print(f"  Largest entity: {max(len(parties) for parties in candidate_entities.values())} parties")
    print(f"  Singleton entities: {sum(1 for parties in candidate_entities.values() if len(parties) == 1)}")
    
    return candidate_entities, G


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


def generate_master_entities(resolved_entities):
    """Generate MASTER_ENTITY table"""
    master_entities = []
    
    for entity_id, party_ids in resolved_entities.items():
        master_entities.append({
            'master_entity_id': entity_id,
            'party_count': len(party_ids),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True
        })
    
    return pd.DataFrame(master_entities)


def generate_party_to_entity_links(resolved_entities):
    """Generate PARTY_TO_ENTITY_LINK table (SCD2)"""
    links = []
    
    for entity_id, party_ids in resolved_entities.items():
        for party_id in party_ids:
            links.append({
                'link_id': str(uuid.uuid4()),
                'party_id': party_id,
                'master_entity_id': entity_id,
                'link_type': 'MATCH_EVIDENCE',
                'confidence_score': 1.0,  # TODO: Calculate aggregate confidence
                'created_at': datetime.now().isoformat(),
                'rec_start_date': datetime.now().isoformat(),
                'rec_end_date': None,
                'is_current': True
            })
    
    return pd.DataFrame(links)


def export_gold_tables(master_entity_df, party_link_df, new_blocking_df, output_dir='data/gold'):
    """Export Gold layer tables"""
    project_root = Path(__file__).parent.parent.parent
    gold_dir = project_root / output_dir
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    master_entity_file = gold_dir / 'master_entity.csv'
    party_link_file = gold_dir / 'party_to_entity_link.csv'
    
    master_entity_df.to_csv(master_entity_file, index=False)
    party_link_df.to_csv(party_link_file, index=False)
    
    # Append new transitive blocking records to existing MATCH_BLOCKING
    if len(new_blocking_df) > 0:
        silver_dir = project_root / 'data/silver'
        blocking_file = silver_dir / 'match_blocking.csv'
        existing_blocking = pd.read_csv(blocking_file)
        updated_blocking = pd.concat([existing_blocking, new_blocking_df], ignore_index=True)
        updated_blocking.to_csv(blocking_file, index=False)
        print(f"\n✓ Appended {len(new_blocking_df)} transitive blocking records to MATCH_BLOCKING")
    
    print(f"\n✓ Exported to:")
    print(f"  {master_entity_file}")
    print(f"  {party_link_file}")


def main():
    print("="*70)
    print("ENTITY RESOLUTION WITH TRANSITIVE CONFLICT DETECTION")
    print("="*70)
    
    # Load data
    match_evidence_df, match_blocking_df, std_attr_df, blocking_rules_df = load_data()
    
    # Build candidate entities from match evidence graph
    candidate_entities, entity_graph = build_candidate_entities(match_evidence_df)
    
    # Detect and resolve transitive conflicts
    resolved_entities, conflict_stats, new_blocking_records = resolve_entities_with_conflicts(
        candidate_entities, entity_graph, std_attr_df, blocking_rules_df, match_blocking_df
    )
    
    # Generate Gold layer tables
    master_entity_df = generate_master_entities(resolved_entities)
    party_link_df = generate_party_to_entity_links(resolved_entities)
    new_blocking_df = pd.DataFrame(new_blocking_records)
    
    # Export
    export_gold_tables(master_entity_df, party_link_df, new_blocking_df)
    
    print("\n" + "="*70)
    print("✅ ENTITY RESOLUTION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
