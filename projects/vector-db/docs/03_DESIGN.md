# 03 - Design: Vector Database

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                VectorDB (API)                │
│  - CRUD operations                          │
│  - Search with filters                      │
│  - Persistence (save/load)                  │
├─────────────────────────────────────────────┤
│           Index Layer (pluggable)           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ BruteForce│ │   LSH    │ │   HNSW   │   │
│  │  (exact)  │ │(approx.) │ │(approx.) │   │
│  └──────────┘ └──────────┘ └──────────┘    │
├─────────────────────────────────────────────┤
│  Metrics Layer          │  Filter Layer     │
│  - Euclidean            │  - MetadataFilter │
│  - Cosine               │  - FilterCondition│
│  - Inner Product        │  - Operators      │
└─────────────────────────────────────────────┘
```

## Module Design

### 1. VectorDB (`vector_db.py`)
The main entry point. Orchestrates all operations.

**Responsibilities:**
- Validate inputs (dimensions, types)
- Delegate to appropriate index
- Provide convenience methods
- Handle persistence

**Design Patterns:**
- Facade pattern: simplifies complex subsystem
- Strategy pattern: pluggable index and metric implementations

### 2. Index Layer (`index/`)

#### BaseIndex (`base.py`)
Abstract base class defining the index interface.

```
BaseIndex (ABC)
├── add(id, vector, metadata)
├── remove(id)
├── get(id)
├── update(id, vector, metadata)
├── search(query, k, filter) [abstract]
├── _on_add(id, vector, metadata) [hook]
├── _on_remove(id) [hook]
└── _remove_from_index(id) [hook]
```

Key design decisions:
- Template method pattern: base class handles common logic, subclasses override hooks
- Vectors and metadata stored in base class dicts (consistent across all indexes)
- Subclasses only manage their own index structures

#### BruteForceIndex (`brute_force.py`)
- No additional data structure beyond base class
- Computes distance to every vector for each query
- Provides exact results as ground truth

#### LSHIndex (`lsh.py`)
- Multiple hash tables with random hyperplane hashing
- Each table uses `num_hyperplanes` random planes to create binary hash keys
- Query looks up candidates from matching hash buckets
- Falls back to all vectors if not enough candidates

**Parameters:**
- `num_tables`: More tables = higher recall, more memory
- `num_hyperplanes`: More planes = finer buckets, fewer collisions

**Hash Function:**
```
hash(v) = (h1(v) > 0) << (k-1) | (h2(v) > 0) << (k-2) | ... | (hk(v) > 0)
```
where `hi(v) = wi . v` and `wi` is a random hyperplane normal.

#### HNSWIndex (`hnsw.py`)
- Multi-layer navigable small world graph
- Layer 0 contains all vectors
- Higher layers contain exponentially fewer vectors
- Search descends from top layer, using greedy search at each layer

**Parameters:**
- `max_connections` (M): Max edges per node per layer
- `max_connections_layer0`: Max edges in layer 0 (typically 2*M)
- `ef_construction`: Candidate list size during build
- `ef_search`: Candidate list size during query

**Layer Assignment:**
```
P(layer = l) = (1/M) * exp(-l/M)
```

**Insert Algorithm:**
1. Assign random layer to new node
2. Search from entry point down to assigned layer
3. At each layer, find nearest neighbors and create bidirectional edges
4. Prune neighbors exceeding max_connections

**Search Algorithm:**
1. Start at top layer entry point
2. Greedy search at each layer to find nearest neighbor
3. Use that as entry point for next layer down
4. At layer 0, maintain a priority queue of size ef_search

### 3. Metrics Layer (`metrics.py`)

Pure functions for distance computation:

| Metric | Returns | Ordering |
|--------|---------|----------|
| Euclidean | distance >= 0 | lower = more similar |
| Cosine | similarity in [-1, 1] | higher = more similar |
| Inner Product | any float | higher = more similar |

Registry pattern maps metrics to (function, is_similarity) tuples.

### 4. Filter Layer (`filter.py`)

```
MetadataFilter
├── conditions: List[FilterCondition]
├── logic: "and" | "or"
└── match(metadata) -> bool

FilterCondition
├── field: str
├── operator: FilterOperator
├── value: Any
└── match(metadata) -> bool
```

**Supported Operators:**
- `EQ`, `NEQ`: Equality
- `GT`, `GTE`, `LT`, `LTE`: Comparison
- `IN`, `NIN`: Set membership
- `CONTAINS`: String substring
- `EXISTS`: Key presence

## Data Flow

### Insert
```
User → VectorDB.insert(id, vector, metadata)
     → BaseIndex.add(id, vector, metadata)
       → Store in _vectors and _metadata dicts
       → Call _on_add hook (subclass adds to index structure)
```

### Search
```
User → VectorDB.search(query, k, filter)
     → Index.search(query, k, filter)
       → [BruteForce] Compute all distances, sort, return top-k
       → [LSH] Hash query, collect candidates from buckets, compute exact distances
       → [HNSW] Greedy search through layers, collect candidates at layer 0
     → Apply metadata filter to candidates
     → Return sorted results
```

## Error Handling

- Dimension mismatch: `ValueError` with descriptive message
- Missing IDs: Return `None` (get) or `False` (update/delete)
- Invalid parameters: `ValueError` at construction time
- Empty database: Return empty list from search

## Testing Strategy

1. **Unit Tests**: Each module tested independently
2. **Integration Tests**: End-to-end workflows through VectorDB API
3. **Recall Tests**: Compare approximate indexes against brute force ground truth
4. **Edge Cases**: Empty database, dimension mismatch, missing IDs
