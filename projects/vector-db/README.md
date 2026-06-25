# Vector Database

A lightweight vector database implementation in Python with multiple indexing strategies, metadata filtering, and support for real-world applications like image search, semantic search, and recommendation systems.

## Features

- **Multiple Index Types**
  - Brute Force (exact search, O(n) per query)
  - LSH - Locality-Sensitive Hashing (approximate, fast for high dimensions)
  - HNSW - Hierarchical Navigable Small World (approximate, excellent recall)

- **Distance Metrics**
  - Euclidean Distance
  - Cosine Similarity
  - Inner Product (Dot Product)

- **CRUD Operations**
  - Insert / Insert Batch
  - Delete / Delete Batch
  - Update (vector and/or metadata)
  - Get by ID
  - Search / Range Search

- **Metadata Filtering**
  - Equality, Comparison, Range filters
  - AND/OR logic
  - IN, CONTAINS, EXISTS operators

- **Persistence**
  - Save/Load to disk (JSON format)

## Quick Start

```python
from src.vector_db import VectorDB
import numpy as np

# Create database
db = VectorDB(dimension=128, index_type="hnsw", metric="cosine")

# Insert vectors with metadata
db.insert("img_001", np.random.randn(128), {"category": "photo", "year": 2024})
db.insert("img_002", np.random.randn(128), {"category": "illustration", "year": 2023})

# Search for similar vectors
results = db.search(np.random.randn(128), k=5)
for r in results:
    print(f"{r['id']}: distance={r['distance']:.4f}, metadata={r['metadata']}")

# Search with metadata filter
from src.filter import eq, range_filter
results = db.search(
    np.random.randn(128),
    k=5,
    metadata_filter=eq("category", "photo")
)

# Range search (all vectors within distance)
results = db.range_search(np.random.randn(128), radius=5.0)
```

## Index Types

### Brute Force
```python
db = VectorDB(dimension=128, index_type="brute_force", metric="euclidean")
```
- Exact nearest neighbor search
- Computes distance to every vector
- Best for: small datasets (< 10K vectors), exact results needed

### LSH (Locality-Sensitive Hashing)
```python
db = VectorDB(dimension=128, index_type="lsh", metric="euclidean",
              num_tables=10, num_hyperplanes=16)
```
- Approximate search using random hyperplane hashing
- Sub-linear search time
- Best for: high-dimensional data, millions of vectors

### HNSW (Hierarchical Navigable Small World)
```python
db = VectorDB(dimension=128, index_type="hnsw", metric="cosine",
              max_connections=16, ef_construction=200)
```
- Graph-based approximate search
- Excellent recall with logarithmic search time
- Best for: general purpose, production workloads

## Distance Metrics

| Metric | Formula | Best For |
|--------|---------|----------|
| `euclidean` | \|\|a - b\|\| | Spatial data, normalized features |
| `cosine` | 1 - (a . b) / (\|a\| \|b\|) | Text embeddings, direction matters |
| `inner_product` | a . b | Recommendation systems, raw similarity |

## Metadata Filtering

```python
from src.filter import MetadataFilter, FilterOperator, eq, gt, range_filter

# Simple filters
db.search(query, k=10, metadata_filter=eq("category", "electronics"))
db.search(query, k=10, metadata_filter=gt("rating", 4.0))
db.search(query, k=10, metadata_filter=range_filter("price", 10, 100))

# Complex filter
f = MetadataFilter()
f.add_condition("category", FilterOperator.EQ, "electronics")
f.add_condition("rating", FilterOperator.GTE, 4.0)
f.add_condition("price", FilterOperator.LTE, 500)
results = db.search(query, k=10, metadata_filter=f)

# OR logic
f = MetadataFilter()
f.set_logic("or")
f.add_condition("color", FilterOperator.EQ, "red")
f.add_condition("color", FilterOperator.EQ, "blue")
```

## Examples

### Similar Image Search
```bash
python examples/image_search.py
```

### Semantic Search
```bash
python examples/semantic_search.py
```

### Recommendation System
```bash
python examples/recommendation.py
```

## Project Structure

```
vector-db/
├── src/
│   ├── __init__.py          # Package exports
│   ├── vector_db.py         # Main VectorDB class
│   ├── metrics.py           # Distance metrics
│   ├── filter.py            # Metadata filtering
│   ├── index/
│   │   ├── __init__.py
│   │   ├── base.py          # Base index class
│   │   ├── brute_force.py   # Brute force index
│   │   ├── lsh.py           # LSH index
│   │   └── hnsw.py          # HNSW index
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Utility functions
├── tests/
│   ├── test_vector_db.py    # CRUD tests
│   ├── test_metrics.py      # Metric tests
│   ├── test_filter.py       # Filter tests
│   └── test_indexes.py      # Index tests
├── examples/
│   ├── image_search.py      # Image similarity search
│   ├── semantic_search.py   # Text semantic search
│   └── recommendation.py    # Movie recommendations
├── docs/                    # Documentation
├── requirements.txt
└── README.md
```

## Running Tests

```bash
# Run all tests
cd projects/vector-db
python tests/test_vector_db.py
python tests/test_metrics.py
python tests/test_filter.py
python tests/test_indexes.py
```

## Requirements

- Python 3.8+
- NumPy

## License

MIT
