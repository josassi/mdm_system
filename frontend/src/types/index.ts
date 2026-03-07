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
}

export interface Party {
  party_id: string
  party_type: string
  source_system: string
  source_table: string
  attributes: Attribute[]
  link_confidence?: string
  resolution_method?: string
  resolution_score?: number
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
  from_party_id: string
  to_party_id: string
  from_matching_value?: string
  to_matching_value?: string
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
