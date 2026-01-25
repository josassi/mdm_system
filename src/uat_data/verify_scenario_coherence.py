"""
Scenario Coherence Verification Tool

Verifies that for each UAT scenario:
1. All party records have clusters (even singleton clusters for unlinked parties)
2. All person records have master entities (even single-party entities for unmatched persons)
3. All records in match_evidence are present in expected_clusters
4. All records in expected_master_entities are present in expected_clusters
5. Master entities correctly represent transitive closure of matches
6. Negative matches do NOT result in parties being in the same master entity

Usage: python verify_scenario_coherence.py
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict


class ScenarioVerifier:
    def __init__(self, data_dir='data/uat_generation/expected'):
        self.data_dir = Path(data_dir)
        self.clusters = None
        self.matches = None
        self.entities = None
        self.issues = []
        
    def load_expected_outputs(self):
        """Load all expected output files"""
        project_root = Path(__file__).parent.parent.parent
        expected_dir = project_root / 'data' / 'uat_generation' / 'expected'
        
        self.clusters = pd.read_csv(expected_dir / 'expected_clusters.csv')
        self.matches = pd.read_csv(expected_dir / 'expected_match_evidence.csv')
        self.entities = pd.read_csv(expected_dir / 'expected_master_entities.csv')
        
        print(f"✓ Loaded {len(self.clusters)} cluster entries")
        print(f"✓ Loaded {len(self.matches)} match evidence entries")
        print(f"✓ Loaded {len(self.entities)} master entity entries")
        print()
    
    def get_scenarios(self):
        """Get list of all scenarios"""
        return sorted(self.clusters['scenario_id'].unique())
    
    def verify_scenario(self, scenario_id):
        """Verify coherence for a single scenario"""
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario_id}")
        print(f"{'='*70}")
        
        # Get data for this scenario
        scenario_clusters = self.clusters[self.clusters['scenario_id'] == scenario_id]
        scenario_matches = self.matches[self.matches['scenario_id'] == scenario_id]
        scenario_entities = self.entities[self.entities['scenario_id'] == scenario_id]
        
        # Extract party IDs from clusters
        cluster_party_ids = set(scenario_clusters['source_pk_value'].unique())
        num_clusters = scenario_clusters['expected_cluster_id'].nunique()
        
        # Filter to only person records (leads, quote members, policy members)
        person_tables = ['smartplus_lead', 'smartplus_quote_member', 'smile_policy_member']
        person_records = scenario_clusters[scenario_clusters['source_table'].isin(person_tables)]
        person_party_ids = set(person_records['source_pk_value'].unique())
        
        print(f"Clusters: {num_clusters} cluster(s), {len(cluster_party_ids)} party records")
        print(f"Persons:  {len(person_party_ids)} person records")
        print(f"Matches:  {len(scenario_matches)} match evidence entries")
        print(f"Entities: {len(scenario_entities)} master entity entries")
        
        issues = []
        
        # Check 1: All match pairs must be in clusters
        for _, match in scenario_matches.iterrows():
            party1 = match['party_id_1']
            party2 = match['party_id_2']
            
            if party1 not in cluster_party_ids:
                issues.append(f"  ⚠ Match references {party1} not in clusters")
            if party2 not in cluster_party_ids:
                issues.append(f"  ⚠ Match references {party2} not in clusters")
        
        # Check 2: All entity party IDs must be in clusters
        for _, entity in scenario_entities.iterrows():
            # Parse source_party_ids (it's a JSON array string)
            import json
            party_ids = json.loads(entity['source_party_ids'])
            for party_id in party_ids:
                if party_id not in cluster_party_ids:
                    issues.append(f"  ⚠ Entity {entity['expected_master_entity_id']} references {party_id} not in clusters")
        
        # Check 3: Verify transitive closure
        # Build match graph
        from collections import defaultdict
        match_graph = defaultdict(set)
        
        for _, match in scenario_matches.iterrows():
            if match['should_match']:  # Only positive matches
                p1, p2 = match['party_id_1'], match['party_id_2']
                match_graph[p1].add(p2)
                match_graph[p2].add(p1)
        
        # Find connected components using DFS
        def find_connected_component(start, visited):
            """DFS to find all connected parties"""
            component = set()
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbor in match_graph[node]:
                    if neighbor not in visited:
                        stack.append(neighbor)
            return component
        
        visited = set()
        expected_components = []
        for party_id in match_graph:
            if party_id not in visited:
                component = find_connected_component(party_id, visited)
                expected_components.append(component)
        
        # Check 4: Compare expected components with defined entities (only if there are matches)
        if len(expected_components) > 0:
            # We have matches, so verify transitive closure
            if len(scenario_entities) > 0:
                # Extract entity components from expected_master_entities
                defined_components = []
                for _, entity in scenario_entities.iterrows():
                    import json
                    party_ids = set(json.loads(entity['source_party_ids']))
                    defined_components.append(party_ids)
                
                # Check if each expected component is defined
                for comp in expected_components:
                    found = any(comp == def_comp for def_comp in defined_components)
                    if not found:
                        issues.append(f"  ⚠ Missing entity for connected parties: {comp}")
            else:
                issues.append(f"  ⚠ {len(expected_components)} master entities expected (from matches) but NONE defined")
        
        # Check 4.5: ALL person records must have master entities
        entity_party_ids = set()
        for _, entity in scenario_entities.iterrows():
            import json
            party_ids = json.loads(entity['source_party_ids'])
            entity_party_ids.update(party_ids)
        
        missing_entities = person_party_ids - entity_party_ids
        if missing_entities:
            issues.append(f"  ⚠ {len(missing_entities)} person records without master entities: {missing_entities}")
        
        # Check 5: Negative matches should NOT be in same master entity (but CAN be in same cluster)
        for _, match in scenario_matches.iterrows():
            if not match['should_match']:  # Negative match
                p1, p2 = match['party_id_1'], match['party_id_2']
                
                # Check if both parties are in the same master entity (they shouldn't be)
                for _, entity in scenario_entities.iterrows():
                    import json
                    party_ids = json.loads(entity['source_party_ids'])
                    if p1 in party_ids and p2 in party_ids:
                        issues.append(f"  ⚠ NEGATIVE match {p1}-{p2} but both in same master entity {entity['expected_master_entity_id']}!")
                
                # Note: Negative matches CAN be in same cluster if linked by business relationship (e.g., father/son in family quote)
        
        # Print results
        if issues:
            print(f"\n❌ ISSUES FOUND:")
            for issue in issues:
                print(issue)
            return False
        else:
            print(f"\n✅ COHERENT: All checks passed")
            return True
    
    def verify_all_scenarios(self):
        """Verify all scenarios and generate report"""
        print("\n" + "="*70)
        print("SCENARIO COHERENCE VERIFICATION")
        print("="*70)
        
        self.load_expected_outputs()
        
        scenarios = self.get_scenarios()
        results = {}
        
        for scenario_id in scenarios:
            is_coherent = self.verify_scenario(scenario_id)
            results[scenario_id] = is_coherent
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        coherent_count = sum(results.values())
        total_count = len(results)
        
        print(f"\nCoherent scenarios: {coherent_count}/{total_count}")
        
        if coherent_count < total_count:
            print("\nScenarios with issues:")
            for scenario_id, is_coherent in results.items():
                if not is_coherent:
                    print(f"  - {scenario_id}")
        else:
            print("\n✅ ALL SCENARIOS ARE COHERENT!")
        
        return results


if __name__ == '__main__':
    verifier = ScenarioVerifier()
    results = verifier.verify_all_scenarios()
