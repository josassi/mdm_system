# Party Granularity Architecture
## Single View of Person (SVOP) MDM System

---

## Problem Statement

In a Master Data Management (MDM) system for person identity resolution, the fundamental challenge is defining **what constitutes a "party"** at the most granular level possible.

### The Core Challenge

**A party is not always a whole database row.**

Traditional MDM systems assume:
```
One source row = One party
```

However, real-world source systems have more complex patterns:

**Pattern 1: Multiple Parties in One Row (Column-Subset Based)**
```csv
app_id, applicant_name, applicant_dob, spouse_name, spouse_dob
A001,   "John Smith",   "1985-01-01",   "Mary Smith", "1987-05-10"
```
→ This **single row** contains **two parties**: applicant and spouse

**Pattern 2: One Party Per Row (Conditional Type Determination)**
```csv
qm_id, quote_id, name,        relationship_type
QM001, Q001,     "John",      "Primary"
QM002, Q001,     "Mary",      "Spouse"
```
→ Each row is one party, but the **party_type** is determined by a discriminator column

**Pattern 3: One Party Per Row (Simple/Business Objects)**
```csv
quote_id, lead_id, contract_number, total_premium
Q001,     L001,    C001,            5000.00
Q002,     L002,    C002,            7500.00
```
→ Each row represents exactly one entity (business object like quote, policy, claim)
→ Used for FK relationships between parties across tables

### Why This Matters

**Incorrect granularity leads to:**
- False positive matches (merging different people)
- False negative matches (failing to link the same person)
- Incorrect relationship discovery
- Broken entity resolution logic

**Example:**
If you treat the entire application row as one party, you lose the ability to match the spouse independently. If you try to create relationships between quote_member rows using "same-row relationship" logic, you're fundamentally misunderstanding the data structure.

---

## Requirements

### 1. **Party Type Definition**

**party_type** = The minimum granular identity schema for a specific person in a specific context.

**Format:** `system.table[.role]`

**Examples:**
- `smartplus.lead` - A lead record (whole row)
- `smartplus.application.applicant` - Applicant columns within application row (column subset)
- `smartplus.application.spouse` - Spouse columns within application row (column subset)
- `smartplus.quote_member.applicant` - Quote member row where relationship_type='Primary'
- `smartplus.quote_member.spouse` - Quote member row where relationship_type='Spouse'

**Key Principle:** A party_type defines which columns belong to which identity.

### 2. **METADATA_COLUMN: Source of Truth**

Every source column must be mapped to either:
- **An attribute of a party_type** (is_attribute=True, party_type specified)
- **A relationship/ID column** (is_relationship=True, party_type=NULL)
- **A party_type discriminator** (is_party_type_condition=True, condition_logic specified)

**Critical Rule:** Attributes MUST have a party_type. There cannot be `party_type=NULL` for attribute columns.

**For Pattern 1 (Column-Subset):**
```csv
source_column,           party_type,                          attribute_type
applicant_first_name,    smartplus.application.applicant,     ATTR_FIRST_NAME
spouse_first_name,       smartplus.application.spouse,        ATTR_FIRST_NAME
```

**For Pattern 2 (Conditional):**
- Discriminator column has `condition_logic` (e.g., `relationship_type='Primary'`)
- Attribute columns are replicated for each possible party_type:
```csv
source_column,  party_type,                             condition_logic
first_name,     smartplus.quote_member.applicant,       NULL
first_name,     smartplus.quote_member.spouse,          NULL
first_name,     smartplus.quote_member.dependent,       NULL
```

### 3. **METADATA_PARTY_TYPE_RELATIONSHIP**

**Purpose:** Define semantic relationships between parties **within the same row**.

**Critical Distinction:**
- **Same Row** → METADATA_PARTY_TYPE_RELATIONSHIP
- **Different Rows** → METADATA_RELATIONSHIP (FK-based)

**Structure:**
```csv
party_type_relationship_id, from_party_type,                    to_party_type,                       relationship_type, is_bidirectional, source_system, source_table
PTR_APP_APPLICANT_SPOUSE,   smartplus.application.applicant,   smartplus.application.spouse,        SPOUSE_OF,         True,             SmartPlus,     application
```

**No condition_logic needed** - if parties are in the same row, the relationship is implicit.

**Wrong Usage (REMOVED):**
```
PTR_QM_APPLICANT_SPOUSE, quote_member.applicant, quote_member.spouse, condition_logic="from.quote_id=to.quote_id"
```
→ This is WRONG because applicant and spouse are in **different rows**. This should use METADATA_RELATIONSHIP instead.

### 4. **METADATA_RELATIONSHIP (FK-Based)**

**Purpose:** Define foreign key relationships between parties **in different rows/tables**.

