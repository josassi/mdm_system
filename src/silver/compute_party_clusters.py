"""
PARTY_CLUSTER Computation - First Silver Layer Table

Computes clusters of parties based on relationship graph connectivity.
Uses graph traversal (BFS) to find connected components.

A cluster is the ensemble of all parties linked together by direct or indirect relationships.
Both bidirectional and directional relationships connect parties to the same cluster.
Singleton parties (no relationships) get their own cluster_id.

Algorithm:
1. Load all SOURCE_PARTY and RELATIONSHIP records
2. Build undirected graph (treat all relationships as bidirectional for clustering)
3. Find connected components using BFS
4. Assign cluster_id to each component
5. Handle singleton parties
6. Write to PARTY_CLUSTER table
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime
import uuid


def load_bronze_data(data_dir='data/bronze'):
    """Load SOURCE_PARTY and RELATIONSHIP from Bronze layer"""
    project_root = Path(__file__).parent.parent.parent
    bronze_dir = project_root / data_dir
    
    print("Loading Bronze layer data...")
    source_party = pd.read_csv(bronze_dir / 'source_party.csv')
    relationship = pd.read_csv(bronze_dir / 'relationship.csv')
    
    print(f"  ✓ Loaded {len(source_party)} SOURCE_PARTY records")
    print(f"  ✓ Loaded {len(relationship)} RELATIONSHIP records")
    
    return source_party, relationship


def build_relationship_graph(relationship_df):
    """
    Build undirected graph from relationships.
    
    For clustering purposes, we treat ALL relationships as bidirectional:
    - If A→B exists, both A and B are in the same cluster
    - Directionality doesn't matter for clustering (only for relationship semantics)
    
    Returns:
        dict: adjacency list {party_id: set(connected_party_ids)}
    """
    print("\nBuilding relationship graph...")
    graph = defaultdict(set)
    
    for _, rel in relationship_df.iterrows():
        from_party = rel['from_party_id']
        to_party = rel['to_party_id']
        
        # Add bidirectional edges (undirected graph for clustering)
        graph[from_party].add(to_party)
        graph[to_party].add(from_party)
    
    print(f"  ✓ Built graph with {len(graph)} nodes")
    return graph


def find_connected_components_bfs(graph, all_party_ids):
    """
    Find all connected components using BFS.
    
    Args:
        graph: adjacency list
        all_party_ids: set of all party IDs (including singletons)
    
    Returns:
        list of sets: each set contains party_ids in one cluster
    """
    print("\nFinding connected components...")
    visited = set()
    components = []
    
    # Process parties that have relationships
    for start_party in graph.keys():
        if start_party in visited:
            continue
        
        # BFS to find all connected parties
        component = set()
        queue = deque([start_party])
        
        while queue:
            party_id = queue.popleft()
            if party_id in visited:
                continue
            
            visited.add(party_id)
            component.add(party_id)
            
            # Add all neighbors to queue
            for neighbor in graph[party_id]:
                if neighbor not in visited:
                    queue.append(neighbor)
        
        components.append(component)
    
    # Handle singleton parties (no relationships)
    singleton_parties = all_party_ids - visited
    for singleton_party in singleton_parties:
        components.append({singleton_party})
    
    print(f"  ✓ Found {len(components)} clusters")
    print(f"    - Multi-party clusters: {sum(1 for c in components if len(c) > 1)}")
    print(f"    - Singleton clusters: {sum(1 for c in components if len(c) == 1)}")
    print(f"    - Largest cluster size: {max(len(c) for c in components)}")
    
    return components


def create_party_cluster_records(components):
    """
    Create PARTY_CLUSTER records from connected components.
    
    Each component gets a unique cluster_id.
    Each party in the component gets a record linking it to that cluster.
    
    Returns:
        pd.DataFrame: PARTY_CLUSTER records
    """
    print("\nCreating PARTY_CLUSTER records...")
    records = []
    now = datetime.now()
    
    for component in components:
        # Generate unique cluster_id for this component
        cluster_id = str(uuid.uuid4())
        
        # Create record for each party in this cluster
        for party_id in component:
            records.append({
                'party_id': party_id,
                'cluster_id': cluster_id,
                'rec_start_date': now,
                'rec_end_date': None  # Current version
            })
    
    df = pd.DataFrame(records)
    print(f"  ✓ Created {len(df)} PARTY_CLUSTER records")
    
    return df


def export_party_cluster(party_cluster_df, output_dir='data/silver'):
    """Export PARTY_CLUSTER to CSV"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / output_dir
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = silver_dir / 'party_cluster.csv'
    party_cluster_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Exported to {output_file}")
    print(f"  Total records: {len(party_cluster_df)}")


def verify_clustering(source_party_df, party_cluster_df):
    """Verify that clustering is complete and consistent"""
    print("\n" + "="*70)
    print("CLUSTERING VERIFICATION")
    print("="*70)
    
    all_parties = set(source_party_df['source_party_id'])
    clustered_parties = set(party_cluster_df['party_id'])
    
    # Check 1: All parties have clusters
    missing = all_parties - clustered_parties
    if missing:
        print(f"❌ ERROR: {len(missing)} parties missing from clusters: {missing}")
        return False
    else:
        print(f"✅ All {len(all_parties)} parties have cluster assignments")
    
    # Check 2: No duplicate party assignments
    duplicates = party_cluster_df['party_id'].duplicated()
    if duplicates.any():
        dup_parties = party_cluster_df[duplicates]['party_id'].tolist()
        print(f"❌ ERROR: {duplicates.sum()} duplicate party assignments: {dup_parties}")
        return False
    else:
        print(f"✅ No duplicate cluster assignments")
    
    # Check 3: Cluster statistics
    cluster_sizes = party_cluster_df.groupby('cluster_id').size()
    print(f"\n✅ Cluster Statistics:")
    print(f"   Total clusters: {len(cluster_sizes)}")
    print(f"   Multi-party clusters: {sum(cluster_sizes > 1)}")
    print(f"   Singleton clusters: {sum(cluster_sizes == 1)}")
    print(f"   Largest cluster: {cluster_sizes.max()} parties")
    print(f"   Average cluster size: {cluster_sizes.mean():.2f} parties")
    
    return True


def main():
    """Main clustering pipeline"""
    print("="*70)
    print("PARTY CLUSTER COMPUTATION")
    print("="*70)
    
    # Step 1: Load Bronze layer data
    source_party_df, relationship_df = load_bronze_data()
    all_party_ids = set(source_party_df['source_party_id'])
    
    # Step 2: Build relationship graph
    graph = build_relationship_graph(relationship_df)
    
    # Step 3: Find connected components
    components = find_connected_components_bfs(graph, all_party_ids)
    
    # Step 4: Create PARTY_CLUSTER records
    party_cluster_df = create_party_cluster_records(components)
    
    # Step 5: Verify clustering
    if verify_clustering(source_party_df, party_cluster_df):
        # Step 6: Export to CSV
        export_party_cluster(party_cluster_df)
        
        print("\n" + "="*70)
        print("✅ CLUSTERING COMPLETE")
        print("="*70)
    else:
        print("\n❌ CLUSTERING VERIFICATION FAILED")


if __name__ == '__main__':
    main()
