
// =====================================================================
// FINALIZED DATA MODEL
// Renamed 'Record' to 'Party' for conceptual integrity. A 'Party' is a 
// person or organization, which is more accurate than a generic 'Record'.
// =====================================================================
// =====================================================================
// 1. SOURCE & STAGING LAYER (BRONZE)
// =====================================================================
table SOURCE_PARTY {
  party_id uuid [pk, note: 'Unique ID for a single party (person/org) instance from a source system']
  system_table_id uuid [ref: > METADATA_SYSTEM_TABLE.system_table_id, not null]
  party_type_id uuid [ref: > METADATA_PARTY_TYPE.party_type_id, not null]
  source_pk_hash jsonb [not null, note: 'Hash of the original primary key(s) from the source table']
  cluster_computed_at timestamp [note: 'When the clustering was last computed']
}

table PK_HASH_MAPPING {
  pk_hash uuid [pk, note: 'Hash of the original primary key(s) from the source table']
  pk_values jsonb [not null, note: 'The original primary key(s) from the source table, stored as JSON']
}


table METADATA_PARTY_TYPE {
  party_type_id uuid
  party_type string [note: 'Name of the party type']
}

table PARTY_CLUSTER {
  party_id uuid [pk, ref: > SOURCE_PARTY.party_id, not null]
  cluster_id uuid [note: 'All parties connected via RELATIONSHIP edges share the same cluster_id']
  rec_start_date timestamp
  rec_end_date timestamp
}

table RAW_ATTRIBUTE {
  raw_attribute_type_id uuid [pk, note: 'Unique ID for this specific version of the raw attribute']
  party_id uuid [ref: > SOURCE_PARTY.party_id, not null, note: 'Links to the source party']
  
  // This is the only link to attribute metadata. It implicitly defines the GENERAL attribute type.
  column_id uuid [ref: > METADATA_COLUMN.column_id, not null]
  
  raw_value string [not null, note: 'The exact, unaltered value from the source system']
  
  // SCD2 Columns for Full Auditing
  rec_start_date timestamp [not null, note: 'The timestamp when this version of the value became active']
  rec_end_date timestamp [note: 'The timestamp when this value was superseded. NULL means it is the current version.']
  is_current boolean [not null, default: true, note: 'A flag for easy querying of the current version.']
  
  indexes {
    (party_id, column_id, rec_end_date) [note: 'Efficiently find the current value for a given party/column']
  }
}

table RELATIONSHIP {
  party_relationship_id uuid [pk]
  metadata_relationship_id uuid [ref: > METADATA_RELATIONSHIP.relationship_id, note: 'Populated if FK-based relationship']
  metadata_party_type_relationship_id uuid [ref: > METADATA_PARTY_TYPE_RELATIONSHIP.party_type_relationship_id, note: 'Populated if semantic (within the same row) relationship']
  from_party_id uuid [ref: > SOURCE_PARTY.party_id, not null]
  to_party_id uuid [ref: > SOURCE_PARTY.party_id, not null]
  from_matching_value string [note: 'e.g., The application_id value that created this link. If within_same_row_relationship, equals to the pk hash']
  to_matching_value string [note: 'e.g., The application_id value that created this link. Same as from_matching_value for simple relationships or within rows relationship (in which case it is the PK hash)']
  rec_start_date timestamp
  rec_end_date timestamp
}

