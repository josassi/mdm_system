export interface Entity {
  entity_id: string
  primary_name: string
  party_count: number
  source_systems: string[]
  match_evidence_count: number
  conflict_count: number
  has_conflicts: boolean
  resolution_score: number
  created_at: string
  updated_at: string
  // Analytics from master_entity
  total_pairs?: number
  pairs_with_evidence?: number
  pairs_blocked?: number
  unique_attributes?: number
  total_attribute_instances?: number
  fully_matching_attributes?: number
  contradicting_attributes?: number
  non_matching_pairs?: number
  ok_pairs?: number
  matching_pairs?: number
  avg_pair_score?: number
  min_pair_score?: number
  max_pair_score?: number
}

export interface Party {
  party_id: string
  party_type: string
  source_system: string
  source_table: string
  cluster_id?: string | null
  attributes: Attribute[]
  link_confidence?: string
  resolution_method?: string
  resolution_score?: number
  in_cluster?: boolean
  in_entity?: boolean
  is_focus?: boolean
}

export interface Attribute {
  attribute_subtype_id: string
  attribute_type: string
  standardized_value: string
  raw_value: string
  source_column: string
  confidence_score: number
  quality_score: number
  is_pii: boolean
}

export interface MatchEvidence {
  evidence_id: string
  party_id_1: string
  party_id_2: string
  match_type: string
  match_rule_id: string
  match_key: string
  evidence_value: string
  confidence_score: number
  created_at: string
  match_score?: number
  num_matches?: number
  num_differences?: number
}

export interface Blocking {
  blocking_id: string
  party_id_1: string
  party_id_2: string
  blocking_reason_code: string
  blocking_source: string
  conflict_details: Record<string, any>
  rule_info: {
    rule_name?: string
    rule_type?: string
    attribute_subtype_id?: string
  }
  created_at: string
}

export interface Relationship {
  relationship_id: string
  metadata_relationship_id: string
  from_party_id: string
  to_party_id: string
  from_matching_value?: string | null
  to_matching_value?: string | null
  metadata: {
    relationship_type: string
    is_bidirectional: boolean
    guarantees_same_party: boolean
    confidence_score: number | null
  }
}

export interface EntityDetail {
  entity_id: string
  created_at: string
  updated_at: string
  parties: Party[]
  match_evidence: MatchEvidence[]
  blocking: Blocking[]
  relationships: Relationship[]
}

export interface PartyDetail {
  party_id: string
  cluster_id: string | null
  entity_id: string | null
  parties: Party[]
  match_evidence: MatchEvidence[]
  blocking: Blocking[]
  relationships: Relationship[]
}

export interface Cluster {
  cluster_id: string
  party_count: number
  entity_count: number
  resolution_rate: number
  source_systems: string[]
  party_types: string[]
  relationship_count: number
  evidence_count: number
}
