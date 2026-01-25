"""
UAT Data Generator for SVOP MDM System
Generates comprehensive test data using pandas and exports to CSV.

Usage: python generate_uat_data.py
"""

import pandas as pd
from datetime import date, datetime
from pathlib import Path
import json
from uat_scenarios import generate_all_scenarios


def main():
    """Main entry point"""
    # Use project root for output
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / 'data' / 'uat_generation' / 'sources'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Also create expected directory
    expected_dir = project_root / 'data' / 'uat_generation' / 'expected'
    expected_dir.mkdir(exist_ok=True, parents=True)
    
    print("=" * 70)
    print("GENERATING UAT TEST DATA FOR SVOP MDM SYSTEM")
    print("=" * 70)
    
    # Generate all scenario data
    data = generate_all_scenarios()
    
    # Convert to DataFrames
    print("\nCreating DataFrames...")
    datasets = {}
    for key, records in data.items():
        if records:
            datasets[key] = pd.DataFrame(records)
        else:
            datasets[key] = pd.DataFrame()
    
    # Print statistics
    print("\n" + "=" * 70)
    print("DATA GENERATION STATISTICS")
    print("=" * 70)
    print(f"SmartPlus Leads:          {len(datasets['leads']):>4} records")
    print(f"SmartPlus Quotes:         {len(datasets['quotes']):>4} records")
    print(f"SmartPlus Quote Members:  {len(datasets['quote_members']):>4} records")
    print(f"SmartPlus Applications:   {len(datasets['applications']):>4} records")
    print(f"Smile Policies:           {len(datasets['policies']):>4} records")
    print(f"Smile Policy Members:     {len(datasets['policy_members']):>4} records")
    print(f"Smile Claims:             {len(datasets['claims']):>4} records")
    print("-" * 70)
    total = sum(len(df) for key, df in datasets.items() if key not in ['expected_clusters', 'expected_entities', 'expected_matches'])
    print(f"Total Source Records:     {total:>4} records")
    print("=" * 70)
    
    if not datasets['expected_clusters'].empty:
        print(f"Expected Clusters:        {datasets['expected_clusters']['expected_cluster_id'].nunique():>4} unique")
    print(f"Expected Master Entities: {len(datasets['expected_entities']):>4} entities")
    print(f"Expected Match Evidence:  {len(datasets['expected_matches']):>4} matches")
    print("=" * 70)
    
    # Export to CSV
    print(f"\nExporting source files to {output_dir}/...")
    
    source_files = {
        'leads': 'smartplus_lead.csv',
        'quotes': 'smartplus_quote.csv',
        'quote_members': 'smartplus_quote_member.csv',
        'applications': 'smartplus_application.csv',
        'policies': 'smile_policy.csv',
        'policy_members': 'smile_policy_member.csv',
        'claims': 'smile_claim.csv'
    }
    
    for key, filename in source_files.items():
        filepath = output_dir / filename
        datasets[key].to_csv(filepath, index=False, date_format='%Y-%m-%d')
        print(f"  ✓ {filename:40s} ({len(datasets[key]):>4} rows)")
    
    print(f"\nExporting expected files to {expected_dir}/...")
    
    expected_files = {
        'expected_clusters': 'expected_clusters.csv',
        'expected_entities': 'expected_master_entities.csv',
        'expected_matches': 'expected_match_evidence.csv'
    }
    
    for key, filename in expected_files.items():
        filepath = expected_dir / filename
        datasets[key].to_csv(filepath, index=False, date_format='%Y-%m-%d')
        print(f"  ✓ {filename:40s} ({len(datasets[key]):>4} rows)")
    
    print(f"\n✓ All files exported")
    print("\nNext steps:")
    print("1. Review CSV files in data/uat_generation/ folder")
    print("2. Load into your MDM system")
    print("3. Run clustering and matching algorithms")
    print("4. Compare actual results vs expected outcomes")


if __name__ == '__main__':
    main()
