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
import argparse


def load_bronze_data(data_dir='data/bronze'):
    """Load SOURCE_PARTY and RELATIONSHIP from Bronze layer (current versions only)"""
    project_root = Path(__file__).parent.parent.parent
    bronze_dir = project_root / data_dir
    
    print("Loading Bronze layer data...")
    all_source_party = pd.read_csv(bronze_dir / 'source_party.csv')
    all_relationship = pd.read_csv(bronze_dir / 'relationship.csv')
    
    # Filter to current versions only
    if 'rec_end_date' in all_source_party.columns:
        source_party = all_source_party[all_source_party['rec_end_date'].isna()].copy()
    else:
        source_party = all_source_party
    
    if 'rec_end_date' in all_relationship.columns:
        current_relationship = all_relationship[all_relationship['rec_end_date'].isna()].copy()
    else:
        current_relationship = all_relationship
    
    print(f"  ✓ Loaded {len(source_party)} current SOURCE_PARTY records (of {len(all_source_party)} total)")
    print(f"  ✓ Loaded {len(current_relationship)} current RELATIONSHIP records (of {len(all_relationship)} total)")
    
    return source_party, current_relationship, all_relationship


def load_existing_clusters(output_dir='data/silver'):
    """Load existing PARTY_CLUSTER for incremental processing"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / output_dir
    cluster_file = silver_dir / 'party_cluster.csv'
    
    if cluster_file.exists():
        existing = pd.read_csv(cluster_file)
        if 'rec_start_date' in existing.columns:
            existing['rec_start_date'] = pd.to_datetime(existing['rec_start_date'], format='ISO8601')
        if 'rec_end_date' in existing.columns:
            existing['rec_end_date'] = pd.to_datetime(existing['rec_end_date'], format='ISO8601')
        
        current_count = existing['rec_end_date'].isna().sum()
        print(f"  ✓ Loaded {len(existing)} existing PARTY_CLUSTER records ({current_count} current)")
        return existing
    else:
        print(f"  No existing PARTY_CLUSTER found")
        return pd.DataFrame()


def detect_affected_parties(all_relationship_df, existing_clusters):
    """
    Identify parties affected by relationship changes.
    
    A party is affected if it appears in a relationship that was recently
    created or closed (rec_end_date is recent or rec_start_date is recent).
    Also detects new parties not in any existing cluster.
    
    Returns:
        set: Party IDs that need re-clustering
    """
    print("\nDetecting affected parties...")
    affected = set()
    
    if existing_clusters.empty:
        # No existing clusters - all parties affected
        return None  # Signal for full recomputation
    
    # Get the latest rec_start_date from existing clusters to determine cutoff
    current_clusters = existing_clusters[existing_clusters['rec_end_date'].isna()]
    if current_clusters.empty:
        return None
    
    last_cluster_time = current_clusters['rec_start_date'].max()
    
    # Find relationships created after last clustering
    if 'rec_start_date' in all_relationship_df.columns:
        all_relationship_df_parsed = all_relationship_df.copy()
        all_relationship_df_parsed['rec_start_date'] = pd.to_datetime(
            all_relationship_df_parsed['rec_start_date'], format='ISO8601')
        if 'rec_end_date' in all_relationship_df_parsed.columns:
            all_relationship_df_parsed['rec_end_date'] = pd.to_datetime(
                all_relationship_df_parsed['rec_end_date'], format='ISO8601')
        
        # New relationships (created after last clustering)
        new_rels = all_relationship_df_parsed[
            all_relationship_df_parsed['rec_start_date'] > last_cluster_time
        ]
        for _, rel in new_rels.iterrows():
            affected.add(rel['from_party_id'])
            affected.add(rel['to_party_id'])
        
        # Closed relationships (closed after last clustering)
        closed_rels = all_relationship_df_parsed[
            (all_relationship_df_parsed['rec_end_date'].notna()) &
            (all_relationship_df_parsed['rec_end_date'] > last_cluster_time)
        ]
        for _, rel in closed_rels.iterrows():
            affected.add(rel['from_party_id'])
            affected.add(rel['to_party_id'])
    
    # Also detect new parties not in any existing cluster
    existing_party_ids = set(current_clusters['party_id'])
    # New parties will be handled by the main algorithm
    
    print(f"  ✓ Found {len(affected)} directly affected parties")
    print(f"    - From new relationships: {len(new_rels) if 'new_rels' in dir() else 0}")
    print(f"    - From closed relationships: {len(closed_rels) if 'closed_rels' in dir() else 0}")
    
    return affected


def identify_affected_clusters(affected_parties, existing_clusters):
    """
    Find all clusters containing any affected party.
    All parties in these clusters need re-clustering.
    
    Returns:
        set: cluster_ids to recompute
        set: all party_ids in affected clusters
    """
    current_clusters = existing_clusters[existing_clusters['rec_end_date'].isna()]
    
    # Find cluster_ids containing affected parties
    affected_cluster_ids = set(
        current_clusters[
            current_clusters['party_id'].isin(affected_parties)
        ]['cluster_id']
    )
    
    # Get ALL parties in those clusters (not just directly affected)
    all_affected_parties = set(
        current_clusters[
            current_clusters['cluster_id'].isin(affected_cluster_ids)
        ]['party_id']
    )
    
    print(f"  ✓ {len(affected_cluster_ids)} clusters affected")
    print(f"  ✓ {len(all_affected_parties)} total parties in affected clusters")
    
    return affected_cluster_ids, all_affected_parties


def map_new_clusters_to_old(new_components, existing_clusters, affected_cluster_ids):
    """
    Map new cluster components to old cluster_ids for stability.
    
    Rules:
    - If >50% of new component came from one old cluster: reuse its cluster_id
    - Otherwise: generate new UUID
    - Each old cluster_id used at most once
    
    Returns:
        dict: {component_index: cluster_id_to_use}
    """
    current_clusters = existing_clusters[existing_clusters['rec_end_date'].isna()]
    cluster_id_map = {}
    used_cluster_ids = set()
    
    for comp_idx, component in enumerate(new_components):
        # Find which old clusters had parties from this component
        party_to_old_cluster = current_clusters[
            current_clusters['party_id'].isin(component)
        ][['party_id', 'cluster_id']]
        
        if party_to_old_cluster.empty:
            # Entirely new component
            cluster_id_map[comp_idx] = str(uuid.uuid4())
            continue
        
        # Count overlap with each old cluster
        overlap_counts = party_to_old_cluster['cluster_id'].value_counts()
        max_overlap_cluster = overlap_counts.idxmax()
        max_overlap_count = overlap_counts.max()
        
        # Reuse if >50% overlap and not already used
        if (max_overlap_count / len(component) > 0.5 and 
            max_overlap_cluster not in used_cluster_ids):
            cluster_id_map[comp_idx] = max_overlap_cluster
            used_cluster_ids.add(max_overlap_cluster)
        else:
            cluster_id_map[comp_idx] = str(uuid.uuid4())
    
    reused = sum(1 for cid in cluster_id_map.values() if cid in affected_cluster_ids)
    print(f"  ✓ Cluster ID stability: {reused} reused, {len(cluster_id_map) - reused} new")
    
    return cluster_id_map


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


def create_party_cluster_records(components, cluster_id_map=None):
    """
    Create PARTY_CLUSTER records from connected components.
    
    Args:
        components: list of sets of party_ids
        cluster_id_map: optional dict {comp_idx: cluster_id} for ID stability
    
    Returns:
        pd.DataFrame: PARTY_CLUSTER records
    """
    print("\nCreating PARTY_CLUSTER records...")
    records = []
    now = datetime.now()
    
    for comp_idx, component in enumerate(components):
        # Use mapped cluster_id if available, else generate new
        if cluster_id_map and comp_idx in cluster_id_map:
            cluster_id = cluster_id_map[comp_idx]
        else:
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
    """Export PARTY_CLUSTER to CSV with SCD2 statistics"""
    project_root = Path(__file__).parent.parent.parent
    silver_dir = project_root / output_dir
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = silver_dir / 'party_cluster.csv'
    party_cluster_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Exported to {output_file}")
    print(f"  Total records: {len(party_cluster_df)}")
    
    # SCD2 statistics
    if 'rec_end_date' in party_cluster_df.columns:
        current_count = party_cluster_df['rec_end_date'].isna().sum()
        historical_count = party_cluster_df['rec_end_date'].notna().sum()
        current_df = party_cluster_df[party_cluster_df['rec_end_date'].isna()]
        cluster_sizes = current_df.groupby('cluster_id').size()
        
        print(f"\nSCD2 Statistics:")
        print(f"  Current assignments:    {current_count:>5}")
        print(f"  Historical assignments: {historical_count:>5}")
        print(f"  Total records:          {len(party_cluster_df):>5}")
        print(f"\nCluster Statistics (current):")
        print(f"  Total clusters:         {len(cluster_sizes):>5}")
        print(f"  Multi-party clusters:   {sum(cluster_sizes > 1):>5}")
        print(f"  Singleton clusters:     {sum(cluster_sizes == 1):>5}")
        print(f"  Largest cluster:        {cluster_sizes.max():>5} parties")


def verify_clustering(source_party_df, party_cluster_df):
    """Verify that clustering is complete and consistent (current versions only)"""
    print("\n" + "="*70)
    print("CLUSTERING VERIFICATION")
    print("="*70)
    
    all_parties = set(source_party_df['source_party_id'])
    
    # Filter to current cluster assignments
    current_clusters = party_cluster_df[party_cluster_df['rec_end_date'].isna()] if 'rec_end_date' in party_cluster_df.columns else party_cluster_df
    clustered_parties = set(current_clusters['party_id'])
    
    # Check 1: All parties have clusters
    missing = all_parties - clustered_parties
    if missing:
        print(f"❌ ERROR: {len(missing)} parties missing from clusters: {list(missing)[:5]}...")
        return False
    else:
        print(f"✅ All {len(all_parties)} parties have cluster assignments")
    
    # Check 2: No duplicate current party assignments
    duplicates = current_clusters['party_id'].duplicated()
    if duplicates.any():
        dup_parties = current_clusters[duplicates]['party_id'].tolist()
        print(f"❌ ERROR: {duplicates.sum()} duplicate party assignments: {dup_parties[:5]}")
        return False
    else:
        print(f"✅ No duplicate cluster assignments")
    
    # Check 3: Cluster statistics
    cluster_sizes = current_clusters.groupby('cluster_id').size()
    print(f"\n✅ Cluster Statistics:")
    print(f"   Total clusters: {len(cluster_sizes)}")
    print(f"   Multi-party clusters: {sum(cluster_sizes > 1)}")
    print(f"   Singleton clusters: {sum(cluster_sizes == 1)}")
    print(f"   Largest cluster: {cluster_sizes.max()} parties")
    print(f"   Average cluster size: {cluster_sizes.mean():.2f} parties")
    
    return True


def incremental_clustering(source_party_df, current_relationship_df, all_relationship_df, existing_clusters):
    """
    Smart incremental clustering with cluster ID stability.
    
    Only re-clusters components affected by relationship changes.
    Preserves unchanged cluster assignments.
    """
    now = datetime.now()
    all_party_ids = set(source_party_df['source_party_id'])
    
    # Step 1: Detect affected parties
    affected_parties = detect_affected_parties(all_relationship_df, existing_clusters)
    
    if affected_parties is None:
        # No existing clusters or can't determine - full recomputation
        print("  → Full recomputation required")
        graph = build_relationship_graph(current_relationship_df)
        components = find_connected_components_bfs(graph, all_party_ids)
        return create_party_cluster_records(components)
    
    if not affected_parties:
        # Check for new parties not in existing clusters
        current_clusters = existing_clusters[existing_clusters['rec_end_date'].isna()]
        existing_party_ids = set(current_clusters['party_id'])
        new_parties = all_party_ids - existing_party_ids
        
        if not new_parties:
            print("  → No changes detected - clusters unchanged")
            return existing_clusters
        
        # Add new parties as affected
        affected_parties = new_parties
        print(f"  ✓ {len(new_parties)} new parties detected")
    
    # Also include new parties not yet clustered
    current_clusters = existing_clusters[existing_clusters['rec_end_date'].isna()]
    existing_party_ids = set(current_clusters['party_id'])
    new_parties = all_party_ids - existing_party_ids
    affected_parties = affected_parties | new_parties
    
    # Step 2: Identify affected clusters
    affected_cluster_ids, all_affected_parties = identify_affected_clusters(
        affected_parties, existing_clusters
    )
    
    # Include new parties in the affected set
    all_affected_parties = all_affected_parties | new_parties
    
    print(f"\n  Total parties to re-cluster: {len(all_affected_parties)}")
    print(f"  Unchanged parties: {len(all_party_ids) - len(all_affected_parties)}")
    
    # Step 3: Build subgraph for affected parties
    # Use current relationships that involve affected parties
    affected_rels = current_relationship_df[
        (current_relationship_df['from_party_id'].isin(all_affected_parties)) |
        (current_relationship_df['to_party_id'].isin(all_affected_parties))
    ]
    
    # Also include parties connected to affected parties via relationships
    # (to correctly compute new connected components)
    extra_parties = set()
    for _, rel in affected_rels.iterrows():
        extra_parties.add(rel['from_party_id'])
        extra_parties.add(rel['to_party_id'])
    all_affected_parties = all_affected_parties | extra_parties
    
    # Re-filter relationships for the expanded set
    affected_rels = current_relationship_df[
        (current_relationship_df['from_party_id'].isin(all_affected_parties)) |
        (current_relationship_df['to_party_id'].isin(all_affected_parties))
    ]
    
    # Step 4: Re-cluster affected subgraph
    graph = build_relationship_graph(affected_rels)
    components = find_connected_components_bfs(graph, all_affected_parties)
    
    # Step 5: Map to old cluster IDs (stability)
    cluster_id_map = map_new_clusters_to_old(components, existing_clusters, affected_cluster_ids)
    
    # Step 6: Close old assignments for affected parties
    existing_clusters = existing_clusters.copy()
    mask = (
        existing_clusters['party_id'].isin(all_affected_parties) &
        existing_clusters['rec_end_date'].isna()
    )
    existing_clusters.loc[mask, 'rec_end_date'] = now
    
    closed_count = mask.sum()
    print(f"\n  ✓ Closed {closed_count} old cluster assignments")
    
    # Step 7: Create new cluster records with stable IDs
    new_records = []
    for comp_idx, component in enumerate(components):
        cluster_id = cluster_id_map[comp_idx]
        for party_id in component:
            new_records.append({
                'party_id': party_id,
                'cluster_id': cluster_id,
                'rec_start_date': now,
                'rec_end_date': None
            })
    
    new_df = pd.DataFrame(new_records)
    print(f"  ✓ Created {len(new_df)} new cluster assignments")
    
    # Step 8: Combine existing (with closures) + new
    result = pd.concat([existing_clusters, new_df], ignore_index=True)
    
    return result


def main(incremental=False):
    """Main clustering pipeline"""
    print("="*70)
    print(f"PARTY CLUSTER COMPUTATION ({'INCREMENTAL' if incremental else 'FULL'})")
    print("="*70)
    
    # Step 1: Load Bronze layer data
    source_party_df, current_relationship_df, all_relationship_df = load_bronze_data()
    all_party_ids = set(source_party_df['source_party_id'])
    
    if incremental:
        # Load existing clusters
        existing_clusters = load_existing_clusters()
        
        if existing_clusters.empty:
            print("\n  No existing clusters - running full computation")
            incremental = False
        else:
            # Incremental clustering
            party_cluster_df = incremental_clustering(
                source_party_df, current_relationship_df, all_relationship_df, existing_clusters
            )
    
    if not incremental:
        # Full recomputation
        graph = build_relationship_graph(current_relationship_df)
        components = find_connected_components_bfs(graph, all_party_ids)
        party_cluster_df = create_party_cluster_records(components)
    
    # Verify clustering
    if verify_clustering(source_party_df, party_cluster_df):
        # Export to CSV
        export_party_cluster(party_cluster_df)
        
        print("\n" + "="*70)
        print(f"✅ CLUSTERING COMPLETE ({'INCREMENTAL' if incremental else 'FULL'})")
        print("="*70)
    else:
        print("\n❌ CLUSTERING VERIFICATION FAILED")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PARTY_CLUSTER Computation')
    parser.add_argument('--incremental', action='store_true',
                        help='Run in incremental mode (smart re-clustering)')
    
    args = parser.parse_args()
    main(incremental=args.incremental)