**Structure:**
```csv
relationship_id,           from_system, from_table,    from_column, to_system, to_table, to_column, relationship_type
REL_QUOTE_LEAD,            SmartPlus,   quote,         lead_id,     SmartPlus, lead,     lead_id,   BUSINESS_LINK
REL_POLICY_APPLICATION,    Smile,       policy,        application_id, SmartPlus, application, app_id, BUSINESS_LINK
```

**Key Feature: relationship_id**
- Each FK relationship has a unique identifier
- Referenced in Bronze RELATIONSHIP.metadata_relationship_id
- Enables traceability from relationship instances back to their metadata definition

### 5. **METADATA_SYSTEM_TABLE.main_party_type_id**

**Purpose:** Designate which party_type to use for FK relationships when a table has multiple party types.

**Challenge:**
- Application table has 2 party types: applicant and spouse
- Policy table has FK to application: `policy.application_id → application.app_id`
- Which party should be linked: applicant or spouse?

**Solution: main_party_type_id**

```csv
system_table_id,         table_name,    main_party_type_id
TBL_SMARTPLUS_APPLICATION, application,   PT_SMARTPLUS_APPLICATION_APPLICANT
TBL_SMARTPLUS_QUOTE,      quote,         PT_SMARTPLUS_QUOTE (business object)
TBL_SMILE_POLICY,         policy,        PT_SMILE_POLICY (business object)
```

**For Person Tables:** Use the "primary" party type (applicant/primary member)
**For Business Objects:** Create a dedicated party_type for FK relationship purposes

**Benefits:**
- Pragmatic solution that covers majority of relationships
- Simple rule: use main_party_type_id for FK lookups
- Non-main parties still linked through same-row relationships (form clusters)

### 6. **Bronze Ingestion Logic**

**For Pattern 1 (Column-Subset):**
```python
# Read application row A001
# Create 2 SOURCE_PARTY records from ONE row:
SOURCE_PARTY[1]: party_type=smartplus.application.applicant, source_record_id=A001
SOURCE_PARTY[2]: party_type=smartplus.application.spouse,    source_record_id=A001

# Extract attributes for each party:
RAW_ATTRIBUTE[applicant]: column_id → applicant_first_name mapping
RAW_ATTRIBUTE[spouse]:     column_id → spouse_first_name mapping

# Create same-row relationship:
RELATIONSHIP: from=SOURCE_PARTY[1], to=SOURCE_PARTY[2], 
              metadata_party_type_relationship_id=PTR_APP_APPLICANT_SPOUSE
```

**For Pattern 2 (Conditional):**
```python
# Read quote_member row QM001 with relationship_type='Primary'
# Determine party_type via condition_logic in METADATA_COLUMN
# Create 1 SOURCE_PARTY: party_type=smartplus.quote_member.applicant

# Read quote_member row QM002 with relationship_type='Spouse'
# Create 1 SOURCE_PARTY: party_type=smartplus.quote_member.spouse

# These are in DIFFERENT ROWS - no same-row relationship!
```

**For Pattern 3 (Simple/Business Objects):**
```python
# Read quote row Q001
# Use main_party_type_id from METADATA_SYSTEM_TABLE
# Create 1 SOURCE_PARTY: party_type=smartplus.quote, source_record_id=Q001

# No attributes extracted (business objects typically have no person attributes)
# Used for FK relationship lookups
```

**FK Relationship Discovery:**
```python
# For each METADATA_RELATIONSHIP entry (e.g., quote → lead):
# 1. Get main_party_type_id for both tables
# 2. Load and merge source tables on FK columns
# 3. For each matched row:
#    - Find SOURCE_PARTY filtered by main_party_type_id
#    - Create RELATIONSHIP record with metadata_relationship_id
```

---

## Difficulties Encountered

### Difficulty 1: Conceptual Confusion Between Scenarios

**Problem:** Initially implemented quote_member/policy_member as "multiple parties in one row" when they are actually "one party per row with conditional typing."

**Root Cause:** The `relationship_type` column looked like it was defining relationships, but it's actually a **discriminator** that determines which party_type the entire row represents.

**Resolution:**
- Created METADATA_COLUMN entries for discriminator columns with `is_party_type_condition=True`
- Replicated attribute column mappings for each possible party_type
- Reserved METADATA_PARTY_TYPE_RELATIONSHIP exclusively for same-row patterns

### Difficulty 2: NULL party_type for Attributes

**Problem:** Initial metadata had attributes with `party_type=NULL` for tables with conditional party types.

**Why This Failed:**
```
RAW_ATTRIBUTE → METADATA_COLUMN → party_type_id (NOT NULL in data model)
```

Every attribute instance must know which party it belongs to.

**Resolution:**
For tables like quote_member with 3 possible party types, each attribute column generates 3 METADATA_COLUMN rows:
```csv
source_column, party_type
first_name,    smartplus.quote_member.applicant
first_name,    smartplus.quote_member.spouse
first_name,    smartplus.quote_member.dependent
```

