"""
Helper functions for UAT scenario generation
"""

from datetime import datetime
import json


def init_data_structure():
    """Initialize empty data structure for all tables"""
    return {
        'leads': [],
        'quotes': [],
        'quote_members': [],
        'applications': [],
        'policies': [],
        'policy_members': [],
        'claims': [],
        'expected_clusters': [],
        'expected_entities': [],
        'expected_matches': []
    }


def add_cluster(data, sid, sname, cid, table, pk, notes=''):
    """Helper to add expected cluster"""
    data['expected_clusters'].append({
        'scenario_id': sid,
        'scenario_name': sname,
        'expected_cluster_id': cid,
        'source_table': table,
        'source_pk_value': pk,
        'notes': notes
    })


def add_entity(data, sid, sname, eid, person_id, party_ids, notes=''):
    """Helper to add expected entity"""
    data['expected_entities'].append({
        'scenario_id': sid,
        'scenario_name': sname,
        'expected_master_entity_id': eid,
        'person_identifier': person_id,
        'source_party_ids': json.dumps(party_ids),
        'notes': notes
    })


def add_match(data, sid, p1, p2, should_match, reason, conf):
    """Helper to add expected match"""
    data['expected_matches'].append({
        'scenario_id': sid,
        'party_id_1': p1,
        'party_id_2': p2,
        'should_match': should_match,
        'match_reason': reason,
        'min_confidence_score': conf
    })


def now():
    """Return current timestamp"""
    return datetime.now()
