# UAT Test Scenarios for SVOP MDM System

## Source Systems Overview

### System A: SmartPlus (Modern CRM)
- **Lead** - Initial customer contact
- **Quote** - Insurance quote (single or family)
- **Quote_Member** - Individual persons on a quote (1:many with Quote)
- **Application** - Submitted application

### System B: Smile (Legacy Policy System)
- **Policy** - Insurance policy/contract
- **Policy_Member** - Individuals covered under policy (1:many with Policy)
- **Claim** - Insurance claims

## Test Scenario Categories

### Category 1: Basic Business Link Scenarios

#### Scenario 1.1: Perfect Happy Path (Single Person, Full Sales Funnel)
**Description:** One person goes through complete sales journey in SmartPlus, then gets policy in Smile
**Source Data:**
- SmartPlus.Lead: John Smith (lead_id=L001)
- SmartPlus.Quote: Single quote (quote_id=Q001, lead_id=L001)
- SmartPlus.Quote_Member: John Smith (qm_id=QM001, quote_id=Q001)
- SmartPlus.Application: Application (app_id=A001, quote_id=Q001)
- Smile.Policy: Policy (policy_id=P001, application_id=A001)
- Smile.Policy_Member: John Smith (pm_id=PM001, policy_id=P001, member_number=1)

**Expected Outcome:**
- Cluster: All 6 records in one cluster
- Master Entity: 1 master entity (John Smith)
- Relationships Preserved: Lead→Quote→Application→Policy chain
- Match Evidence: Name/DOB matches within cluster

---

#### Scenario 1.2: Family Quote with Multiple Members
**Description:** Family of 3 gets quote together, all become policy members
**Source Data:**
- SmartPlus.Quote: Family quote (quote_id=Q002, lead_id=L002)
- SmartPlus.Quote_Member: 
  - Sarah Lee (qm_id=QM002, quote_id=Q002, relationship_type='Primary')
  - David Lee (qm_id=QM003, quote_id=Q002, relationship_type='Spouse')
  - Emma Lee (qm_id=QM004, quote_id=Q002, relationship_type='Child')
- SmartPlus.Application: (app_id=A002, quote_id=Q002)
- Smile.Policy: (policy_id=P002, application_id=A002, contract_number='C002')
- Smile.Policy_Member:
  - Sarah Lee (pm_id=PM002, policy_id=P002, member_number=1)
  - David Lee (pm_id=PM003, policy_id=P002, member_number=2)
  - Emma Lee (pm_id=PM004, policy_id=P002, member_number=3)

**Expected Outcome:**
- Cluster: All 8 records in one cluster (1 quote + 3 quote_members + 1 app + 1 policy + 3 policy_members)
- Master Entities: 3 (one per person)
- Within-Cluster Matching: QM002↔PM002, QM003↔PM003, QM004↔PM004
- Family Relationships: Sarah(spouse)David, Sarah(parent)Emma, David(parent)Emma

---

### Category 2: Granularity Loss/Preservation Scenarios

#### Scenario 2.1: Quote-Level Link Only (No Member-Level Match)
**Description:** Application links to Quote but not to specific Quote_Member (granularity loss)
**Source Data:**
- SmartPlus.Quote: (quote_id=Q003)
- SmartPlus.Quote_Member: 
  - Alice Wong (qm_id=QM005, quote_id=Q003)
  - Bob Wong (qm_id=QM006, quote_id=Q003)
- SmartPlus.Application: (app_id=A003, quote_id=Q003, quote_member_id=NULL)

**Expected Outcome:**
- Cluster: All 3 records (1 quote + 2 members + 1 app)
- Relationship Metadata: 
  - App→Quote: keeping_granularity_when_used=FALSE, guarantees_same_party=FALSE
  - Quote→QuoteMembers: keeping_granularity_when_used=TRUE, guarantees_same_party=FALSE
- Master Entities: 2 (Alice, Bob) but unclear which one submitted application

---

#### Scenario 2.2: Membership Number Provides Granularity
**Description:** Contract number links families, membership number links individuals
**Source Data:**
- SmartPlus.Quote_Member: 
  - Michael Chen (qm_id=QM007, quote_id=Q004, member_seq=1)
  - Linda Chen (qm_id=QM008, quote_id=Q004, member_seq=2)