Bronze ingestion uses the row's discriminator value to select the correct party_type, then finds the matching METADATA_COLUMN entry.

### Difficulty 3: Misuse of condition_logic

**Problem:** METADATA_PARTY_TYPE_RELATIONSHIP initially had `condition_logic` like:
```
"from.relationship_type='Primary' AND to.relationship_type='Spouse' AND from.quote_id=to.quote_id"
```

**Why This Was Wrong:**
- This logic is trying to find relationships **between different rows**
- METADATA_PARTY_TYPE_RELATIONSHIP is for **same row only**
- The `from.quote_id=to.quote_id` clause is a clear indicator these are different rows

**Resolution:**
- Removed `condition_logic` column entirely from METADATA_PARTY_TYPE_RELATIONSHIP
- Same-row relationships don't need conditions - if two party_types exist in the same table and row, they're related by definition
- Relationships between different rows should use METADATA_RELATIONSHIP (FK-based)

### Difficulty 4: Bronze Ingestion Complexity

**Problem:** Bronze ingestion must handle three fundamentally different scenarios with the same metadata structure.

**Challenge:**
- Pattern 1: One source row → Multiple SOURCE_PARTY records (extract column subsets)
- Pattern 2: One source row → One SOURCE_PARTY record (use whole row, conditional typing)
- Pattern 3: One source row → One SOURCE_PARTY record (simple, use main_party_type_id)

**Implementation:**
```python
is_column_subset = table has multiple party_types in METADATA_COLUMN
has_conditional = table has is_party_type_condition=True in METADATA_COLUMN

if is_column_subset:
    # Pattern 1: Column-subset based
    for each unique party_type in this table:
        if party has non-NULL attributes:
            create SOURCE_PARTY with party_type
            extract attributes from column subset
elif has_conditional:
    # Pattern 2: Conditional
    evaluate condition_logic to determine party_type
    create SOURCE_PARTY with determined party_type
    extract all attribute columns
else:
    # Pattern 3: Simple
    use main_party_type_id from METADATA_SYSTEM_TABLE
    create SOURCE_PARTY with main_party_type_id
```

**Status:** ✅ Implemented in `ingest_bronze_source_party.py`

### Difficulty 5: FK Relationships Without Party Records

**Problem:** METADATA_RELATIONSHIP contained FK relationships between:
- Party tables (lead, quote_member, application)
- Business object tables (quote, policy, claim)

But SOURCE_PARTY only contained person records, so FK relationships to/from business objects returned 0 matches.

**Initial Approach (FAILED):**
Skip relationships where one or both tables had `main_party_type_id=NULL`:
```python
if from_main_party_type_id is None or to_main_party_type_id is None:
    skip_relationship()  # WRONG: Skips 7 out of 8 relationships!
```

**Root Cause:** Business objects (quote, policy, claim) are not people, but they ARE needed for FK relationship linkage.

**Solution: Extend Party Concept to Business Objects**

1. **Created party types for business objects:**
   ```csv
   party_type_id,        party_type
   PT_SMARTPLUS_QUOTE,   smartplus.quote
   PT_SMILE_POLICY,      smile.policy
   PT_SMILE_CLAIM,       smile.claim
   ```

2. **Assigned main_party_type_id to all tables:**
   ```csv
   table_name,    main_party_type_id
   quote,         PT_SMARTPLUS_QUOTE
   policy,        PT_SMILE_POLICY
   claim,         PT_SMILE_CLAIM
   ```

3. **Updated SOURCE_PARTY ingestion to include business objects:**
   - Pattern 3 (Simple): Create one SOURCE_PARTY per row using main_party_type_id
   - Now ingests 7 tables (4 person + 3 business object) → 137 SOURCE_PARTY records

4. **FK relationship ingestion now works:**
   - Uses main_party_type_id to filter SOURCE_PARTY lookups
   - Successfully creates 74 FK-based relationships + 4 semantic relationships = 78 total

**Key Insight:** In MDM, "party" doesn't strictly mean "person" - it means "entity that can participate in relationships". Business objects need representation in SOURCE_PARTY to enable FK-based relationship discovery.

---

## Data Model Alignment

### METADATA_PARTY_TYPE
```csv
party_type_id,                        party_type
# Person party types
PT_SMARTPLUS_LEAD,                    smartplus.lead
PT_SMARTPLUS_APPLICATION_APPLICANT,   smartplus.application.applicant
PT_SMARTPLUS_APPLICATION_SPOUSE,      smartplus.application.spouse
PT_SMARTPLUS_QUOTE_MEMBER_APPLICANT,  smartplus.quote_member.applicant
PT_SMARTPLUS_QUOTE_MEMBER_SPOUSE,     smartplus.quote_member.spouse
PT_SMARTPLUS_QUOTE_MEMBER_DEPENDENT,  smartplus.quote_member.dependent
PT_SMILE_POLICY_MEMBER_PRIMARY,       smile.policy_member.primary
PT_SMILE_POLICY_MEMBER_DEPENDENT,     smile.policy_member.dependent

# Business object party types (for FK relationships)
PT_SMARTPLUS_QUOTE,                   smartplus.quote
PT_SMILE_POLICY,                      smile.policy
PT_SMILE_CLAIM,                       smile.claim
```