table METADATA_PARTY_TYPE_RELATIONSHIP {
  party_type_relationship_id uuid [pk]
  from_party_type_id uuid [ref: > METADATA_PARTY_TYPE.party_type_id, not null, note: 'Source party type in the relationship']
  to_party_type_id uuid [ref: > METADATA_PARTY_TYPE.party_type_id, not null, note: 'Target party type in the relationship']
  relationship_type_id uuid [ref: > METADATA_RELATIONSHIP_TYPE.relationship_type_id, not null]
  binding_strength string [not null, note: 'STRONG, MEDIUM, WEAK']
  is_hierarchical boolean [not null, default: false, note: 'True for parent-child relationships']
  is_bidirectional boolean [not null, default: false, note: 'True if relationship applies in both directions']
  source_system string [not null, note: 'System where this relationship pattern exists, e.g., SmartPlus']
  source_table string [not null, note: 'Table where this relationship pattern exists, e.g., quote_member']
  
  indexes {
    (from_party_type_id, to_party_type_id, source_system, source_table) [note: 'Unique relationship pattern per context']
  }
  
  note: 'Defines within-row semantic relationships between party types (e.g., spouse, dependent relationships within same quote/policy). Used by SOURCE_RELATIONSHIP ingestion to discover relationships without explicit foreign keys.'
}


Table METADATA_RELATIONSHIP {
  relationship_id                  uuid       [pk]
  is_bidirectional                 bool       [not null]
  guarantees_same_party            bool       [not null]
  keeping_granularity_when_used    bool       [not null]
  from_the_same_row                bool       [not null]
  relationship_type_id             uuid       [not null, ref: > METADATA_RELATIONSHIP_TYPE.relationship_type_id]
  from_column_id                   uuid       [not null, ref: > METADATA_COLUMN.column_id]
  to_column_id                     uuid       [not null, ref: > METADATA_COLUMN.column_id]
  bridge_table_id                  uuid       [ref: > METADATA_SYSTEM_TABLE.system_table_id, note: 'Nullable for direct relationships']
  bridge_column_source_id          uuid       [ref: > METADATA_COLUMN.column_id, note: 'Nullable']
  bridge_column_target_id          uuid       [ref: > METADATA_COLUMN.column_id, note: 'Nullable']
  remarks                          string
  confidence_score                 float     
  rec_start_date                   timestamp
  rec_end_date                     timestamp
}


// =====================================================================
// 2. STANDARDIZATION & RESOLUTION LAYER (SILVER)
// =====================================================================
table STANDARDIZED_ATTRIBUTE {
  standardized_attribute_type_id uuid [pk]
  // This provides perfect traceability from the standardized value back to its exact raw source.
  raw_attribute_type_id uuid [ref: > RAW_ATTRIBUTE.raw_attribute_type_id, not null]
  
  // This is the correct and only place for the sub-type.
  // It stores the result of the classification logic (e.g., "Passport", "HKID").
  attribute_subtype_id uuid [ref: > METADATA_ATTRIBUTE_SUBTYPE.attribute_subtype_id, not null]
  
  standardized_value string [not null, note: 'The cleaned, normalized value used for matching']
  
  // Optional but recommended columns for this layer.
  confidence_score float [note: 'Confidence of the classification logic (0.0 to 1.0).']
  pipeline_version string [note: 'Version of the classification pipeline that generated this record.']
  indexes {
    // We match on the specific sub-type and its standardized value.
    (attribute_subtype_id, standardized_value)
    // A unique index to prevent the pipeline from inserting a duplicate classification for the same raw attribute.
    (raw_attribute_type_id, attribute_subtype_id) [unique]
  }
}
table MATCH_EVIDENCE {
  evidence_id uuid [pk]
  party_id_1 uuid [ref: > SOURCE_PARTY.party_id, not null]
  party_id_2 uuid [ref: > SOURCE_PARTY.party_id, not null]
  
  match_type string [not null, note: 'e.g., PII, RELATIONSHIP, HARD_LINK']
  match_rule_id string [note: 'Identifier for the specific rule that fired, e.g., RULE_PASSPORT_MATCH', ref: > METADATA_MATCH_RULE.match_rule_id]
  match_key string [not null, note: 'e.g., STANDARDIZED_GOV_ID, SHARED_POLICY_ID']
  evidence_value string [not null, note: 'The actual value that matched, e.g., "K1234567" or "POLICY-12345"']
  
  confidence_score float [not null]
  created_at timestamp [default: `now()`]
  blocking_keys string [note: 'keys used for blocking to create this matching evidence']
  indexes {
    (party_id_1, party_id_2, match_rule_id) [unique]
  }
}