- Smile.Policy_Member:
  - Michael Chen (pm_id=PM005, policy_id=P004, contract_number='C004', member_number=1)
  - Linda Chen (pm_id=PM006, policy_id=P004, contract_number='C004', member_number=2)

**Expected Outcome:**
- Bridge via contract_number+member_number preserves person-level granularity
- Relationships: 
  - QM007→PM005 (guarantees_same_party=TRUE)
  - QM008→PM006 (guarantees_same_party=TRUE)
- Master Entities: 2 (Michael, Linda)

---

### Category 3: Missing Business Links

#### Scenario 3.1: Orphaned Policy (No Upstream Quote/Application)
**Description:** Legacy Smile policy exists without corresponding SmartPlus records
**Source Data:**
- Smile.Policy: (policy_id=P005, application_id=NULL)
- Smile.Policy_Member: Robert Taylor (pm_id=PM007, policy_id=P005)

**Expected Outcome:**
- Cluster: Isolated cluster (no links to SmartPlus)
- Synthetic Records: Should system create synthetic Quote/Application? (Design decision)
- Master Entity: 1 (Robert Taylor)

---

#### Scenario 3.2: Broken Link (Application References Non-Existent Quote)
**Description:** Data quality issue - foreign key points to missing record
**Source Data:**
- SmartPlus.Application: (app_id=A004, quote_id='Q999')  -- Q999 doesn't exist
- Smile.Policy: (policy_id=P006, application_id='A004')
- Smile.Policy_Member: Grace Park (pm_id=PM008, policy_id=P006)

**Expected Outcome:**
- Cluster: Contains Application+Policy+PolicyMember (but no Quote)
- Synthetic Records: Create synthetic Quote Q999? Or leave broken?
- Flag: is_synthetic=TRUE if created

---

### Category 4: Cross-System Matching via PII

#### Scenario 4.1: Same Person in Both Systems (No Business Link)
**Description:** Person gets quote in SmartPlus, separately gets policy in Smile (e.g., through broker vs direct)
**Source Data:**
- SmartPlus.Quote_Member: James Wilson, DOB=1985-03-15, Email=james.w@email.com (qm_id=QM009)
- Smile.Policy_Member: James Wilson, DOB=1985-03-15, Email=james.w@email.com (pm_id=PM009)
- NO business links between the records

**Expected Outcome:**
- Clusters: 2 separate clusters (no business relationship)
- Match Evidence: Should NOT be created (different clusters)
- Master Entities: 2 separate entities (respects business boundary)
- **Key Test:** Validates that PII matching doesn't cross cluster boundaries

---

#### Scenario 4.2: Same Name, Different Person (Within Cluster)
**Description:** Two people named "John Smith" in same family quote (father & son)
**Source Data:**
- SmartPlus.Quote: (quote_id=Q005, contract_number='C005')
- SmartPlus.Quote_Member:
  - John Smith Sr (qm_id=QM010, DOB=1960-05-20, quote_id=Q005)
  - John Smith Jr (qm_id=QM011, DOB=1990-05-20, quote_id=Q005)

**Expected Outcome:**
- Cluster: 1 cluster (same quote)
- Master Entities: 2 (different DOB prevents merge)
- Match Evidence: Should NOT be created despite same name
- **Key Test:** DOB dissimilarity prevents false positive

---

### Category 5: Name Variations & Fuzzy Matching

#### Scenario 5.1: Name Spelling Variations (Within Cluster)
**Description:** Same person with slight name variations across systems
**Source Data:**
- SmartPlus.Quote_Member: "Catherine Smith", DOB=1978-11-10, HKID=A123456(7) (qm_id=QM012)
- Smile.Policy_Member: "Cathy Smith", DOB=1978-11-10, HKID=A123456(7) (pm_id=PM010)
- Linked via contract_number='C006'

**Expected Outcome:**
- Cluster: 1 cluster (business link exists)
- Match Evidence: Created due to HKID exact match + name similarity
- Master Entity: 1 (Catherine/Cathy merged)
- Confidence Score: 0.95+ (HKID is strong signal)