### METADATA_COLUMN (Samples)

**Application Table (Column-Subset):**
```csv
source_table,  source_column,         party_type,                          is_attribute
application,   app_id,                NULL,                                False (PK)
application,   applicant_first_name,  smartplus.application.applicant,     True
application,   applicant_dob,         smartplus.application.applicant,     True
application,   spouse_first_name,     smartplus.application.spouse,        True
application,   spouse_dob,            smartplus.application.spouse,        True
```

**Quote Member Table (Conditional):**
```csv
source_table,   source_column,     party_type,                            is_party_type_condition,  condition_logic
quote_member,   qm_id,             NULL,                                  False,                    NULL
quote_member,   relationship_type, NULL,                                  True,                     relationship_type='Primary' → applicant
quote_member,   first_name,        smartplus.quote_member.applicant,      False,                    NULL
quote_member,   first_name,        smartplus.quote_member.spouse,         False,                    NULL
quote_member,   first_name,        smartplus.quote_member.dependent,      False,                    NULL
```

### METADATA_PARTY_TYPE_RELATIONSHIP

```csv
party_type_relationship_id,         from_party_type,                    to_party_type,                    relationship_type,  is_bidirectional,  source_system,  source_table
PTR_SMARTPLUS_APP_APPLICANT_SPOUSE, smartplus.application.applicant,    smartplus.application.spouse,     SPOUSE_OF,          True,              SmartPlus,      application
```

**Note:** Only 1 same-row relationship defined. Cross-row relationships use METADATA_RELATIONSHIP instead.

### METADATA_RELATIONSHIP (Sample)

```csv
relationship_id,           from_system, from_table,     from_column,    to_system,  to_table,     to_column,  relationship_type
REL_QUOTE_LEAD,            SmartPlus,   quote,          lead_id,        SmartPlus,  lead,         lead_id,    BUSINESS_LINK
REL_QUOTE_MEMBER_QUOTE,    SmartPlus,   quote_member,   quote_id,       SmartPlus,  quote,        quote_id,   BUSINESS_LINK
REL_APPLICATION_QUOTE,     SmartPlus,   application,    quote_id,       SmartPlus,  quote,        quote_id,   BUSINESS_LINK
REL_POLICY_APPLICATION,    Smile,       policy,         application_id, SmartPlus,  application,  app_id,     BUSINESS_LINK
REL_POLICY_MEMBER_POLICY,  Smile,       policy_member,  policy_id,      Smile,      policy,       policy_id,  BUSINESS_LINK
```

**Note:** 7 FK-based relationships spanning person-to-person, person-to-business, and business-to-business linkages.

---

## UAT Data and Expected Outputs

### Data Completeness Guarantees

**100% Cluster Coverage:**
- Every party record (person or business object) MUST have a cluster assignment
- Parties linked by business relationships (FK) share clusters
- Parties WITHOUT business links get separate clusters
- Example: S4.1 declined quote vs active policy = 2 separate clusters (same person, no FK link)

**100% Master Entity Coverage (for Person Records):**
- Every person record (Lead, Quote Member, Policy Member) MUST have a master entity
- Matched persons (linked by PII) share multi-party master entities
- Unmatched persons get single-party master entities
- Example: 84 person records → 51 master entities (29 multi-party + 22 single-party)

**Current UAT Statistics:**
```
Total scenarios:            28 (S1.x - S12.x)
Total party records:        155 (all in clusters)
  - Person records:          94 (all have master entities)
  - Business objects:        61
Total clusters:              33
Total master entities:       58
  - Multi-party entities:    36 (matched persons)
  - Single-party entities:   22 (unmatched persons)
Total match evidence:        44 (positive + negative matches)
  - Positive matches:        38
  - Negative/blocking:        6
```

### Expected Output Files

**1. expected_clusters.csv**
- Links party records to clusters via business relationships
- Every party record appears exactly once
- Format: `scenario_id, cluster_id, source_table, source_pk_value`

**2. expected_master_entities.csv**
- Defines unique person entities and their constituent party records
- Every person record appears in exactly one master entity
- Multi-party entities: Persons matched across systems via PII
- Single-party entities: Unmatched persons (one party ID)
- Format: `scenario_id, entity_id, entity_name, source_party_ids (JSON array)`

**3. expected_match_evidence.csv**
- Documents expected PII matching outcomes
- Positive matches: `should_match=True` (same person, have PII overlap)
- Negative matches: `should_match=False` (different persons OR same person but no business link)
- Format: `scenario_id, party_id_1, party_id_2, should_match, reason, confidence`

