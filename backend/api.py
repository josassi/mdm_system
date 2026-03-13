"""
Flask API for Entity Resolution Frontend
Provides endpoints to query entities, parties, attributes, and match evidence
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent


def load_data():
    """Load all necessary data from CSV files"""
    bronze_dir = PROJECT_ROOT / 'data/bronze'
    silver_dir = PROJECT_ROOT / 'data/silver'
    gold_dir = PROJECT_ROOT / 'data/gold'
    metadata_dir = PROJECT_ROOT / 'data/uat_generation/metadata'
    
    data = {
        'source_party': pd.read_csv(bronze_dir / 'source_party.csv'),
        'raw_attribute': pd.read_csv(bronze_dir / 'raw_attribute.csv'),
        'relationship': pd.read_csv(bronze_dir / 'relationship.csv'),
        'standardized_attribute': pd.read_csv(silver_dir / 'standardized_attribute.csv'),
        'match_evidence': pd.read_csv(silver_dir / 'match_evidence.csv'),
        'difference_evidence': pd.read_csv(silver_dir / 'difference_evidence.csv'),
        'match_blocking': pd.read_csv(silver_dir / 'match_blocking.csv'),
        'party_cluster': pd.read_csv(silver_dir / 'party_cluster.csv'),
        'master_entity': pd.read_csv(gold_dir / 'master_entity.csv'),
        'party_to_entity_link': pd.read_csv(gold_dir / 'party_to_entity_link.csv'),
        'metadata_system': pd.read_csv(metadata_dir / 'metadata_system.csv'),
        'metadata_system_table': pd.read_csv(metadata_dir / 'metadata_system_table.csv'),
        'metadata_party_type': pd.read_csv(metadata_dir / 'metadata_party_type.csv'),
        'metadata_column': pd.read_csv(metadata_dir / 'metadata_column.csv'),
        'metadata_blocking_rule': pd.read_csv(metadata_dir / 'metadata_blocking_rule.csv'),
        'metadata_relationship': pd.read_csv(metadata_dir / 'metadata_relationship.csv'),
    }
    
    return data


data = load_data()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/entities', methods=['GET'])
def get_entities():
    """Get list of all master entities with summary statistics"""
    entities_list = []
    
    for idx, entity in data['master_entity'].iterrows():
        try:
            entity_id = entity['master_entity_id']
            
            # Get linked parties
            linked_parties = data['party_to_entity_link'][
                data['party_to_entity_link']['master_entity_id'] == entity_id
            ]
            
            party_ids = linked_parties['party_id'].tolist()
            
            # Get primary name from first party with name attributes
            primary_name = None
            for party_id in party_ids:
                try:
                    attrs = get_party_attributes_dict(party_id)
                    if 'ATTR_FIRST_NAME' in attrs and 'ATTR_LAST_NAME' in attrs:
                        primary_name = f"{attrs['ATTR_FIRST_NAME']} {attrs['ATTR_LAST_NAME']}"
                        break
                except Exception as e:
                    print(f"Error getting attributes for party {party_id}: {e}")
                    continue
            
            # Count match evidence
            evidence_count = 0
            for i, party1 in enumerate(party_ids):
                for party2 in party_ids[i+1:]:
                    evidence = data['match_evidence'][
                        (((data['match_evidence']['party_id_1'] == party1) & 
                          (data['match_evidence']['party_id_2'] == party2)) |
                         ((data['match_evidence']['party_id_1'] == party2) & 
                          (data['match_evidence']['party_id_2'] == party1)))
                    ]
                    evidence_count += len(evidence)
            
            # Check for conflicts
            conflicts = []
            for i, party1 in enumerate(party_ids):
                for party2 in party_ids[i+1:]:
                    blocking = data['match_blocking'][
                        (((data['match_blocking']['party_id_1'] == party1) & 
                          (data['match_blocking']['party_id_2'] == party2)) |
                         ((data['match_blocking']['party_id_1'] == party2) & 
                          (data['match_blocking']['party_id_2'] == party1))) &
                        (data['match_blocking']['is_active'] == True)
                    ]
                    if len(blocking) > 0:
                        conflicts.append({
                            'party1': party1,
                            'party2': party2,
                            'reason': blocking.iloc[0]['blocking_reason_code']
                        })
            
            # Single-party entities have no pairs to compare, so scores should be null
            is_single_party = len(party_ids) == 1
            
            entities_list.append({
                'entity_id': entity_id,
                'primary_name': primary_name or 'Unknown',
                'party_count': len(party_ids),
                'source_systems': get_source_systems(party_ids),
                'match_evidence_count': evidence_count,
                'conflict_count': len(conflicts),
                'has_conflicts': len(conflicts) > 0,
                'resolution_score': float(linked_parties['confidence_score'].mean()) if len(linked_parties) > 0 else 0,
                'created_at': entity['created_at'],
                'updated_at': entity['updated_at'],
                # Analytics from master_entity - only columns that actually exist
                'total_pairs': int(entity['total_pairs']) if pd.notna(entity.get('total_pairs')) else 0,
                'unique_attributes': int(entity['unique_attributes']) if pd.notna(entity.get('unique_attributes')) else 0,
                'total_attribute_instances': int(entity['total_attribute_instances']) if pd.notna(entity.get('total_attribute_instances')) else 0,
                'fully_matching_attributes': int(entity['fully_matching_attributes']) if pd.notna(entity.get('fully_matching_attributes')) else 0,
                'contradicting_attributes': int(entity['contradicting_attributes']) if pd.notna(entity.get('contradicting_attributes')) else 0,
                # For single-party entities, scores are null (no pairs to compare)
                'avg_pair_score': None if is_single_party else (float(entity['avg_pair_score']) if pd.notna(entity.get('avg_pair_score')) else 0),
                'min_pair_score': None if is_single_party else (float(entity['min_pair_score']) if pd.notna(entity.get('min_pair_score')) else 0),
                'max_pair_score': None if is_single_party else (float(entity['max_pair_score']) if pd.notna(entity.get('max_pair_score')) else 0),
            })
        except Exception as e:
            print(f"Error processing entity {entity_id} at index {idx}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return jsonify(entities_list)


@app.route('/api/entities/<entity_id>', methods=['GET'])
def get_entity_detail(entity_id):
    """Get detailed information about a specific entity"""
    entity = data['master_entity'][data['master_entity']['master_entity_id'] == entity_id]
    
    if len(entity) == 0:
        return jsonify({'error': 'Entity not found'}), 404
    
    entity = entity.iloc[0]
    
    # Get linked parties
    linked_parties = data['party_to_entity_link'][
        data['party_to_entity_link']['master_entity_id'] == entity_id
    ]
    
    party_ids = linked_parties['party_id'].tolist()
    
    # Build party details
    parties = []
    for party_id in party_ids:
        try:
            party_info = get_party_info(party_id)
            if party_info is None:
                continue
            link_info = linked_parties[linked_parties['party_id'] == party_id].iloc[0]
            party_info['link_confidence'] = float(link_info['confidence_score'])
            party_info['resolution_method'] = link_info['link_type']
            party_info['resolution_score'] = float(link_info['confidence_score'])
            parties.append(party_info)
        except Exception as e:
            continue
    
    # Get match evidence between parties
    evidence = get_match_evidence_for_parties(party_ids)
    
    # Get blocking information
    blocking = get_blocking_for_parties(party_ids)
    
    # Get relationships
    relationships = get_relationships_for_parties(party_ids)
    
    return jsonify({
        'entity_id': entity_id,
        'created_at': entity['created_at'],
        'updated_at': entity['updated_at'],
        'parties': parties,
        'match_evidence': evidence,
        'blocking': blocking,
        'relationships': relationships
    })


@app.route('/api/parties/<party_id>', methods=['GET'])
def get_party(party_id):
    """Get detailed information about a specific party"""
    party_info = get_party_info(party_id)
    
    if party_info is None:
        return jsonify({'error': 'Party not found'}), 404
    
    return jsonify(party_info)


@app.route('/api/parties/<party_id>/detail', methods=['GET'])
def get_party_detail(party_id):
    """Get comprehensive party detail including cluster and entity context"""
    
    # Check if party exists
    party = data['source_party'][data['source_party']['source_party_id'] == party_id]
    if len(party) == 0:
        return jsonify({'error': 'Party not found'}), 404
    
    # Get cluster_id for this party
    cluster_info = data['party_cluster'][
        (data['party_cluster']['party_id'] == party_id) &
        (data['party_cluster']['rec_end_date'].isna())
    ]
    
    cluster_id = None
    cluster_party_ids = []
    if len(cluster_info) > 0:
        cluster_id = cluster_info.iloc[0]['cluster_id']
        # Get all parties in this cluster
        cluster_parties = data['party_cluster'][
            (data['party_cluster']['cluster_id'] == cluster_id) &
            (data['party_cluster']['rec_end_date'].isna())
        ]
        cluster_party_ids = cluster_parties['party_id'].tolist()
    
    # Get entity_id for this party
    entity_link = data['party_to_entity_link'][
        data['party_to_entity_link']['party_id'] == party_id
    ]
    
    entity_id = None
    entity_party_ids = []
    if len(entity_link) > 0:
        entity_id = entity_link.iloc[0]['master_entity_id']
        # Get all parties in this entity
        entity_parties = data['party_to_entity_link'][
            data['party_to_entity_link']['master_entity_id'] == entity_id
        ]
        entity_party_ids = entity_parties['party_id'].tolist()
    
    # Get all unique party IDs (union of cluster and entity)
    all_party_ids = list(set(cluster_party_ids + entity_party_ids))
    
    # Get relationships for these parties
    initial_relationships = get_relationships_for_parties(all_party_ids)
    
    # Add any parties that are connected via relationships (even if not in same entity/cluster)
    relationship_party_ids = set(all_party_ids)
    for rel in initial_relationships:
        relationship_party_ids.add(rel['from_party_id'])
        relationship_party_ids.add(rel['to_party_id'])
    
    # Convert back to list
    all_party_ids = list(relationship_party_ids)
    
    # Get party details for all parties (including relationship-connected ones)
    parties = []
    for pid in all_party_ids:
        party_info = get_party_info(pid)
        if party_info:
            # Add flags to indicate membership
            party_info['in_cluster'] = pid in cluster_party_ids
            party_info['in_entity'] = pid in entity_party_ids
            party_info['is_focus'] = pid == party_id
            parties.append(party_info)
    
    # Get match evidence and blocking for all parties
    match_evidence = get_match_evidence_for_parties(all_party_ids)
    blocking = get_blocking_for_parties(all_party_ids)
    
    # Get relationships for all parties (re-fetch with expanded party list)
    relationships = get_relationships_for_parties(all_party_ids)
    
    return jsonify({
        'party_id': party_id,
        'cluster_id': cluster_id,
        'entity_id': entity_id,
        'parties': parties,
        'match_evidence': match_evidence,
        'blocking': blocking,
        'relationships': relationships
    })


def get_party_info(party_id):
    """Get comprehensive party information"""
    party = data['source_party'][data['source_party']['source_party_id'] == party_id]
    
    if len(party) == 0:
        return None
    
    party = party.iloc[0]
    
    # Get party type
    party_type = data['metadata_party_type'][
        data['metadata_party_type']['party_type_id'] == party['party_type_id']
    ].iloc[0]['party_type']
    
    # Get source system and table info
    system_table_info = data['metadata_system_table'][
        data['metadata_system_table']['system_table_id'] == party['system_table_id']
    ].iloc[0]
    
    # Get system name
    system_info = data['metadata_system'][
        data['metadata_system']['system_id'] == system_table_info['system_id']
    ]
    system_name = system_info.iloc[0]['system_name'] if len(system_info) > 0 else 'Unknown'
    
    # Get attributes with sources
    attributes = get_party_attributes_with_sources(party_id)
    
    return {
        'party_id': party_id,
        'party_type': party_type,
        'source_system': system_name,
        'source_table': system_table_info['table_name'],
        'attributes': attributes
    }


def get_party_attributes_dict(party_id):
    """Get party attributes as a simple dict"""
    std_attrs = data['standardized_attribute'][
        data['standardized_attribute']['source_party_id'] == party_id
    ]
    
    attr_dict = {}
    for _, row in std_attrs.iterrows():
        attr_dict[row['attribute_subtype_id']] = row['standardized_value']
    
    return attr_dict


def get_party_attributes_with_sources(party_id):
    """Get party attributes with full source lineage"""
    std_attrs = data['standardized_attribute'][
        data['standardized_attribute']['source_party_id'] == party_id
    ]
    
    attributes = []
    for _, std_attr in std_attrs.iterrows():
        # Get raw attribute
        raw_attr = data['raw_attribute'][
            data['raw_attribute']['raw_attribute_id'] == std_attr['raw_attribute_id']
        ]
        
        if len(raw_attr) == 0:
            continue
            
        raw_attr = raw_attr.iloc[0]
        
        # Get column metadata using positional index
        # column_id in raw_attribute is actually the row index in metadata_column
        try:
            column_meta = data['metadata_column'].iloc[int(raw_attr['column_id'])]
        except (IndexError, ValueError):
            continue
        
        attributes.append({
            'attribute_subtype_id': std_attr['attribute_subtype_id'],
            'attribute_type': column_meta['attribute_type'],
            'standardized_value': std_attr['standardized_value'],
            'raw_value': raw_attr['raw_value'],
            'source_column': column_meta['source_column'],
            'confidence_score': float(std_attr.get('confidence_score', 1.0)),
            'quality_score': float(column_meta.get('quality_score', 1.0)),
            'is_pii': bool(column_meta.get('is_pii', False))
        })
    
    return attributes


def get_source_systems(party_ids):
    """Get unique source systems for a list of parties"""
    systems = set()
    for party_id in party_ids:
        party = data['source_party'][data['source_party']['source_party_id'] == party_id]
        if len(party) > 0:
            system_table_info = data['metadata_system_table'][
                data['metadata_system_table']['system_table_id'] == party.iloc[0]['system_table_id']
            ]
            if len(system_table_info) > 0:
                system_info = data['metadata_system'][
                    data['metadata_system']['system_id'] == system_table_info.iloc[0]['system_id']
                ]
                if len(system_info) > 0:
                    systems.add(system_info.iloc[0]['system_name'])
    return list(systems)


def get_match_evidence_for_parties(party_ids):
    """Get all match evidence between a set of parties with pairwise match scores"""
    evidence_list = []
    
    # Calculate pairwise scores from actual evidence
    for i, party1 in enumerate(party_ids):
        for party2 in party_ids[i+1:]:
            pair_key = tuple(sorted([party1, party2]))
            
            # Get match evidence for this pair
            match_evidence = data['match_evidence'][
                (((data['match_evidence']['party_id_1'] == party1) & 
                  (data['match_evidence']['party_id_2'] == party2)) |
                 ((data['match_evidence']['party_id_1'] == party2) & 
                  (data['match_evidence']['party_id_2'] == party1)))
            ]
            
            # Get difference evidence for this pair
            diff_evidence = data['difference_evidence'][
                (((data['difference_evidence']['party_id_1'] == party1) & 
                  (data['difference_evidence']['party_id_2'] == party2)) |
                 ((data['difference_evidence']['party_id_1'] == party2) & 
                  (data['difference_evidence']['party_id_2'] == party1)))
            ]
            
            # Count matches and differences
            num_matches = len(match_evidence)
            num_differences = len(diff_evidence)
            
            # Calculate pairwise match score (simple ratio for now)
            # This represents the proportion of compared attributes that match
            total_compared = num_matches + num_differences
            match_score = num_matches / total_compared if total_compared > 0 else 0.0
            
            # Add scores to each evidence record for this pair
            for _, ev in match_evidence.iterrows():
                evidence_list.append({
                    'evidence_id': ev['evidence_id'],
                    'party_id_1': ev['party_id_1'],
                    'party_id_2': ev['party_id_2'],
                    'match_type': ev['match_type'],
                    'match_rule_id': ev['match_rule_id'],
                    'match_key': ev['match_key'],
                    'evidence_value': ev['evidence_value'],
                    'confidence_score': float(ev['confidence_score']),
                    'created_at': ev['created_at'],
                    # Add pairwise scores calculated from evidence
                    'match_score': match_score,
                    'num_matches': num_matches,
                    'num_differences': num_differences
                })
    
    return evidence_list


def get_blocking_for_parties(party_ids):
    """Get all blocking information between a set of parties"""
    blocking_list = []
    
    for i, party1 in enumerate(party_ids):
        for party2 in party_ids[i+1:]:
            blocking = data['match_blocking'][
                (((data['match_blocking']['party_id_1'] == party1) & 
                  (data['match_blocking']['party_id_2'] == party2)) |
                 ((data['match_blocking']['party_id_1'] == party2) & 
                  (data['match_blocking']['party_id_2'] == party1))) &
                (data['match_blocking']['is_active'] == True)
            ]
            
            for _, block in blocking.iterrows():
                # Get blocking rule details
                rule_info = {}
                if pd.notna(block['blocking_rule_id']):
                    rule = data['metadata_blocking_rule'][
                        data['metadata_blocking_rule']['blocking_rule_id'] == block['blocking_rule_id']
                    ]
                    if len(rule) > 0:
                        rule = rule.iloc[0]
                        rule_info = {
                            'rule_name': rule['rule_name'],
                            'rule_type': rule['rule_type'],
                            'attribute_subtype_id': rule['attribute_subtype_id']
                        }
                
                conflict_details = {}
                if pd.notna(block['conflict_details']):
                    try:
                        conflict_details = json.loads(block['conflict_details'])
                    except:
                        conflict_details = {'raw': block['conflict_details']}
                
                blocking_list.append({
                    'blocking_id': block['blocking_id'],
                    'party_id_1': block['party_id_1'],
                    'party_id_2': block['party_id_2'],
                    'blocking_reason_code': block['blocking_reason_code'],
                    'blocking_source': block['blocking_source'],
                    'conflict_details': conflict_details,
                    'rule_info': rule_info,
                    'created_at': block['created_at']
                })
    
    return blocking_list


def get_relationships_for_parties(party_ids):
    """Get all relationships involving the given parties with metadata"""
    relationships_list = []
    
    relationships = data['relationship'][
        (data['relationship']['from_party_id'].isin(party_ids)) |
        (data['relationship']['to_party_id'].isin(party_ids))
    ]
    
    for _, rel in relationships.iterrows():
        # Get relationship metadata
        metadata = data['metadata_relationship'][
            data['metadata_relationship']['relationship_id'] == rel['metadata_relationship_id']
        ]
        
        rel_metadata = {}
        if len(metadata) > 0:
            meta_row = metadata.iloc[0]
            rel_metadata = {
                'relationship_type': meta_row['relationship_type'],
                'is_bidirectional': bool(meta_row['is_bidirectional']),
                'guarantees_same_party': bool(meta_row['guarantees_same_party']),
                'confidence_score': float(meta_row['confidence_score']) if pd.notna(meta_row['confidence_score']) else None,
            }
        
        relationships_list.append({
            'relationship_id': rel['party_relationship_id'] if pd.notna(rel.get('party_relationship_id')) else None,
            'metadata_relationship_id': rel['metadata_relationship_id'] if pd.notna(rel.get('metadata_relationship_id')) else None,
            'from_party_id': rel['from_party_id'] if pd.notna(rel.get('from_party_id')) else None,
            'to_party_id': rel['to_party_id'] if pd.notna(rel.get('to_party_id')) else None,
            'from_matching_value': rel.get('from_matching_value') if pd.notna(rel.get('from_matching_value')) else None,
            'to_matching_value': rel.get('to_matching_value') if pd.notna(rel.get('to_matching_value')) else None,
            'metadata': rel_metadata
        })
    
    return relationships_list


@app.route('/api/search', methods=['GET'])
def search_entities():
    """Search entities by name or party attributes"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify([])
    
    results = []
    
    for _, entity in data['master_entity'].iterrows():
        entity_id = entity['master_entity_id']
        linked_parties = data['party_to_entity_link'][
            data['party_to_entity_link']['master_entity_id'] == entity_id
        ]
        party_ids = linked_parties['party_id'].tolist()
        
        # Search in party attributes
        match_found = False
        for party_id in party_ids:
            attrs = get_party_attributes_dict(party_id)
            for attr_value in attrs.values():
                if query in str(attr_value).lower():
                    match_found = True
                    break
            if match_found:
                break
        
        if match_found:
            # Get primary name
            primary_name = None
            for party_id in party_ids:
                attrs = get_party_attributes_dict(party_id)
                if 'ATTR_FIRST_NAME' in attrs and 'ATTR_LAST_NAME' in attrs:
                    primary_name = f"{attrs['ATTR_FIRST_NAME']} {attrs['ATTR_LAST_NAME']}"
                    break
            
            results.append({
                'entity_id': entity_id,
                'primary_name': primary_name or 'Unknown',
                'party_count': len(party_ids)
            })
    
    return jsonify(results[:20])