---

#### Scenario 5.2: Name Transposition Error
**Description:** First/Last name swapped in one system
**Source Data:**
- SmartPlus.Quote_Member: First="Wei", Last="Zhang", DOB=1982-07-25 (qm_id=QM013)
- Smile.Policy_Member: First="Zhang", Last="Wei", DOB=1982-07-25 (pm_id=PM011)
- Linked via contract_number='C007'

**Expected Outcome:**
- Cluster: 1 cluster
- Match Evidence: Token-level matching detects transposition
- Master Entity: 1 (with data quality flag)

---

### Category 6: Within-Table Multiple Parties

#### Scenario 6.1: Quote_Member Table with Multiple People
**Description:** Already covered in Scenario 1.2, but explicitly test:
- METADATA_RELATIONSHIP.from_the_same_row = TRUE for Quote_Member↔Quote_Member
- All members of same quote should be in same cluster
- Pairwise relationships created

**Source Data:**
- (Use data from Scenario 1.2)

**Expected Outcome:**
- Within-row relationships: QM002↔QM003, QM002↔QM004, QM003↔QM004
- Relationship type: "SAME_QUOTE_MEMBER" or "FAMILY_MEMBER"

---

### Category 7: Complex Multi-System Scenarios

#### Scenario 7.1: Multi-Touch Customer Journey
**Description:** Person appears in multiple touchpoints across systems
**Source Data:**
- SmartPlus.Lead: Susan Martinez (lead_id=L003)
- SmartPlus.Quote: Quote 1 (quote_id=Q007, lead_id=L003) - Declined
- SmartPlus.Quote: Quote 2 (quote_id=Q008, lead_id=L003) - Accepted
- SmartPlus.Quote_Member: Susan Martinez (qm_id=QM014, quote_id=Q008)
- SmartPlus.Application: (app_id=A005, quote_id=Q008)
- Smile.Policy: (policy_id=P007, application_id=A005)
- Smile.Policy_Member: Susan Martinez (pm_id=PM012)
- Smile.Claim: (claim_id=CL001, policy_id=P007, claimant_member_number=1)

**Expected Outcome:**
- Cluster: All 8 records in one cluster
- Master Entity: 1 (Susan Martinez)
- Relationships: Lead→Quote1 (dead end), Lead→Quote2→App→Policy→Claim (successful path)
- Match Evidence: Within-cluster PII matches across touchpoints

---

#### Scenario 7.2: Policy Transfer Between Family Members
**Description:** Policy primary member changes over time (SCD2 test)
**Source Data:**
- T1 (2020): Smile.Policy_Member: Primary=Father (pm_id=PM013, policy_id=P008, relationship_type='Primary', valid_from=2020-01-01)
- T2 (2023): Smile.Policy_Member: Primary=Father (pm_id=PM013, valid_to=2023-06-30)
- T2 (2023): Smile.Policy_Member: Primary=Son (pm_id=PM014, policy_id=P008, relationship_type='Primary', valid_from=2023-07-01)

**Expected Outcome:**
- Cluster: Father, Son, Policy all connected
- Master Entities: 2 (Father, Son)
- Relationship temporal tracking: Primary responsibility transferred
- SCD2: rec_end_date on old RELATIONSHIP record, new record created

---

### Category 8: Edge Cases & Data Quality Issues

#### Scenario 8.1: Missing Critical PII
**Description:** Record has business links but no name/DOB for matching
**Source Data:**
- SmartPlus.Quote_Member: Name=NULL, DOB=NULL, Email=NULL, quote_id=Q009 (qm_id=QM015)
- Smile.Policy_Member: Name="Unknown", DOB=NULL, policy_id=P009 (pm_id=PM015)
- Linked via quote_id/application

**Expected Outcome:**
- Cluster: Records clustered via business link
- Match Evidence: None (no PII to match)
- Master Entities: Cannot merge without PII - stay as separate entities
- Data Quality Flag: missing_critical_pii=TRUE

---