### Verification Tooling

**verify_scenario_coherence.py**

Validates UAT data integrity:

1. ✅ All person records have master entities
2. ✅ All match evidence parties exist in clusters
3. ✅ Master entities correctly represent transitive closure of matches
4. ✅ Negative matches do NOT share master entities
5. ✅ Entity party IDs exist in clusters

**Usage:**
```bash
python src/uat_data/verify_scenario_coherence.py
```

**Output:** Scenario-by-scenario validation with coherence status

---

## Test Coverage

### Current UAT Data

**Application Table (Pattern 1):**
```csv
app_id, applicant_name, applicant_dob, spouse_name,  spouse_dob
A001,   John Smith,     1985-06-15,    NULL,         NULL         → 1 party
A002,   Sarah Lee,      1982-03-20,    David Lee,    1980-07-10   → 2 parties (same row!)
```

**Quote Member Table (Pattern 2):**
```csv
qm_id, quote_id, name,  relationship_type
QM002, Q002,     Sarah, Primary        → party_type: applicant
QM003, Q002,     David, Spouse         → party_type: spouse
QM004, Q002,     Emma,  Child          → party_type: dependent
```

### UAT Scenario Categories

**S1.x - Basic Scenarios:** Happy path and family quote
**S2.x - Granularity Issues:** Quote-level links and membership numbers
**S3.x - Missing Links:** Orphaned records and broken FK references
**S4.x - Matching Scenarios:** Same person without link, father/son same name
**S5.x - Name Variations:** Fuzzy matching, transposed names
**S7.x - Complex Journeys:** Multi-touch customer journeys
**S8.x - Edge Cases:** Missing PII, duplicates, invalid FKs, large families, Unicode
**S9.x - Performance & Special Characters:** Scale testing
**S10.x - Negative Tests:** Cross-cluster validation
**S11.x - Metadata-Driven:** Conditional types, routing, composite keys
**S12.x - Blocking Rules & Conflicts:** Tests for Silver/Gold matching decisions

### Blocking Rules Scenarios (S12.x)

These scenarios test critical edge cases for entity resolution in the Silver/Gold layers:

**S12.1 - Conflicting HKIDs (Blocking Rule)**
- Same name, DOB, email but **different HKIDs**: C123456(7) vs C999999(9)
- Tests: Should BLOCK match despite other PII similarity
- Use case: Data quality issue detection - different valid IDs = different persons
- Expected: 2 separate master entities, confidence=0.0

**S12.2 - Name Change Over Time (Maiden Name)**
- Maiden name "Thompson" (2020) → Married name "Chen" (2024)
- Same HKID, DOB, email - stable identifiers
- Tests: Should MATCH despite name change using stable identifiers
- Expected: 1 master entity, confidence=0.90

**S12.3 - Gender Conflict (Blocking Rule)**
- Same name, DOB, email, passport but **different gender**: M vs F
- Tests: Should BLOCK or flag for manual review
- Use case: Data entry error or truly different persons
- Expected: 2 separate clusters, 2 separate entities, confidence=0.0

**S12.4 - Multiple ID Types (Allowed)**
- Same person with HKID (E123456) and Passport (K9876543)
- Tests: Different ID types should NOT block - match via other PII
- Use case: Person has multiple valid identification documents
- Expected: 1 master entity, confidence=0.85

**S12.5 - DOB Typo (Review Required)**
- DOB differs by 1 day: 1992-07-15 vs 1992-07-16
- Same HKID, name, email
- Tests: Should MATCH with flag for manual review - likely typo
- Use case: Minor data entry errors in otherwise strong matches
- Expected: 1 master entity, confidence=0.75 (needs review threshold)

### Expected Bronze Output

**SOURCE_PARTY:**
```csv
source_party_id,                         party_type_id,                      source_record_id
# Person parties
SP_SmartPlus_lead_L001,                  PT_SMARTPLUS_LEAD,                  L001
SP_SmartPlus_application_A001_applicant, PT_SMARTPLUS_APPLICATION_APPLICANT, A001
SP_SmartPlus_application_A002_applicant, PT_SMARTPLUS_APPLICATION_APPLICANT, A002
SP_SmartPlus_application_A002_spouse,    PT_SMARTPLUS_APPLICATION_SPOUSE,    A002  ← Same source row!
SP_SmartPlus_quote_member_QM002,         PT_SMARTPLUS_QUOTE_MEMBER_APPLICANT, QM002
SP_SmartPlus_quote_member_QM003,         PT_SMARTPLUS_QUOTE_MEMBER_SPOUSE,    QM003
SP_SmartPlus_quote_member_QM004,         PT_SMARTPLUS_QUOTE_MEMBER_DEPENDENT, QM004

# Business object parties (for FK relationships)
SP_SmartPlus_quote_Q001,                 PT_SMARTPLUS_QUOTE,                 Q001
SP_Smile_policy_P001,                    PT_SMILE_POLICY,                    P001
```

