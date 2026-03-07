import { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import type { Party, MatchEvidence, Blocking, Relationship } from '../types'
import PartyNode from './PartyNode'
import EdgeDetailsModal from './EdgeDetailsModal'

const nodeTypes = {
  party: PartyNode,
}

interface EntityGraphProps {
  parties: Party[]
  matchEvidence: MatchEvidence[]
  blocking: Blocking[]
  relationships: Relationship[]
  selectedPartyId: string | null
  onPartySelect: (partyId: string | null) => void
}

export default function EntityGraph({
  parties,
  matchEvidence,
  blocking,
  relationships,
  selectedPartyId,
  onPartySelect,
}: EntityGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedEdge, setSelectedEdge] = useState<{ party1: Party, party2: Party } | null>(null)

  useEffect(() => {
    const newNodes: Node[] = parties.map((party, index) => {
      const angle = (2 * Math.PI * index) / parties.length
      const radius = Math.max(200, parties.length * 50)
      
      const hasConflict = blocking.some(
        b => b.party_id_1 === party.party_id || b.party_id_2 === party.party_id
      )

      return {
        id: party.party_id,
        type: 'party',
        position: {
          x: 400 + radius * Math.cos(angle),
          y: 300 + radius * Math.sin(angle),
        },
        data: {
          party,
          isSelected: selectedPartyId === party.party_id,
          hasConflict,
          onClick: () => onPartySelect(party.party_id),
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      }
    })

    const newEdges: Edge[] = []

    const calculateMatchPercentage = (p1Id: string, p2Id: string) => {
      const p1 = parties.find(p => p.party_id === p1Id)
      const p2 = parties.find(p => p.party_id === p2Id)
      if (!p1 || !p2) return { match: 0, total: 0 }

      const p1AttrTypes = new Set(p1.attributes.map(a => a.attribute_type))
      const p2AttrTypes = new Set(p2.attributes.map(a => a.attribute_type))
      const commonTypes = Array.from(p1AttrTypes).filter(t => p2AttrTypes.has(t))

      const matches = commonTypes.filter(type => {
        const v1 = p1.attributes.find(a => a.attribute_type === type)?.standardized_value
        const v2 = p2.attributes.find(a => a.attribute_type === type)?.standardized_value
        return v1 && v2 && v1 === v2
      }).length

      return { match: matches, total: commonTypes.length }
    }

    matchEvidence.forEach(evidence => {
      const { match, total } = calculateMatchPercentage(evidence.party_id_1, evidence.party_id_2)
      const matchPct = total > 0 ? (match / total) * 100 : 0
      const mismatchPct = total > 0 ? ((total - match) / total) * 100 : 0

      // Determine source and target based on x position (left to right)
      const node1 = newNodes.find(n => n.id === evidence.party_id_1)
      const node2 = newNodes.find(n => n.id === evidence.party_id_2)
      const isNode1Left = node1 && node2 && node1.position.x < node2.position.x
      
      // Color based on match percentage: green (100%), orange (<100%), red (<50%)
      let strokeColor = '#10b981' // green
      let labelColor = '#059669'
      let labelBgColor = '#d1fae5'
      
      if (matchPct < 50) {
        strokeColor = '#ef4444' // red
        labelColor = '#dc2626'
        labelBgColor = '#fee2e2'
      } else if (matchPct < 100) {
        strokeColor = '#f97316' // orange
        labelColor = '#ea580c'
        labelBgColor = '#ffedd5'
      }
      
      newEdges.push({
        id: `evidence-${evidence.evidence_id}`,
        source: isNode1Left ? evidence.party_id_1 : evidence.party_id_2,
        target: isNode1Left ? evidence.party_id_2 : evidence.party_id_1,
        type: 'smoothstep',
        animated: true,
        style: { stroke: strokeColor, strokeWidth: 2 },
        label: `✓${matchPct.toFixed(0)}% ✗${mismatchPct.toFixed(0)}%`,
        labelStyle: { fill: labelColor, fontSize: 9, fontWeight: 600 },
        labelBgStyle: { fill: labelBgColor, fillOpacity: 0.9 },
        data: { party1Id: evidence.party_id_1, party2Id: evidence.party_id_2 },
      })
    })

    blocking.forEach(block => {
      const { match, total } = calculateMatchPercentage(block.party_id_1, block.party_id_2)
      const matchPct = total > 0 ? (match / total) * 100 : 0
      const mismatchPct = total > 0 ? ((total - match) / total) * 100 : 0

      // Determine source and target based on x position (left to right)
      const node1 = newNodes.find(n => n.id === block.party_id_1)
      const node2 = newNodes.find(n => n.id === block.party_id_2)
      const isNode1Left = node1 && node2 && node1.position.x < node2.position.x

      newEdges.push({
        id: `blocking-${block.blocking_id}`,
        source: isNode1Left ? block.party_id_1 : block.party_id_2,
        target: isNode1Left ? block.party_id_2 : block.party_id_1,
        type: 'straight',
        animated: false,
        style: { 
          stroke: '#ef4444', 
          strokeWidth: 3,
          strokeDasharray: '5,5'
        },
        label: `✓${matchPct.toFixed(0)}% ✗${mismatchPct.toFixed(0)}%`,
        labelStyle: { fill: '#dc2626', fontSize: 9, fontWeight: 700 },
        labelBgStyle: { fill: '#fee2e2', fillOpacity: 0.95 },
        data: { party1Id: block.party_id_1, party2Id: block.party_id_2 },
      })
    })

    relationships.forEach(rel => {
      if (parties.some(p => p.party_id === rel.from_party_id) &&
          parties.some(p => p.party_id === rel.to_party_id)) {
        newEdges.push({
          id: `relationship-${rel.relationship_id}`,
          source: rel.from_party_id,
          target: rel.to_party_id,
          type: 'smoothstep',
          animated: false,
          style: { stroke: '#6366f1', strokeWidth: 1.5 },
          label: 'Relationship',
          labelStyle: { fill: '#4f46e5', fontSize: 9 },
          labelBgStyle: { fill: '#e0e7ff', fillOpacity: 0.8 },
        })
      }
    })

    setNodes(newNodes)
    setEdges(newEdges)
  }, [parties, matchEvidence, blocking, relationships, selectedPartyId, onPartySelect, setNodes, setEdges])

  const onNodeClick = useCallback(
    (_: any, node: Node) => {
      if (node.data.onClick) {
        node.data.onClick()
      }
    },
    []
  )

  const onEdgeClick = useCallback(
    (_: any, edge: Edge) => {
      if (edge.data?.party1Id && edge.data?.party2Id) {
        const p1 = parties.find(p => p.party_id === edge.data.party1Id)
        const p2 = parties.find(p => p.party_id === edge.data.party2Id)
        if (p1 && p2) {
          setSelectedEdge({ party1: p1, party2: p2 })
        }
      }
    },
    [parties]
  )

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2, maxZoom: 0.9 }}
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background />
        <Controls />
      </ReactFlow>
      
      {selectedEdge && (
        <EdgeDetailsModal
          party1={selectedEdge.party1}
          party2={selectedEdge.party2}
          onClose={() => setSelectedEdge(null)}
        />
      )}
    </div>
  )
}
