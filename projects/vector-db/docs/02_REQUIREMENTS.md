# 02 - Requirements: Vector Database

## Functional Requirements

### FR-1: Vector Storage
- Store vectors with unique string identifiers
- Support configurable vector dimensions (1 to N)
- Associate optional metadata (key-value pairs) with each vector

### FR-2: CRUD Operations
- **Create**: Insert single or batch vectors with metadata
- **Read**: Retrieve vector and metadata by ID
- **Update**: Modify vector and/or metadata independently
- **Delete**: Remove single or batch vectors by ID

### FR-3: Similarity Search
- k-Nearest Neighbor (kNN) search
- Range search (all vectors within a distance threshold)
- Search by vector or by existing vector ID

### FR-4: Distance Metrics
- Euclidean distance
- Cosine similarity
- Inner product (dot product)

### FR-5: Index Types
- **Brute Force**: Exact search, baseline implementation
- **LSH**: Approximate search via locality-sensitive hashing
- **HNSW**: Approximate search via hierarchical graph

### FR-6: Metadata Filtering
- Equality filter (field == value)
- Comparison filters (>, >=, <, <=)
- Range filter (min <= value <= max)
- Set membership filter (IN, NOT IN)
- String contains filter
- Existence filter (field exists)
- AND/OR logic for combining conditions

### FR-7: Persistence
- Save database state to disk
- Load database state from disk
- JSON format for portability

## Non-Functional Requirements

### NFR-1: Performance
- Brute force: exact results, O(n*d) per query
- LSH: sub-linear query time, tunable recall
- HNSW: logarithmic query time, high recall (>90% for typical datasets)

### NFR-2: Scalability
- Handle datasets up to 1M vectors on a single machine
- Memory-efficient storage (NumPy arrays)

### NFR-3: Usability
- Clean Python API with type hints
- Method chaining for filter construction
- Informative error messages
- Comprehensive docstrings

### NFR-4: Testability
- Unit tests for all components
- Integration tests for end-to-end workflows
- Recall benchmarks comparing index types

### NFR-5: Maintainability
- Modular architecture (separate index, metrics, filter modules)
- Abstract base class for indexes (easy to add new index types)
- Consistent coding style

## Data Model

### Vector Record
```
{
    "id": string,           # Unique identifier
    "vector": float32[],    # Fixed-dimension vector
    "metadata": {           # Optional key-value metadata
        "key": value,       # Value can be string, number, bool, list
        ...
    }
}
```

### Database Configuration
```
{
    "dimension": int,        # Vector dimension (fixed per database)
    "index_type": string,    # "brute_force" | "lsh" | "hnsw"
    "metric": string,        # "euclidean" | "cosine" | "inner_product"
    "index_params": {}       # Index-specific parameters
}
```

## API Specification

### Constructor
```python
VectorDB(dimension, index_type, metric, **kwargs)
```

### CRUD
```python
insert(id, vector, metadata) -> None
insert_batch(ids, vectors, metadata_list) -> None
get(id) -> dict | None
update(id, vector, metadata) -> bool
delete(id) -> bool
delete_batch(ids) -> int
exists(id) -> bool
```

### Search
```python
search(query, k, metadata_filter, **kwargs) -> list[dict]
search_by_id(id, k, metadata_filter, **kwargs) -> list[dict]
range_search(query, radius, metadata_filter) -> list[dict]
```

### Persistence
```python
save(path) -> None
VectorDB.load(path, **kwargs) -> VectorDB
```

### Utility
```python
list_ids() -> list[str]
clear() -> None
size -> int
```