table METADATA_MATCH_RULE {
  match_rule_id uuid [pk]
  rule_name string [unique, note: 'e.g., EXACT_PASSPORT, FUZZY_NAME_EMAIL']
  rule_type string [note: 'DETERMINISTIC, PROBABILISTIC']
  
  // Define which attributes/subtypes this rule uses
  required_attributes jsonb [note: 'Array of attribute_subtype_ids']
  
  // Scoring parameters
  base_confidence_score float
  threshold float [note: 'Minimum similarity score to create evidence']
  
  // Rule logic (stored as code reference or SQL)
  rule_logic string
  is_active boolean [default: true]
}

table MATCH_BLOCKING {
  blocking_id uuid [pk]
  party_id_1 uuid [ref: > SOURCE_PARTY.party_id, not null]
  party_id_2 uuid [ref: > SOURCE_PARTY.party_id, not null]
  
  // Why is this blocked?
  blocking_reason_code string [not null, note: 'e.g., CONFLICTING_HKID, GENDER_CONFLICT, MANUAL_OVERRIDE']
  blocking_rule_id uuid [ref: > METADATA_BLOCKING_RULE.blocking_rule_id, note: 'NULL if manual block']
  
  // Automatic vs Manual blocking
  blocking_source string [not null, note: 'AUTOMATIC | MANUAL_STEWARD']
  steward_user_id uuid [note: 'Populated if blocking_source=MANUAL_STEWARD']
  
  // Evidence of conflict
  conflicting_attribute_subtype_id uuid [ref: > METADATA_ATTRIBUTE_SUBTYPE.attribute_subtype_id, note: 'Which attribute caused the block']
  conflict_details jsonb [note: 'e.g., {"party1_hkid": "C123456(7)", "party2_hkid": "C999999(9)"}']
  
  // Temporal control
  created_at timestamp [default: `now()`]
  expires_at timestamp [note: 'Optional: temporary blocks for review']
  is_active boolean [default: true, note: 'Allow soft delete of blocking rules']
  
  // Auditing
  created_by string
  notes text [note: 'Steward notes explaining manual blocks']
  
  indexes {
    (party_id_1, party_id_2, blocking_rule_id) [unique, note: 'Prevent duplicate blocking entries']
    (party_id_1, party_id_2) [note: 'Fast lookup during matching - WHERE is_active=TRUE']
  }
  
  note: 'Prevents two parties from being matched. Checked DURING match evidence generation (before running expensive match rules). Used for both automatic blocking (conflicting IDs) and manual steward overrides.'
}

table METADATA_BLOCKING_RULE {
  blocking_rule_id uuid [pk]
  rule_name string [unique, not null, note: 'e.g., DIFFERENT_HKID_BLOCKS_MATCH, GENDER_CONFLICT']
  rule_type string [not null, note: 'CONFLICT | TEMPORAL_CONFLICT | CUSTOM']
  
  // Which attribute this rule applies to
  attribute_subtype_id uuid [ref: > METADATA_ATTRIBUTE_SUBTYPE.attribute_subtype_id, note: 'e.g., HKID, Passport, Gender, DOB']
  
  // Rule parameters
  blocking_logic string [not null, note: 'DIFFERENT_VALUES | THRESHOLD_EXCEEDED | CUSTOM_SQL']
  threshold_value float [note: 'For temporal conflicts (e.g., DOB difference > 365 days)']
  
  // Control
  is_active boolean [default: true]
  priority int [note: 'Higher priority = checked first']
  
  // Context
  applies_to_same_country boolean [default: true, note: 'For IDs: only block if same issuing country']
  requires_high_quality_sources boolean [default: false, note: 'Only block if both sources have quality > threshold']
  source_quality_threshold float [default: 0.8]
  
  // Metadata
  created_at timestamp [default: `now()`]
  updated_at timestamp
  
  note: 'Defines automatic blocking rules that prevent matching. Examples: different HKIDs, gender conflicts, DOB > 1 year difference. Checked during match evidence generation to skip blocked pairs early.'
}

