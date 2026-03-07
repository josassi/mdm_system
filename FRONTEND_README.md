# Entity Resolution Frontend

A modern web application for visualizing and managing entity resolution data. Built for data stewards to understand matched parties, explore relationships, and investigate blocking conflicts.

## 🎨 Features

### Entity Dashboard
- **Entity List View**: Browse all master entities with search and filtering
- **Statistics Cards**: Quick overview of total entities, conflicts, and quality metrics
- **Conflict Filtering**: Filter entities by conflict status (all/with-conflicts/clean)

### Entity Detail View
- **Interactive Graph Visualization**: Force-directed graph showing party relationships
  - Party nodes with visual indicators for conflicts
  - Match evidence edges (green, animated)
  - Blocking conflict edges (red, dashed)
  - Relationship edges (blue)
- **Multiple View Modes**:
  - Graph view for visual exploration
  - Evidence panel for detailed match information
  - Blocking panel for conflict analysis

### Party Details
- **Source Information**: System, table, party type
- **Attributes Panel**: All party attributes with:
  - Standardized vs raw values
  - Source column information
  - Confidence and quality scores
  - PII indicators
  - Visual quality metrics

### Conflict Analysis
- **Blocking Reasons**: Clear explanations of why parties conflict
- **Conflict Details**: Specific attribute values causing blocks
- **Auto-detection vs Manual**: Distinguish between automatic and manual blocks
- **Steward Guidance**: Actionable information for data quality teams

## 🏗️ Architecture

### Frontend Stack
- **React 18** - UI framework
- **TypeScript** - Type safety
- **React Router** - Navigation
- **React Query** - Data fetching & caching
- **React Flow** - Graph visualization
- **Tailwind CSS** - Styling
- **Heroicons** - Icons
- **Vite** - Build tool

### Backend Stack
- **Flask** - Python web framework
- **Pandas** - Data manipulation
- **Flask-CORS** - Cross-origin support

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Your entity resolution data files in the correct locations

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the API server:
```bash
python api.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## 📊 Data Requirements

The backend expects the following CSV files in your data directories:

### Bronze Layer (`data/bronze/`)
- `source_party.csv`
- `raw_attribute.csv`
- `relationship.csv`

### Silver Layer (`data/silver/`)
- `standardized_attribute.csv`
- `match_evidence.csv`
- `match_blocking.csv`

### Gold Layer (`data/gold/`)
- `master_entity.csv`
- `party_to_entity_link.csv`

### Metadata (`data/uat_generation/metadata/`)
- `metadata_system_table.csv`
- `metadata_party_type.csv`
- `metadata_column_mapping.csv`
- `metadata_blocking_rule.csv`

## 🎯 Usage Guide

### Navigating Entities

1. **Browse Entities**: Start on the entity list page
2. **Search**: Use the search bar to find entities by name or ID
3. **Filter**: Toggle between all entities, those with conflicts, or clean entities
4. **View Details**: Click any entity card to see the full graph view

### Understanding the Graph

- **Green Edges**: Match evidence (the reason parties are grouped)
- **Red Dashed Edges**: Blocking conflicts (why parties shouldn't be together)
- **Blue Edges**: Relationships between parties
- **Node Colors**: 
  - Red border = Has conflicts
  - Blue border = Selected
  - Gray border = Normal

### Investigating Conflicts

1. Click an entity with conflicts (red badge)
2. Switch to the "Blocking" tab
3. Review the conflict explanations
4. Check the conflicting attribute values
5. Examine whether it's auto-detected or manual

### Exploring Party Attributes

1. In graph view, click any party node
2. The attributes panel appears on the right
3. View all attributes with their:
   - Standardized values
   - Original raw values
   - Source information
   - Quality metrics

## 🎨 UX Design Decisions

### Information Hierarchy
1. **Overview → Detail**: Start broad, drill down progressively
2. **Graph-First**: Visual representation as primary view
3. **Contextual Details**: Show details only when needed

### Visual Design
- **Color Coding**: Green (good/matched), Red (conflicts), Blue (neutral/info)
- **Progressive Disclosure**: Show summaries, expand for details
- **Status Indicators**: Clear badges and icons for quick scanning

### Operational Focus
- **Steward-Centric**: Designed for data quality professionals
- **Conflict Prominence**: Conflicts highlighted throughout
- **Actionable Information**: Clear explanations, not just data

## 🔧 Development

### Build for Production

Frontend:
```bash
cd frontend
npm run build
```

The build output will be in `frontend/dist/`

### Environment Variables

Backend (optional):
- `PORT`: API server port (default: 5000)
- `DEBUG`: Enable Flask debug mode

Frontend (optional):
- `VITE_API_URL`: Backend API URL (default: /api)

## 📝 API Endpoints

- `GET /api/health` - Health check
- `GET /api/entities` - List all entities
- `GET /api/entities/:id` - Get entity details
- `GET /api/parties/:id` - Get party details
- `GET /api/search?q=query` - Search entities

## 🤝 Contributing

This is a data steward portal for entity resolution. Key areas for enhancement:

1. **Filtering**: Add more sophisticated filters
2. **Export**: Download entity data as CSV/JSON
3. **Steward Actions**: Manual merge/split capabilities
4. **Audit Trail**: Track steward decisions
5. **Notifications**: Alert on new conflicts

## 📄 License

Internal tool for data quality management.