@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        # Total counts
        total_parties = len(data['source_party'])
        total_entities = len(data['master_entity'])
        total_systems = len(data['metadata_system'])
        
        # Join tables to get attribute types
        # Convert column_id to string to ensure consistent types
        raw_attrs = data['raw_attribute'][['raw_attribute_id', 'column_id']].copy()
        raw_attrs['column_id'] = raw_attrs['column_id'].astype(str)
        
        metadata_cols = data['metadata_column'][['column_id', 'attribute_type']].copy()
        metadata_cols['column_id'] = metadata_cols['column_id'].astype(str)
        
        std_attrs_with_type = data['standardized_attribute'].merge(
            raw_attrs, 
            on='raw_attribute_id', 
            how='left'
        ).merge(
            metadata_cols, 
            on='column_id', 
            how='left'
        )
        
        # Distinct HKID count (count unique SUB_HKID values)
        # HKIDs are stored with attribute_subtype_id='SUB_HKID' in standardized_attribute
        hkid_attrs = data['standardized_attribute'][
            data['standardized_attribute']['attribute_subtype_id'] == 'SUB_HKID'
        ]
        distinct_hkids = hkid_attrs['standardized_value'].nunique()
        
        # Entities by match score distribution
        entities_df = data['master_entity']
        score_distribution = {
            'perfect_match': len(entities_df[entities_df['avg_pair_score'] >= 0.99]),
            'high_match': len(entities_df[(entities_df['avg_pair_score'] >= 0.8) & (entities_df['avg_pair_score'] < 0.99)]),
            'medium_match': len(entities_df[(entities_df['avg_pair_score'] >= 0.5) & (entities_df['avg_pair_score'] < 0.8)]),
            'low_match': len(entities_df[(entities_df['avg_pair_score'] > 0) & (entities_df['avg_pair_score'] < 0.5)]),
            'no_match': len(entities_df[entities_df['avg_pair_score'] == 0])
        }
        
        # Entity size distribution
        entity_size_distribution = {
            'single_party': len(entities_df[entities_df['party_count'] == 1]),
            'two_parties': len(entities_df[entities_df['party_count'] == 2]),
            'three_parties': len(entities_df[entities_df['party_count'] == 3]),
            'four_plus_parties': len(entities_df[entities_df['party_count'] >= 4])
        }
        
        # Conflict statistics
        total_blocking_pairs = len(data['match_blocking'][data['match_blocking']['is_active'] == True])
        entities_with_contradictions = len(entities_df[entities_df['contradicting_attributes'] > 0])
        
        # Match evidence statistics
        total_match_evidence = len(data['match_evidence'])
        # Calculate avg match evidence per entity from match_evidence table
        evidence_by_entity = {}
        for entity_id in entities_df['master_entity_id']:
            entity_parties = data['party_to_entity_link'][
                data['party_to_entity_link']['master_entity_id'] == entity_id
            ]['party_id'].tolist()
            
            evidence_count = 0
            for i, p1 in enumerate(entity_parties):
                for p2 in entity_parties[i+1:]:
                    pair_evidence = data['match_evidence'][
                        (((data['match_evidence']['party_id_1'] == p1) & 
                          (data['match_evidence']['party_id_2'] == p2)) |
                         ((data['match_evidence']['party_id_1'] == p2) & 
                          (data['match_evidence']['party_id_2'] == p1)))
                    ]
                    evidence_count += len(pair_evidence)
            evidence_by_entity[entity_id] = evidence_count
        
        avg_match_evidence_per_entity = sum(evidence_by_entity.values()) / len(evidence_by_entity) if evidence_by_entity else 0
        
        # Relationship statistics (active relationships have no end date)
        relationships_df = data['relationship']
        total_relationships = len(relationships_df[relationships_df['rec_end_date'].isna()])
        
        # Attribute statistics
        total_attributes = len(data['standardized_attribute'])
        unique_attribute_types = std_attrs_with_type['attribute_type'].nunique()
        
        # Quality metrics (exclude single-party entities from score averages)
        multi_party_entities = entities_df[entities_df['party_count'] > 1]
        avg_entity_match_score = multi_party_entities['avg_pair_score'].mean() if len(multi_party_entities) > 0 else 0
        avg_unique_attrs_per_entity = entities_df['unique_attributes'].mean()
        avg_contradicting_attrs = entities_df['contradicting_attributes'].mean()
        
        # System-level statistics - join source_party with metadata_system_table to get system_id
        parties_with_system = data['source_party'].merge(
            data['metadata_system_table'][['system_table_id', 'system_id']], 
            on='system_table_id', 
            how='left'
        )
        parties_by_system = parties_with_system.groupby('system_id').size().to_dict()
        
        return jsonify({
            'totals': {
                'total_parties': int(total_parties),
                'total_entities': int(total_entities),
                'total_systems': int(total_systems),
                'distinct_hkids': int(distinct_hkids),
                'total_relationships': int(total_relationships),
                'total_attributes': int(total_attributes),
                'unique_attribute_types': int(unique_attribute_types)
            },
            'match_score_distribution': score_distribution,
            'entity_size_distribution': entity_size_distribution,
            'conflicts': {
                'total_blocking_pairs': int(total_blocking_pairs),
                'entities_with_contradictions': int(entities_with_contradictions)
            },
            'quality_metrics': {
                'avg_entity_match_score': float(avg_entity_match_score),
                'avg_match_evidence_per_entity': float(avg_match_evidence_per_entity),
                'avg_unique_attrs_per_entity': float(avg_unique_attrs_per_entity),
                'avg_contradicting_attrs': float(avg_contradicting_attrs),
                'total_match_evidence': int(total_match_evidence)
            },
            'parties_by_system': parties_by_system
        })
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Entity Resolution API Server...")
    print(f"Data loaded: {len(data['master_entity'])} entities")
    app.run(debug=True, port=5001)
