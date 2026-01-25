"""
UAT Metadata Generator
Generates metadata CSV files that define how source systems map to MDM structures.
"""

import pandas as pd
from pathlib import Path
import uuid


def generate_uuid(prefix):
    """Generate deterministic UUID based on prefix for reproducibility"""
    return f"{prefix}_{str(uuid.uuid5(uuid.NAMESPACE_DNS, prefix))[:8]}"


def generate_metadata_system():
    """Generate METADATA_SYSTEM table"""
    return [
        {'system_id': 'SYS_SMARTPLUS', 'system_name': 'SmartPlus'},
        {'system_id': 'SYS_SMILE', 'system_name': 'Smile'},
    ]


def generate_metadata_system_table():
    """
    Generate METADATA_SYSTEM_TABLE table.
    
    main_party_type_id: Designates which party_type to use for FK-based relationships.
    - For party tables with single party_type: use that type
    - For party tables with multiple party_types: use the "primary" one (applicant/primary)
    - For non-party tables (business objects): NULL
    """
    return [
        {'system_table_id': 'TBL_SMARTPLUS_LEAD', 'system_id': 'SYS_SMARTPLUS', 'table_name': 'lead', 
         'main_party_type_id': 'PT_SMARTPLUS_LEAD'},
        {'system_table_id': 'TBL_SMARTPLUS_QUOTE', 'system_id': 'SYS_SMARTPLUS', 'table_name': 'quote', 
         'main_party_type_id': 'PT_SMARTPLUS_QUOTE'},  # Business object
        {'system_table_id': 'TBL_SMARTPLUS_QUOTE_MEMBER', 'system_id': 'SYS_SMARTPLUS', 'table_name': 'quote_member', 
         'main_party_type_id': 'PT_SMARTPLUS_QUOTE_MEMBER_APPLICANT'},  # Primary member
        {'system_table_id': 'TBL_SMARTPLUS_APPLICATION', 'system_id': 'SYS_SMARTPLUS', 'table_name': 'application', 
         'main_party_type_id': 'PT_SMARTPLUS_APPLICATION_APPLICANT'},  # Applicant is primary
        {'system_table_id': 'TBL_SMARTPLUS_CONTACT_PERSON', 'system_id': 'SYS_SMARTPLUS', 'table_name': 'contact_person', 
         'main_party_type_id': 'PT_SMARTPLUS_CONTACT_PERSON'},  # Person party type
        {'system_table_id': 'TBL_SMARTPLUS_LEAD_CONTACT', 'system_id': 'SYS_SMARTPLUS', 'table_name': 'lead_contact', 
         'main_party_type_id': None},  # Bridge table - no main party (junction only) member
        {'system_table_id': 'TBL_SMILE_POLICY', 'system_id': 'SYS_SMILE', 'table_name': 'policy', 
         'main_party_type_id': 'PT_SMILE_POLICY'},  # Business object
        {'system_table_id': 'TBL_SMILE_POLICY_MEMBER', 'system_id': 'SYS_SMILE', 'table_name': 'policy_member', 
         'main_party_type_id': 'PT_SMILE_POLICY_MEMBER_PRIMARY'},  # Primary member
        {'system_table_id': 'TBL_SMILE_CLAIM', 'system_id': 'SYS_SMILE', 'table_name': 'claim', 
         'main_party_type_id': 'PT_SMILE_CLAIM'},  # Business object
    ]


