import { useCallback, useEffect, useState, useRef } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  NodeChange,
} from 'reactflow'
import 'reactflow/dist/style.css'
import PartyNode from './PartyNode'
import RelationshipDetailsModal from './RelationshipDetailsModal'
import type { Party, MatchEvidence, Blocking, Relationship } from '../types'
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, SimulationNodeDatum } from 'd3-force'

interface SimulationNode extends SimulationNodeDatum {
  id: string
  type: string
  data: any
  position: { x: number; y: number }
}

interface PartyGraphProps {
  parties: Party[]
  matchEvidence: MatchEvidence[]
  blocking: Blocking[]
  relationships: Relationship[]
  focusPartyId: string | null
  onPartySelect: (partyId: string) => void
}

const nodeTypes = {
  partyNode: PartyNode,
}

export default function PartyGraph({
  parties,
  matchEvidence,
  blocking,
  relationships,
  focusPartyId,
  onPartySelect,
}: PartyGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedPartyId, setSelectedPartyId] = useState<string | null>(null)
  const [selectedRelationship, setSelectedRelationship] = useState<Relationship | null>(null)
  const simulationRef = useRef<any>(null)
  const isDraggingRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    const newEdges: Edge[] = []

    // Generate entity color mapping for visual identification
    const entityIds = [...new Set(parties.map(p => (p as any).entity_id).filter(Boolean))]
    const entityColors: Record<string, string> = {}
    const colorPalette = [
      '#3b82f6', // blue
      '#8b5cf6', // purple
      '#ec4899', // pink
      '#f59e0b', // amber
      '#10b981', // emerald
      '#06b6d4', // cyan
      '#f97316', // orange
      '#84cc16', // lime
      '#6366f1', // indigo
      '#14b8a6', // teal
    ]
    entityIds.forEach((entityId, idx) => {
      entityColors[entityId] = colorPalette[idx % colorPalette.length]
    })

    // Create initial nodes with random positions
    const nodeData: SimulationNode[] = parties.map(party => ({
      id: party.party_id,
      type: 'partyNode',
      position: { x: Math.random() * 1000, y: Math.random() * 800 },
      data: {
        party,
        isSelected: selectedPartyId === party.party_id,
        hasConflict: blocking.some(b => 
          b.party_id_1 === party.party_id || b.party_id_2 === party.party_id
        ),
        entityColor: (party as any).entity_id ? entityColors[(party as any).entity_id] : undefined,
        onClick: () => {
          setSelectedPartyId(party.party_id)
          onPartySelect(party.party_id)
        },
      },
      x: Math.random() * 1000,
      y: Math.random() * 800,
    }))

    // Build links for force simulation from relationships
    const links = relationships
      .filter(rel => {
        const fromParty = parties.find(p => p.party_id === rel.from_party_id)
        const toParty = parties.find(p => p.party_id === rel.to_party_id)
        return fromParty && toParty
      })
      .map(rel => ({
        source: rel.from_party_id,
        target: rel.to_party_id,
      }))

    // Stop previous simulation if exists
    if (simulationRef.current) {
      simulationRef.current.stop()
    }

    // Create and start force simulation
    const simulation = forceSimulation(nodeData)
      .force('link', forceLink(links).id((d: any) => d.id).distance(250).strength(0.7))
      .force('charge', forceManyBody().strength(-2000))
      .force('center', forceCenter(500, 400))
      .force('collide', forceCollide(150))
      .alphaDecay(0.05)
      .velocityDecay(0.6)
      .on('tick', () => {
        // Update node positions from simulation
        setNodes(nodeData.map(node => ({
          id: node.id,
          type: node.type,
          position: { 
            x: node.x || 0, 
            y: node.y || 0 
          },
          data: node.data,
          draggable: true,
        })))
      })

    simulationRef.current = simulation

    // Create edges for business relationships
    relationships.forEach(rel => {
      const fromParty = parties.find(p => p.party_id === rel.from_party_id)
      const toParty = parties.find(p => p.party_id === rel.to_party_id)
      
      // Only show if both parties are in the graph
      if (!fromParty || !toParty) return
      
      // Color based on relationship type and confidence
      const confidence = rel.metadata.confidence_score || 0
      let strokeColor = '#3b82f6' // blue
      let labelColor = '#1d4ed8'
      let labelBgColor = '#dbeafe'
      
      if (confidence >= 1.0) {
        strokeColor = '#10b981' // green for high confidence
        labelColor = '#059669'
        labelBgColor = '#d1fae5'
      } else if (confidence < 0.98) {
        strokeColor = '#f97316' // orange for lower confidence
        labelColor = '#ea580c'
        labelBgColor = '#ffedd5'
      }
      
      const relationshipLabel = rel.metadata_relationship_id 
        ? rel.metadata_relationship_id.replace('REL_', '').replace(/_/g, ' ')
        : 'RELATIONSHIP'
      
      newEdges.push({
        id: `rel-${rel.relationship_id}`,
        source: rel.from_party_id,
        target: rel.to_party_id,
        type: 'straight',
        animated: false,
        style: { stroke: strokeColor, strokeWidth: 2.5, cursor: 'pointer' },
        label: relationshipLabel,
        labelStyle: { fill: labelColor, fontSize: 9, fontWeight: 600, cursor: 'pointer' },
        labelBgStyle: { fill: labelBgColor, fillOpacity: 0.9 },
        data: { type: 'relationship', relationship: rel },
      })
    })

    setEdges(newEdges)

    // Cleanup on unmount
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop()
      }
    }
  }, [parties, matchEvidence, blocking, relationships, focusPartyId, onPartySelect, setNodes, setEdges])

  // Update node selection state without resetting layout
  useEffect(() => {
    setNodes(prevNodes => 
      prevNodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          isSelected: selectedPartyId === node.id,
        },
      }))
    )
  }, [selectedPartyId, setNodes])

  // Handle node drag events to update simulation
  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    onNodesChange(changes)
    
    if (!simulationRef.current) return

    changes.forEach(change => {
      if (change.type === 'position' && change.dragging) {
        const node = simulationRef.current.nodes().find((n: SimulationNode) => n.id === change.id)
        if (node && change.position) {
          // Fix node position while dragging
          node.fx = change.position.x
          node.fy = change.position.y
          isDraggingRef.current.add(change.id)
          // Restart simulation with reduced alpha for smooth adjustment
          simulationRef.current.alpha(0.3).restart()
        }
      } else if (change.type === 'position' && !change.dragging && change.id) {
        // Release node when drag ends
        const node = simulationRef.current.nodes().find((n: SimulationNode) => n.id === change.id)
        if (node) {
          node.fx = null
          node.fy = null
          isDraggingRef.current.delete(change.id)
        }
      }
    })
  }, [onNodesChange])

  const handleEdgeClick = useCallback((_event: React.MouseEvent, edge: Edge) => {
    if (edge.data?.type === 'relationship' && edge.data?.relationship) {
      setSelectedRelationship(edge.data.relationship)
    }
  }, [])

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={onEdgesChange}
        onEdgeClick={handleEdgeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
        minZoom={0.1}
        maxZoom={2}
        nodesDraggable={true}
      >
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        <Controls />
      </ReactFlow>
      
      {selectedRelationship && (
        <RelationshipDetailsModal
          relationship={selectedRelationship}
          onClose={() => setSelectedRelationship(null)}
        />
      )}
    </div>
  )
}