**Total: 137 SOURCE_PARTY records** (92 person + 45 business object)

**RELATIONSHIP:**
```csv
from_party_id,                           to_party_id,                             metadata_relationship_id,          metadata_party_type_relationship_id
# Same-row relationships (4 records)
SP_SmartPlus_application_A002_applicant, SP_SmartPlus_application_A002_spouse,    NULL,                              PTR_SMARTPLUS_APP_APPLICANT_SPOUSE
SP_SmartPlus_application_A002_spouse,    SP_SmartPlus_application_A002_applicant, NULL,                              PTR_SMARTPLUS_APP_APPLICANT_SPOUSE
SP_SmartPlus_application_A003_applicant, SP_SmartPlus_application_A003_spouse,    NULL,                              PTR_SMARTPLUS_APP_APPLICANT_SPOUSE
SP_SmartPlus_application_A003_spouse,    SP_SmartPlus_application_A003_applicant, NULL,                              PTR_SMARTPLUS_APP_APPLICANT_SPOUSE

# FK-based relationships (74 records)
SP_SmartPlus_quote_Q001,                 SP_SmartPlus_lead_L001,                  REL_QUOTE_LEAD,                    NULL
SP_SmartPlus_quote_member_QM001,         SP_SmartPlus_quote_Q001,                 REL_QUOTE_MEMBER_QUOTE,            NULL
SP_SmartPlus_application_A001_applicant, SP_SmartPlus_quote_Q001,                 REL_APPLICATION_QUOTE,             NULL
SP_Smile_policy_P001,                    SP_SmartPlus_application_A001_applicant, REL_POLICY_APPLICATION,            NULL
```

**Total: 78 RELATIONSHIP records** (4 semantic + 74 FK-based)

---

## Implementation Status

### ✅ Completed Features

**1. Bronze SOURCE_PARTY Ingestion**
- ✅ Pattern 1 (Column-Subset): Multiple parties per row
- ✅ Pattern 2 (Conditional): One party per row with discriminator
- ✅ Pattern 3 (Simple): Business objects using main_party_type_id
- ✅ Ingests 7 tables → 137 SOURCE_PARTY records

**2. Bronze RAW_ATTRIBUTE Ingestion**
- ✅ Handles multiple SOURCE_PARTY per source_record_id
- ✅ Correctly extracts column-subset attributes (applicant_*, spouse_*)
- ✅ Supports all 3 ingestion patterns

**3. Bronze RELATIONSHIP Ingestion**
- ✅ Same-row semantic relationships (4 records from METADATA_PARTY_TYPE_RELATIONSHIP)
- ✅ FK-based relationships (74 records from METADATA_RELATIONSHIP)
- ✅ Bridge table relationships (lead → lead_contact → contact_person)
- ✅ Uses main_party_type_id for party selection in FK lookups
- ✅ Supports composite key matching (pipe-separated columns)
- ✅ Total: 78 relationship records

**4. Metadata Architecture**
- ✅ METADATA_SYSTEM_TABLE.main_party_type_id
- ✅ METADATA_RELATIONSHIP.relationship_id
- ✅ METADATA_COLUMN.column_id for referential integrity
- ✅ Party types for business objects (quote, policy, claim)
- ✅ 11 party types total (8 person + 3 business object)
- ✅ Bridge table support for many-to-many relationships

**5. UAT Data Generation & Verification**
- ✅ 28 comprehensive UAT scenarios covering edge cases
- ✅ 155 party records with 100% cluster coverage
- ✅ 94 person records with 100% master entity coverage
- ✅ 58 expected master entities (36 multi-party + 22 single-party)
- ✅ 44 match evidence entries (38 positive + 6 negative/blocking)
- ✅ Automated coherence verification script
- ✅ Validates transitive closure, negative matches, and completeness

**6. Silver Layer - PARTY_CLUSTER**
- ✅ Graph-based clustering using BFS (Breadth-First Search)
- ✅ Treats all relationships as bidirectional for clustering
- ✅ Finds connected components from RELATIONSHIP edges
- ✅ 142 SOURCE_PARTY → 63 clusters (27 multi-party + 36 singleton)
- ✅ Largest cluster: 11 parties
- ✅ 100% coverage verified

---

## Silver/Gold Matching Strategy

### Challenge: Sparse Data in CRM Systems

**Problem:** CRM systems (e.g., SmartPlus) often have **multiple sparse parties** representing the same person:
- Applicant (name, DOB, phone)
- Card holder (name, card_number)
- Contact person (name, email)
- Cheque issuer (name, address)
- Reimbursement person (name, bank_account)

Each party has only 2-3 attributes, but **together** they form a complete profile.