def generate_metadata_party_type():
    """Generate METADATA_PARTY_TYPE table - one per unique identity schema"""
    return [
        # SmartPlus party types (people)
        {'party_type_id': 'PT_SMARTPLUS_LEAD', 'party_type': 'smartplus.lead'},
        {'party_type_id': 'PT_SMARTPLUS_APPLICATION_APPLICANT', 'party_type': 'smartplus.application.applicant'},
        {'party_type_id': 'PT_SMARTPLUS_APPLICATION_SPOUSE', 'party_type': 'smartplus.application.spouse'},
        {'party_type_id': 'PT_SMARTPLUS_QUOTE_MEMBER_APPLICANT', 'party_type': 'smartplus.quote_member.applicant'},
        {'party_type_id': 'PT_SMARTPLUS_QUOTE_MEMBER_SPOUSE', 'party_type': 'smartplus.quote_member.spouse'},
        {'party_type_id': 'PT_SMARTPLUS_QUOTE_MEMBER_DEPENDENT', 'party_type': 'smartplus.quote_member.dependent'},
        
        # SmartPlus business objects (for FK relationships)
        {'party_type_id': 'PT_SMARTPLUS_QUOTE', 'party_type': 'smartplus.quote'},
        
        # SmartPlus contact persons (for bridge table relationships)
        {'party_type_id': 'PT_SMARTPLUS_CONTACT_PERSON', 'party_type': 'smartplus.contact_person'},
        
        # Smile party types (people)
        {'party_type_id': 'PT_SMILE_POLICY_MEMBER_PRIMARY', 'party_type': 'smile.policy_member.primary'},
        {'party_type_id': 'PT_SMILE_POLICY_MEMBER_DEPENDENT', 'party_type': 'smile.policy_member.dependent'},
        
        # Smile business objects (for FK relationships)
        {'party_type_id': 'PT_SMILE_POLICY', 'party_type': 'smile.policy'},
        {'party_type_id': 'PT_SMILE_CLAIM', 'party_type': 'smile.claim'},
    ]


def generate_metadata_relationship_type():
    """Generate METADATA_RELATIONSHIP_TYPE table"""
    return [
        {'relationship_type_id': 'RT_BUSINESS_LINK', 'type_name': 'BUSINESS_LINK', 'binding_strength': 'HARD'},
        {'relationship_type_id': 'RT_MEMBERSHIP_LINK', 'type_name': 'MEMBERSHIP_LINK', 'binding_strength': 'HARD'},
        {'relationship_type_id': 'RT_SPOUSE_OF', 'type_name': 'SPOUSE_OF', 'binding_strength': 'STRONG'},
        {'relationship_type_id': 'RT_DEPENDENT_OF', 'type_name': 'DEPENDENT_OF', 'binding_strength': 'STRONG'},
    ]


