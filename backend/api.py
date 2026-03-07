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
        'match_blocking': pd.read_csv(silver_dir / 'match_blocking.csv'),
        'master_entity': pd.read_csv(gold_dir / 'master_entity.csv'),
        'party_to_entity_link': pd.read_csv(gold_dir / 'party_to_entity_link.csv'),
        'metadata_system': pd.read_csv(metadata_dir / 'metadata_system.csv'),
        'metadata_system_table': pd.read_csv(metadata_dir / 'metadata_system_table.csv'),
        'metadata_party_type': pd.read_csv(metadata_dir / 'metadata_party_type.csv'),
        'metadata_column': pd.read_csv(metadata_dir / 'metadata_column.csv'),
        'metadata_blocking_rule': pd.read_csv(metadata_dir / 'metadata_blocking_rule.csv'),
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
                'updated_at': entity['updated_at']
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
        party_info = get_party_info(party_id)
        link_info = linked_parties[linked_parties['party_id'] == party_id].iloc[0]
        party_info['link_confidence'] = float(link_info['confidence_score'])
        party_info['resolution_method'] = link_info['link_type']
        party_info['resolution_score'] = float(link_info['confidence_score'])
        parties.append(party_info)
    
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
    """Get all match evidence between a set of parties"""
    evidence_list = []
    
    for i, party1 in enumerate(party_ids):
        for party2 in party_ids[i+1:]:
            evidence = data['match_evidence'][
                (((data['match_evidence']['party_id_1'] == party1) & 
                  (data['match_evidence']['party_id_2'] == party2)) |
                 ((data['match_evidence']['party_id_1'] == party2) & 
                  (data['match_evidence']['party_id_2'] == party1)))
            ]
            
            for _, ev in evidence.iterrows():
                evidence_list.append({
                    'evidence_id': ev['evidence_id'],
                    'party_id_1': ev['party_id_1'],
                    'party_id_2': ev['party_id_2'],
                    'match_type': ev['match_type'],
                    'match_rule_id': ev['match_rule_id'],
                    'match_key': ev['match_key'],
                    'evidence_value': ev['evidence_value'],
                    'confidence_score': float(ev['confidence_score']),
                    'created_at': ev['created_at']
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
    """Get all relationships involving the given parties"""
    relationships_list = []
    
    relationships = data['relationship'][
        (data['relationship']['from_party_id'].isin(party_ids)) |
        (data['relationship']['to_party_id'].isin(party_ids))
    ]
    
    for _, rel in relationships.iterrows():
        relationships_list.append({
            'relationship_id': rel['party_relationship_id'],
            'from_party_id': rel['from_party_id'],
            'to_party_id': rel['to_party_id'],
            'from_matching_value': rel.get('from_matching_value'),
            'to_matching_value': rel.get('to_matching_value')
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


if __name__ == '__main__':
    print("Starting Entity Resolution API Server...")
    print(f"Data loaded: {len(data['master_entity'])} entities")
    app.run(debug=True, port=5001)