**Traditional Approach Problems:**
- ❌ Ignoring some parties → Lost information
- ❌ Cross-system comparison only → Miss within-system duplicates
- ❌ Naïve all-pairs comparison → 142 parties = 10,011 comparisons

### Solution: Two-Phase Blocking Strategy

#### **Phase 1: Within-Cluster Matching (PRIMARY)**

**Key Insight:** Use `cluster_id` as the primary blocking key

**Why This Works:**
1. ✅ **Business semantics**: Parties linked by contracts (FK relationships) are highly likely to be the same person
2. ✅ **Scoped comparisons**: O(n²) only within cluster, not across entire dataset
3. ✅ **Handles sparse data**: Even with minimal PII, business links create natural boundaries
4. ✅ **Efficient**: Largest cluster = 11 parties = only 55 comparisons

**Algorithm:**
```
For each cluster:
  Get all parties in cluster
  Compare ALL pairs within cluster (cartesian product)
  Run match rules even with sparse PII
  Output: MATCH_EVIDENCE (blocking_keys='CLUSTER')
```

**Example:**
```
Cluster #1 (linked by contract C001):
├─ Lead L001 (name: John Smith, email: john@email.com)
├─ Quote Member QM001 (name: John Smith, DOB: 1985-06-15)
├─ Policy Member PM001 (name: J. Smith, HKID: C123456)
└─ Claim Claimant CL001 (name: John Smith, phone: +852-9999)

Action: Compare ALL 6 pairs within cluster
Result: High probability all are same person (linked by contract)
```

#### **Phase 2: Cross-Cluster Matching (SECONDARY)**

**Purpose:** Find matches across clusters using strong PII blocking keys

**When This Matters:**
- Person has multiple unlinked contracts (same person, separate clusters)
- Data quality issues (broken FK links)
- Cross-system duplicates without business links

**Blocking Keys for Phase 2 (High-Precision Only):**
- `EXACT_HKID`: Different contracts, same HKID
- `EXACT_PASSPORT`: Different contracts, same Passport
- `EXACT_EMAIL`: Different contracts, same Email (if quality is high)

**Important:** Skip pairs already compared in Phase 1 (deduplication)

**Algorithm:**
```
For each strong blocking key:
  Get candidate pairs across ALL parties
  Skip if pair already in seen_pairs (Phase 1)
  Skip if same cluster (handled in Phase 1)
  Run match rules
  Output: MATCH_EVIDENCE (blocking_keys=key_name)
```

### Pair Deduplication Strategy

**Problem:** Different blocking keys may generate the same pairs

**Solution:** Global `seen_pairs` set across both phases

**Benefits:**
- ✅ **Efficiency**: Avoid redundant expensive match rule execution
- ✅ **Tracking**: Know which blocking key(s) generated each pair
- ✅ **Statistics**: Measure blocking key effectiveness and overlap
- ✅ **Clean logic**: Each pair compared exactly once per match rule

**Overhead Analysis:**
```
Memory: O(n) set of tuples (party_id_1, party_id_2)
  - 142 parties, worst case: ~10K pairs = ~160 KB (negligible)
Time: O(1) set lookup per pair
  - ~microseconds vs milliseconds for match rules
  - < 0.1% of total processing time
```

**Implementation:**
```python
seen_pairs = set()  # Global across both phases

# Phase 1: Within-cluster
for cluster in clusters:
    for pair in get_all_pairs_in_cluster(cluster):
        seen_pairs.add(normalize_pair(pair))
        run_match_rules(pair)

# Phase 2: Cross-cluster
for blocking_key in ['EXACT_HKID', 'EXACT_PASSPORT']:
    for pair in get_candidates(blocking_key):
        if pair in seen_pairs:  # Already compared in Phase 1
            continue
        seen_pairs.add(pair)
        run_match_rules(pair)
```

### Comparison Metrics

**Without Cluster Blocking (Naïve):**
```
142 parties total
Comparisons: 142 × 141 / 2 = 10,011 pairs
Even with strong PII keys: thousands of comparisons
```

**With Two-Phase Cluster Blocking (Recommended):**
```
Phase 1: Within-cluster only
  - 63 clusters
  - Largest cluster: 11 parties = 55 comparisons
  - Total Phase 1: ~300-500 comparisons

Phase 2: Cross-cluster (strong PII only)
  - High-precision keys: HKID, Passport, Email
  - Maybe 50-100 additional comparisons
  - Minus duplicates from Phase 1: ~30-80 net new

Total: ~400-600 comparisons (vs 10,011)
Reduction: 95% fewer comparisons
```

### Blocking Rules & Conflict Detection

**Automatic Blocking Rules:**
- **Conflicting HKIDs**: Different valid HKIDs = different persons (S12.1)
- **Gender Conflict**: Same name/DOB but different gender = block or review (S12.3)
- **DOB Temporal Conflict**: DOB difference > 1 year = likely different persons