def generate_metadata_attribute_type():
    """Generate METADATA_ATTRIBUTE_TYPE table"""
    return [
        {'attribute_type_id': 'ATTR_FIRST_NAME', 'attribute_name': 'First Name', 'is_pii': True, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_LAST_NAME', 'attribute_name': 'Last Name', 'is_pii': True, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_DOB', 'attribute_name': 'Date of Birth', 'is_pii': True, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_EMAIL', 'attribute_name': 'Email Address', 'is_pii': True, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_PHONE', 'attribute_name': 'Phone Number', 'is_pii': True, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_ADDRESS', 'attribute_name': 'Address', 'is_pii': True, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_GOV_ID', 'attribute_name': 'Government ID', 'is_pii': True, 'requires_classification': True},
        {'attribute_type_id': 'ATTR_GOV_ID_TYPE', 'attribute_name': 'Government ID Type', 'is_pii': False, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_GENDER', 'attribute_name': 'Gender', 'is_pii': False, 'requires_classification': False},
        {'attribute_type_id': 'ATTR_RELATIONSHIP_TYPE', 'attribute_name': 'Relationship Type', 'is_pii': False, 'requires_classification': False},
    ]


def generate_metadata_attribute_subtype():
    """Generate METADATA_ATTRIBUTE_SUBTYPE table"""
    return [
        {'attribute_subtype_id': 'SUB_HKID', 'attribute_type_id': 'ATTR_GOV_ID', 'subtype_name': 'HKID'},
        {'attribute_subtype_id': 'SUB_PASSPORT', 'attribute_type_id': 'ATTR_GOV_ID', 'subtype_name': 'Passport'},
        {'attribute_subtype_id': 'SUB_DRIVERS_LICENSE', 'attribute_type_id': 'ATTR_GOV_ID', 'subtype_name': 'Drivers License'},
    ]


def _generate_column_id(system, table, column):
    """Generate a unique column_id from system, table, and column names"""
    return f"COL_{system.upper().replace(' ', '_')}_{table.upper()}_{column.upper()}"


def generate_column_mappings():
    """Generate column-to-attribute mappings for all source tables"""
    mappings = []
    
    # SmartPlus - Lead table (party_type: smartplus.lead)
    mappings.extend([
        {'column_id': _generate_column_id('SmartPlus', 'lead', 'lead_id'),
         'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'lead_id', 
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None, 
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'first_name',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_FIRST_NAME', 'priority': 2, 'quality_score': 0.85, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'last_name',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_LAST_NAME', 'priority': 2, 'quality_score': 0.85, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'date_of_birth',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_DOB', 'priority': 2, 'quality_score': 0.90, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'email',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_EMAIL', 'priority': 2, 'quality_score': 0.80, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'phone',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_PHONE', 'priority': 2, 'quality_score': 0.75, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'address',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_ADDRESS', 'priority': 2, 'quality_score': 0.80, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'gov_id_number',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_GOV_ID', 'priority': 2, 'quality_score': 0.90, 'is_pii': True, 'requires_classification': True},
        {'source_system': 'SmartPlus', 'source_table': 'lead', 'source_column': 'gov_id_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.lead',
         'attribute_type': 'ATTR_GOV_ID_TYPE', 'priority': 2, 'quality_score': 0.90, 'is_pii': False, 'requires_classification': False},
    ])
    
    # SmartPlus - Quote table
    mappings.extend([
        {'source_system': 'SmartPlus', 'source_table': 'quote', 'source_column': 'quote_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'quote', 'source_column': 'lead_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'quote', 'source_column': 'contract_number',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': 'contract_number', 'condition_logic': 'LEN(contract_number)==8',
         'party_type': None, 'attribute_type': None, 'priority': None, 'quality_score': 0.95, 'is_pii': False, 'requires_classification': False},
    ])
    
    # SmartPlus - Quote Member table (with conditional party types)
    mappings.extend([
        {'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': 'qm_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': 'quote_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': 'member_sequence',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        # Conditional party type based on relationship_type
        {'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': 'relationship_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': True,
         'condition_column': 'relationship_type', 'condition_logic': "relationship_type='Primary'",
         'party_type': 'smartplus.quote_member.applicant', 'attribute_type': 'ATTR_RELATIONSHIP_TYPE',
         'priority': 2, 'quality_score': 0.90, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': 'relationship_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': True,
         'condition_column': 'relationship_type', 'condition_logic': "relationship_type='Spouse'",
         'party_type': 'smartplus.quote_member.spouse', 'attribute_type': 'ATTR_RELATIONSHIP_TYPE',
         'priority': 2, 'quality_score': 0.90, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': 'relationship_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': True,
         'condition_column': 'relationship_type', 'condition_logic': "relationship_type='Child'",
         'party_type': 'smartplus.quote_member.dependent', 'attribute_type': 'ATTR_RELATIONSHIP_TYPE',
         'priority': 2, 'quality_score': 0.90, 'is_pii': False, 'requires_classification': False},
    ])
    
    # SmartPlus - Quote Member attributes (replicate for each party_type)
    quote_member_attrs = [
        ('first_name', 'ATTR_FIRST_NAME', 0.80, True, False),
        ('last_name', 'ATTR_LAST_NAME', 0.80, True, False),
        ('date_of_birth', 'ATTR_DOB', 0.85, True, False),
        ('email', 'ATTR_EMAIL', 0.75, True, False),
        ('phone', 'ATTR_PHONE', 0.70, True, False),
        ('gov_id_number', 'ATTR_GOV_ID', 0.90, True, True),
        ('gov_id_type', 'ATTR_GOV_ID_TYPE', 0.90, False, False),
        ('gender', 'ATTR_GENDER', 0.85, False, False),
    ]
    
    # Generate metadata_column rows for all 3 party types
    for party_type in ['smartplus.quote_member.applicant', 'smartplus.quote_member.spouse', 'smartplus.quote_member.dependent']:
        for col, attr, qual, is_pii, req_class in quote_member_attrs:
            mappings.append({
                'source_system': 'SmartPlus', 'source_table': 'quote_member', 'source_column': col,
                'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
                'condition_column': None, 'condition_logic': None, 'party_type': party_type,
                'attribute_type': attr, 'priority': 2, 'quality_score': qual, 
                'is_pii': is_pii, 'requires_classification': req_class
            })
    
    mappings.extend([
    ])
    
    # SmartPlus - Application table (MULTIPLE PARTIES IN ONE ROW)
    # Primary key
    mappings.append({
        'source_system': 'SmartPlus', 'source_table': 'application', 'source_column': 'app_id',
        'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
        'condition_column': None, 'condition_logic': None, 'party_type': None,
        'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False
    })
    
    # Relationship columns
    mappings.extend([
        {'source_system': 'SmartPlus', 'source_table': 'application', 'source_column': 'quote_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'application', 'source_column': 'contract_number',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
    ])
    
    # Applicant columns (party_type: smartplus.application.applicant)
    applicant_attrs = [
        ('applicant_first_name', 'ATTR_FIRST_NAME', 0.90, True, False),
        ('applicant_last_name', 'ATTR_LAST_NAME', 0.90, True, False),
        ('applicant_dob', 'ATTR_DOB', 0.95, True, False),
        ('applicant_email', 'ATTR_EMAIL', 0.85, True, False),
        ('applicant_phone', 'ATTR_PHONE', 0.80, True, False),
        ('applicant_gov_id', 'ATTR_GOV_ID', 0.95, True, True),
    ]
    for col, attr, qual, is_pii, req_class in applicant_attrs:
        mappings.append({
            'source_system': 'SmartPlus', 'source_table': 'application', 'source_column': col,
            'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
            'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.application.applicant',
            'attribute_type': attr, 'priority': 1, 'quality_score': qual,
            'is_pii': is_pii, 'requires_classification': req_class
        })
    
    # Spouse columns (party_type: smartplus.application.spouse)
    spouse_attrs = [
        ('spouse_first_name', 'ATTR_FIRST_NAME', 0.90, True, False),
        ('spouse_last_name', 'ATTR_LAST_NAME', 0.90, True, False),
        ('spouse_dob', 'ATTR_DOB', 0.95, True, False),
        ('spouse_email', 'ATTR_EMAIL', 0.85, True, False),
        ('spouse_phone', 'ATTR_PHONE', 0.80, True, False),
        ('spouse_gov_id', 'ATTR_GOV_ID', 0.95, True, True),
    ]
    for col, attr, qual, is_pii, req_class in spouse_attrs:
        mappings.append({
            'source_system': 'SmartPlus', 'source_table': 'application', 'source_column': col,
            'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
            'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.application.spouse',
            'attribute_type': attr, 'priority': 1, 'quality_score': qual,
            'is_pii': is_pii, 'requires_classification': req_class
        })
    
    # SmartPlus - Contact_Person table (person party type with PII)
    mappings.extend([
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'contact_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'first_name',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_FIRST_NAME', 'priority': 2, 'quality_score': 0.85, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'last_name',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_LAST_NAME', 'priority': 2, 'quality_score': 0.85, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'date_of_birth',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_DOB', 'priority': 2, 'quality_score': 0.90, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'email',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_EMAIL', 'priority': 2, 'quality_score': 0.80, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'phone',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_PHONE', 'priority': 2, 'quality_score': 0.75, 'is_pii': True, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'gov_id_number',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_GOV_ID', 'priority': 2, 'quality_score': 0.90, 'is_pii': True, 'requires_classification': True},
        {'source_system': 'SmartPlus', 'source_table': 'contact_person', 'source_column': 'gov_id_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': 'smartplus.contact_person',
         'attribute_type': 'ATTR_GOV_ID_TYPE', 'priority': 2, 'quality_score': 0.90, 'is_pii': False, 'requires_classification': False},
    ])
    
    # SmartPlus - Lead_Contact table (bridge table - no party_type)
    mappings.extend([
        {'source_system': 'SmartPlus', 'source_table': 'lead_contact', 'source_column': 'lc_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead_contact', 'source_column': 'lead_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'SmartPlus', 'source_table': 'lead_contact', 'source_column': 'contact_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
    ])
    
    # Smile - Policy table
    mappings.extend([
        {'source_system': 'Smile', 'source_table': 'policy', 'source_column': 'policy_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'policy', 'source_column': 'contract_number',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'policy', 'source_column': 'application_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
    ])
    
    # Smile - Policy Member table (with conditional party types)
    mappings.extend([
        {'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': 'pm_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': 'policy_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': 'contract_number',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': 'member_number',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        # Conditional party type
        {'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': 'relationship_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': True,
         'condition_column': 'relationship_type', 'condition_logic': "relationship_type='Primary'",
         'party_type': 'smile.policy_member.primary', 'attribute_type': 'ATTR_RELATIONSHIP_TYPE',
         'priority': 1, 'quality_score': 0.95, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': 'relationship_type',
         'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': True,
         'condition_column': 'relationship_type', 'condition_logic': "relationship_type IN ('Spouse','Child','Dependent')",
         'party_type': 'smile.policy_member.dependent', 'attribute_type': 'ATTR_RELATIONSHIP_TYPE',
         'priority': 1, 'quality_score': 0.95, 'is_pii': False, 'requires_classification': False},
    ])
    
    # Smile - Policy Member attributes (replicate for each party_type)
    policy_member_attrs = [
        ('first_name', 'ATTR_FIRST_NAME', 0.95, True, False),
        ('last_name', 'ATTR_LAST_NAME', 0.95, True, False),
        ('date_of_birth', 'ATTR_DOB', 0.98, True, False),
        ('email', 'ATTR_EMAIL', 0.90, True, False),
        ('phone', 'ATTR_PHONE', 0.85, True, False),
        ('gov_id_number', 'ATTR_GOV_ID', 0.98, True, True),
        ('gov_id_type', 'ATTR_GOV_ID_TYPE', 0.98, False, False),
        ('gender', 'ATTR_GENDER', 0.95, False, False),
    ]
    
    # Generate metadata_column rows for both party types
    for party_type in ['smile.policy_member.primary', 'smile.policy_member.dependent']:
        for col, attr, qual, is_pii, req_class in policy_member_attrs:
            mappings.append({
                'source_system': 'Smile', 'source_table': 'policy_member', 'source_column': col,
                'is_attribute': True, 'is_relationship': False, 'is_party_type_condition': False,
                'condition_column': None, 'condition_logic': None, 'party_type': party_type,
                'attribute_type': attr, 'priority': 1, 'quality_score': qual,
                'is_pii': is_pii, 'requires_classification': req_class
            })
    
    mappings.extend([
    ])
    
    # Smile - Claim table
    mappings.extend([
        {'source_system': 'Smile', 'source_table': 'claim', 'source_column': 'claim_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'claim', 'source_column': 'policy_id',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
        {'source_system': 'Smile', 'source_table': 'claim', 'source_column': 'claimant_member_number',
         'is_attribute': False, 'is_relationship': True, 'is_party_type_condition': False,
         'condition_column': None, 'condition_logic': None, 'party_type': None,
         'attribute_type': None, 'priority': None, 'quality_score': None, 'is_pii': False, 'requires_classification': False},
    ])
    
    # Add column_id to all mappings that don't have it
    for mapping in mappings:
        if 'column_id' not in mapping:
            mapping['column_id'] = _generate_column_id(
                mapping['source_system'], 
                mapping['source_table'], 
                mapping['source_column']
            )
    
    return mappings


def generate_relationships():
    """Generate cross-table relationship definitions"""
    return [
        # Quote → Lead (guarantees_same_party=TRUE)
        {'relationship_id': 'REL_QUOTE_LEAD',
         'is_bidirectional': False, 'guarantees_same_party': True, 'keeping_granularity_when_used': True,
         'from_column_id': _generate_column_id('SmartPlus', 'quote', 'lead_id'),
         'to_column_id': _generate_column_id('SmartPlus', 'lead', 'lead_id'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 1.0},
        
        # Quote Member → Quote (guarantees_same_party=FALSE, keeping_granularity=FALSE)
        {'relationship_id': 'REL_QUOTE_MEMBER_QUOTE',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('SmartPlus', 'quote_member', 'quote_id'),
         'to_column_id': _generate_column_id('SmartPlus', 'quote', 'quote_id'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 1.0},
        
        # Application → Quote (guarantees_same_party=FALSE, keeping_granularity=FALSE)
        {'relationship_id': 'REL_APPLICATION_QUOTE',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('SmartPlus', 'application', 'quote_id'),
         'to_column_id': _generate_column_id('SmartPlus', 'quote', 'quote_id'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 0.95},
        
        # REMOVED: Application → Quote Member (column quote_member_id doesn't exist in new structure)
        # Application table now has column-subset pattern (applicant + spouse in same row)
        # No direct FK to quote_member anymore
        
        # Policy → Application (cross-system)
        {'relationship_id': 'REL_POLICY_APPLICATION',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('Smile', 'policy', 'application_id'),
         'to_column_id': _generate_column_id('SmartPlus', 'application', 'app_id'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 0.98},
        
        # Policy → Quote (via contract_number)
        {'relationship_id': 'REL_POLICY_QUOTE',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('Smile', 'policy', 'contract_number'),
         'to_column_id': _generate_column_id('SmartPlus', 'quote', 'contract_number'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 0.95},
        
        # Policy Member → Policy
        {'relationship_id': 'REL_POLICY_MEMBER_POLICY',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('Smile', 'policy_member', 'policy_id'),
         'to_column_id': _generate_column_id('Smile', 'policy', 'policy_id'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 1.0},
        
        # REMOVED: Policy Member → Quote Member composite key relationship
        # quote_member table doesn't have contract_number column in UAT data
        
        # Claim → Policy
        {'relationship_id': 'REL_CLAIM_POLICY',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('Smile', 'claim', 'policy_id'),
         'to_column_id': _generate_column_id('Smile', 'policy', 'policy_id'),
         'bridge_table_id': None, 'bridge_column_source_id': None, 'bridge_column_target_id': None,
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 1.0},
        
        # Lead → Contact Person (via bridge table lead_contact)
        # Many-to-many: leads have multiple contacts, contacts work on multiple leads
        # CRITICAL: contact_person has PII and party_type for MDM resolution
        {'relationship_id': 'REL_LEAD_CONTACT_PERSON',
         'is_bidirectional': False, 'guarantees_same_party': False, 'keeping_granularity_when_used': False,
         'from_column_id': _generate_column_id('SmartPlus', 'lead', 'lead_id'),
         'to_column_id': _generate_column_id('SmartPlus', 'contact_person', 'contact_id'),
         'bridge_table_id': 'TBL_SMARTPLUS_LEAD_CONTACT',
         'bridge_column_source_id': _generate_column_id('SmartPlus', 'lead_contact', 'lead_id'),
         'bridge_column_target_id': _generate_column_id('SmartPlus', 'lead_contact', 'contact_id'),
         'relationship_type': 'BUSINESS_LINK', 'confidence_score': 1.0},
    ]


def generate_metadata_party_type_relationship():
    """
    Generate METADATA_PARTY_TYPE_RELATIONSHIP table - same-row semantic relationships.
    
    NOTE: This table is ONLY for multiple parties within THE SAME ROW.
    For relationships between parties in DIFFERENT rows, use METADATA_RELATIONSHIP.
    """
    return [
        # Within Application table - Applicant to Spouse (SAME ROW - no condition needed!)
        {'party_type_relationship_id': 'PTR_SMARTPLUS_APP_APPLICANT_SPOUSE',
         'from_party_type': 'smartplus.application.applicant', 'to_party_type': 'smartplus.application.spouse',
         'relationship_type': 'SPOUSE_OF', 'binding_strength': 'STRONG', 
         'is_hierarchical': False, 'is_bidirectional': True,
         'source_system': 'SmartPlus', 'source_table': 'application'},
    ]


def main():
    """Generate all metadata CSV files"""
    # Use project root for output
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / 'data' / 'uat_generation' / 'metadata'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print("=" * 70)
    print("GENERATING UAT METADATA FILES")
    print("=" * 70)
    
    # Generate all metadata tables
    metadata_system = generate_metadata_system()
    metadata_system_table = generate_metadata_system_table()
    metadata_party_type = generate_metadata_party_type()
    metadata_relationship_type = generate_metadata_relationship_type()
    metadata_attribute_type = generate_metadata_attribute_type()
    metadata_attribute_subtype = generate_metadata_attribute_subtype()
    metadata_column = generate_column_mappings()
    metadata_relationship = generate_relationships()
    metadata_party_type_relationship = generate_metadata_party_type_relationship()
    
    # Convert to DataFrames
    df_system = pd.DataFrame(metadata_system)
    df_system_table = pd.DataFrame(metadata_system_table)
    df_party_type = pd.DataFrame(metadata_party_type)
    df_relationship_type = pd.DataFrame(metadata_relationship_type)
    df_attribute_type = pd.DataFrame(metadata_attribute_type)
    df_attribute_subtype = pd.DataFrame(metadata_attribute_subtype)
    df_column = pd.DataFrame(metadata_column)
    df_relationship = pd.DataFrame(metadata_relationship)
    df_party_type_relationship = pd.DataFrame(metadata_party_type_relationship)
    
    # Print statistics
    print(f"\nMETADATA_SYSTEM:                    {len(df_system):>3} systems")
    print(f"METADATA_SYSTEM_TABLE:              {len(df_system_table):>3} tables")
    print(f"METADATA_PARTY_TYPE:                {len(df_party_type):>3} party types")
    print(f"METADATA_RELATIONSHIP_TYPE:         {len(df_relationship_type):>3} relationship types")
    print(f"METADATA_ATTRIBUTE_TYPE:            {len(df_attribute_type):>3} attribute types")
    print(f"METADATA_ATTRIBUTE_SUBTYPE:         {len(df_attribute_subtype):>3} subtypes")
    print(f"METADATA_COLUMN:                    {len(df_column):>3} columns mapped")
    print(f"METADATA_RELATIONSHIP:              {len(df_relationship):>3} cross-table relationships")
    print(f"METADATA_PARTY_TYPE_RELATIONSHIP:   {len(df_party_type_relationship):>3} within-row relationships")
    
    # Export to CSV - filenames match data model table names
    print(f"\nExporting to {output_dir}/...")
    
    files = [
        ('metadata_system.csv', df_system),
        ('metadata_system_table.csv', df_system_table),
        ('metadata_party_type.csv', df_party_type),
        ('metadata_relationship_type.csv', df_relationship_type),
        ('metadata_attribute_type.csv', df_attribute_type),
        ('metadata_attribute_subtype.csv', df_attribute_subtype),
        ('metadata_column.csv', df_column),
        ('metadata_relationship.csv', df_relationship),
        ('metadata_party_type_relationship.csv', df_party_type_relationship),
    ]
    
    for filename, df in files:
        filepath = output_dir / filename
        df.to_csv(filepath, index=False)
        print(f"  ✓ {filename:<40} ({len(df):>3} rows)")
    
    print("\n✓ All metadata files exported")
    print("\nNext steps:")
    print("1. Review metadata CSV files in uat_data/metadata/ folder")
    print("2. Adjust priority/quality scores if needed")
    print("3. Load metadata into METADATA_* tables")
    print("4. Use metadata to drive Bronze ingestion")


if __name__ == '__main__':
    main()