// =====================================================================
// 3. MASTER LAYER (GOLD)
// =====================================================================
table MASTER_ENTITY {
  master_entity_id uuid [pk, note: 'The unique ID for a resolved entity, the "Golden Record" ID']
  created_at timestamp [default: `now()`]
  updated_at timestamp
}


table PARTY_TO_ENTITY_LINK {
  party_id uuid [pk, ref: - SOURCE_PARTY.party_id]
  master_entity_id uuid [ref: > MASTER_ENTITY.master_entity_id, not null]
  confidence string
  manual_validation string [note: 'e.g., Validated, Rejected, NeedsReview']
  linked_at timestamp [default: `now()`]
  resolution_method string [note: 'DETERMINISTIC, PROBABILISTIC, MANUAL']
  contributing_evidence_ids jsonb [note: 'Array of evidence_id values that led to this link']
  resolution_score float [note: 'Combined score from all evidence']
  rec_start_date timestamp
  rec_end_date timestamp
  link_source string
}
table MASTER_ENTITY_RELATIONSHIP {
  master_relationship_id uuid [pk]
  from_master_entity_id uuid [ref: > MASTER_ENTITY.master_entity_id, not null]
  to_master_entity_id uuid [ref: > MASTER_ENTITY.master_entity_id, not null]
  relationship_type_id uuid [ref: > METADATA_RELATIONSHIP_TYPE.relationship_type_id, not null]
  // ... other metadata like start/end dates
}
// =====================================================================
// 4. METADATA LAYER
// =====================================================================
table METADATA_SYSTEM {
  system_id uuid [pk]
  system_name string [unique, not null]
}
table METADATA_SYSTEM_TABLE {
  system_table_id uuid [pk]
  system_id uuid [ref: > METADATA_SYSTEM.system_id, not null]
  table_name string [not null]
  
  indexes {
    (system_id, table_name) [unique]
  }
}
table METADATA_COLUMN {
  column_id uuid [pk]
  system_table_id uuid [ref: > METADATA_SYSTEM_TABLE.system_table_id, not null]
  column_name string [not null]
  
  // This correctly points to the GENERAL attribute.
  attribute_type_id uuid [ref: > METADATA_ATTRIBUTE_TYPE.attribute_type_id, not null]
  
  party_type_id uuid [ref: > METADATA_PARTY_TYPE.party_type_id, not null]
  
  
  priority int
  quality_score float
  
  indexes {
    (system_table_id, column_name) [unique]
  }
}
table METADATA_ATTRIBUTE_TYPE {
  attribute_type_id uuid [pk]
  attribute_name string [unique, not null, note: 'e.g., Government ID, First Name, Email Address']
  is_pii boolean [default: true]
  
  requires_classification boolean [not null, default: false]
}
table METADATA_ATTRIBUTE_SUBTYPE {
  attribute_subtype_id uuid [pk]
  attribute_type_id uuid [ref: > METADATA_ATTRIBUTE_TYPE.attribute_type_id, not null, note: 'Links to the parent attribute, e.g., "Government ID"']
  subtype_name string [not null, note: 'The name of the specific type, e.g., "Passport", "HKID", "Drivers License"']
  
  indexes {
    (attribute_type_id, subtype_name) [unique]
  }
}
table METADATA_RELATIONSHIP_TYPE {
  relationship_type_id uuid [pk]
  type_name string [unique, not null]
  binding_strength string [not null, note: 'e.g., HARD, STRONG, WEAK, CONTEXTUAL']
}