**When Applied:**
- **DURING** match evidence generation (before running expensive match rules)
- Checked via `MATCH_BLOCKING` table lookup
- If blocked → skip pair entirely (no MATCH_EVIDENCE created)

**Use Cases:**
1. **Automatic blocking**: Rule-based conflict detection (e.g., HKID mismatch)
2. **Manual blocking**: Steward override ("confirmed different persons")
3. **Unlinking**: Break existing incorrect links via `PARTY_TO_ENTITY_LINK` (SCD2)

### Architecture: Evidence vs Resolution

**Key Principle:** Match evidence generation ≠ Entity resolution

**Silver Layer (Evidence Gathering):**
```
INPUT:  SOURCE_PARTY (142 records)
        STANDARDIZED_ATTRIBUTE (linked to SOURCE_PARTY)
        PARTY_CLUSTER (groups SOURCE_PARTY)

PHASE 1 + PHASE 2: Compare SOURCE_PARTY pairs
OUTPUT: MATCH_EVIDENCE (all evidence from both phases)
```

**Gold Layer (Entity Resolution):**
```
INPUT:  MATCH_EVIDENCE (aggregates all evidence)
PROCESS: Find connected components (transitive closure)
OUTPUT: MASTER_ENTITY + PARTY_TO_ENTITY_LINK
```

**No Consolidation Between Phases:**
- Both Phase 1 and Phase 2 work at **SOURCE_PARTY level**
- No intermediate consolidated entities created
- Consolidation happens **once** in Gold layer after all evidence collected

---

## Key Architectural Principles

1. **Party Type = Identity Schema** - Defines which columns constitute one entity's identity in a given context (person or business object)

2. **METADATA_COLUMN is Source of Truth** - Every column must have explicit party_type mapping (or be marked as relationship/PK)

3. **Three Distinct Ingestion Patterns:**
   - **Pattern 1 (Column-Subset):** Multiple parties per row (e.g., applicant + spouse in application)
   - **Pattern 2 (Conditional):** One party per row with discriminator (e.g., quote_member with relationship_type)
   - **Pattern 3 (Simple):** One party per row using main_party_type_id (e.g., business objects)

4. **Two Relationship Discovery Mechanisms:**
   - **Same-Row (Semantic):** METADATA_PARTY_TYPE_RELATIONSHIP - no conditions needed
   - **Cross-Row (FK-Based):** METADATA_RELATIONSHIP - uses main_party_type_id for party selection

5. **main_party_type_id Strategy** - When tables have multiple party types, designate the "primary" one for FK relationships (non-primary parties form clusters via same-row relationships)

6. **Business Objects as Parties** - Business objects (quote, policy, claim) need SOURCE_PARTY representation to enable FK-based relationship discovery

7. **Granularity Preservation** - The system must maintain the finest level of identity granularity to enable accurate matching and relationship discovery

8. **Traceability via IDs** - relationship_id in METADATA_RELATIONSHIP enables complete lineage from relationship instances back to their metadata definitions

---

## Lessons Learned

**1. Don't Assume Row = Party**
The most fundamental assumption in traditional MDM (one row = one entity) breaks down in real-world source systems.

**2. Discriminators ≠ Relationships**
A `relationship_type` column that says "Primary" or "Spouse" is not defining a relationship between entities - it's classifying what type of entity the row represents.

**3. Metadata Drives Everything**
Without correct metadata defining column-to-party mappings, the entire ingestion pipeline produces incorrect results. Metadata accuracy is critical.

**4. Same-Row vs Cross-Row Logic Must Be Separated**
Attempting to use conditional logic to discover relationships between different rows in a "same-row relationship" table is a fundamental architecture error.

**5. Explicit > Implicit**
While it seems redundant to replicate attribute column mappings for each party_type in conditional scenarios, this explicitness prevents ambiguity and ensures data model integrity (NOT NULL constraints on party_type_id).

**6. "Party" Extends Beyond "Person"**
In MDM, a "party" is any entity that can participate in relationships. Business objects (quotes, policies, claims) must be represented as parties in SOURCE_PARTY to enable FK-based relationship discovery. This isn't a workaround - it's a fundamental requirement for cross-table relationship linkage.

**7. main_party_type_id is a Pragmatic Optimization**
When tables have multiple party types (e.g., applicant + spouse), FK relationships can't reference both. The main_party_type_id solution:
- Designates the "primary" party for FK lookups
- Covers the majority of relationships (primary applicant, primary member)
- Non-primary parties still form relationship clusters through same-row semantic links
- Simple to implement and understand

**8. Relationship Metadata Must Be Traceable**
Adding relationship_id to METADATA_RELATIONSHIP enables:
- Complete lineage from relationship instances to their definitions
- Debugging and validation of relationship discovery
- Clear understanding of which metadata rule created each relationship
- Foundation for relationship quality scoring and confidence metrics