#### Scenario 8.2: Duplicate Quote Members (Data Quality Bug)
**Description:** Same person appears twice in Quote_Member table (source system bug)
**Source Data:**
- SmartPlus.Quote_Member: Peter Johnson, DOB=1975-09-14 (qm_id=QM016, quote_id=Q010)
- SmartPlus.Quote_Member: Peter Johnson, DOB=1975-09-14 (qm_id=QM017, quote_id=Q010)
- Smile.Policy_Member: Peter Johnson, DOB=1975-09-14 (pm_id=PM016, policy_id=P010)

**Expected Outcome:**
- Cluster: All 3 in same cluster (same quote)
- Match Evidence: QM016↔QM017 (duplicate detection), QM016↔PM016, QM017↔PM016
- Master Entity: 1 (all three records merged)
- Data Quality Flag: source_duplicate=TRUE

---

#### Scenario 8.3: Invalid Foreign Key (NULL business link)
**Description:** Application has NULL quote_id
**Source Data:**
- SmartPlus.Application: quote_id=NULL, app_id=A006
- Smile.Policy: application_id=A006, policy_id=P011
- Smile.Policy_Member: pm_id=PM017

**Expected Outcome:**
- Cluster: Application+Policy+PolicyMember (no quote)
- Relationships: Cannot create App→Quote relationship
- Flag: missing_fk=TRUE

---

### Category 9: Boundary Testing

#### Scenario 9.1: Very Large Family (10+ Members)
**Description:** Large family policy to test performance and relationship cardinality
**Source Data:**
- SmartPlus.Quote: quote_id=Q011
- SmartPlus.Quote_Member: 12 family members (QM018-QM029)
- Smile.Policy: policy_id=P012
- Smile.Policy_Member: 12 members (PM018-PM029)

**Expected Outcome:**
- Cluster: 1 cluster with 26 records
- Master Entities: 12
- Within-row relationships: C(12,2) = 66 pairwise Quote_Member relationships
- Match Evidence: 12 cross-system matches

---

#### Scenario 9.2: Long Quote ID (Edge case for matching_value field)
**Description:** Test varchar limits on from_matching_value/to_matching_value
**Source Data:**
- Quote_id: "SUPER_LONG_QUOTE_ID_THAT_EXCEEDS_NORMAL_LENGTH_123456789012345678901234567890"

**Expected Outcome:**
- No truncation or errors
- Matching still works correctly

---

#### Scenario 9.3: Special Characters in Names
**Description:** Names with apostrophes, hyphens, non-Latin characters
**Source Data:**
- Name: "O'Brien-Smith", "José García", "李明", "Müller"

**Expected Outcome:**
- Unicode handling correct
- Matching algorithms handle special characters
- No SQL injection vulnerabilities

---

### Category 10: Negative Test Cases

#### Scenario 10.1: Circular Relationships (Should Not Happen)
**Description:** Invalid data where Quote→Application→Quote (circular FK)
**Source Data:**
- (Intentionally malformed data to test validation)

**Expected Outcome:**
- System detects circular dependency
- Error logged or graph traversal handles gracefully

---

#### Scenario 10.2: Cross-Cluster Match Attempt
**Description:** Verify PII matching doesn't cross cluster boundaries
**Source Data:**
- Cluster A: Quote_Member: "Tom Brown", DOB=1980-01-01, Email=tom@email.com
- Cluster B: Policy_Member: "Tom Brown", DOB=1980-01-01, Email=tom@email.com
- No business link between clusters

**Expected Outcome:**
- Match Evidence: NOT created (different clusters)
- Master Entities: 2 separate entities
- **Critical validation of clustering boundary enforcement**

---

## Summary Statistics for UAT Database

| Metric | Target Count |
|--------|--------------|
| Total Source Records | ~150 |
| Number of Clusters | ~20 |
| Master Entities | ~40 |
| Business Relationships | ~100 |
| Match Evidence Records | ~30 |
| Scenarios Covered | 23 |

## Next Steps

1. Review scenarios with business stakeholders
2. Design source table schemas
3. Generate test data programmatically
4. Create expected outcome tables (for automated testing)
5. Build data generation script
6. Build assertion/validation script
