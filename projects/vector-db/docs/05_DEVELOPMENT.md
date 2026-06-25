# 05 - Development: Vector Database

## Development Environment

### Prerequisites
- Python 3.8+
- NumPy

### Setup
```bash
cd projects/vector-db
pip install -r requirements.txt
```

### Running Tests
```bash
python tests/test_vector_db.py
python tests/test_metrics.py
python tests/test_filter.py
python tests/test_indexes.py
```

### Running Examples
```bash
python examples/image_search.py
python examples/semantic_search.py
python examples/recommendation.py
```

## Implementation Summary

### Phase 1: Core Infrastructure
1. **Distance Metrics** (`src/metrics.py`)
   - Euclidean distance, cosine similarity, inner product
   - Metric registry with (function, is_similarity) tuples

2. **Metadata Filtering** (`src/filter.py`)
   - FilterCondition with operator dispatch
   - MetadataFilter with AND/OR logic
   - Convenience functions (eq, gt, range_filter, etc.)

3. **Base Index** (`src/index/base.py`)
   - Abstract base class with template method pattern
   - Common storage in _vectors and _metadata dicts
   - Hook methods for subclasses (_on_add, _on_remove)

### Phase 2: Index Implementations
4. **Brute Force Index** (`src/index/brute_force.py`)
   - Linear scan of all vectors
   - Exact results as ground truth

5. **LSH Index** (`src/index/lsh.py`)
   - Random hyperplane hashing
   - Multiple hash tables for better recall
   - Candidate collection from hash buckets

6. **HNSW Index** (`src/index/hnsw.py`)
   - Multi-layer graph construction
   - Greedy layer-by-layer search
   - Bidirectional edge management with pruning

### Phase 3: Main API
7. **VectorDB** (`src/vector_db.py`)
   - Unified API over all index types
   - CRUD operations (insert, get, update, delete)
   - Search operations (kNN, range, by-ID)
   - Convenience filter methods
   - JSON persistence (save/load)

### Phase 4: Testing & Examples
8. **Tests**
   - CRUD operations (17 tests)
   - Distance metrics (5 tests)
   - Metadata filtering (10 tests)
   - Index correctness and recall (9 tests)

9. **Examples**
   - Image similarity search
   - Semantic document search
   - Movie recommendation system

## Key Algorithms

### LSH Hash Function
```python
# For each hash table:
# 1. Generate k random hyperplanes (normal vectors)
# 2. Project input vector onto each hyperplane
# 3. Convert signs to bits: positive → 1, negative → 0
# 4. Combine bits into integer hash key

projections = hyperplanes @ vector  # shape: (k,)
bits = (projections > 0).astype(int)
hash_key = sum(bit << i for i, bit in enumerate(bits))
```

### HNSW Insert
```python
1. layer = random_exponential_layer()
2. entry = global_entry_point
3. for l in range(top_layer, layer):
4.     entry = greedy_search(query, entry, ef=1, layer=l)
5. for l in range(layer, -1, -1):
6.     neighbors = search_layer(query, entry, ef_construction, l)
7.     selected = select_neighbors(neighbors, max_connections)
8.     add_bidirectional_edges(query, selected, l)
9.     entry = selected[0]
10. if layer > top_layer: update_entry_point()
```

### HNSW Search
```python
1. entry = global_entry_point
2. for l in range(top_layer, 0):
3.     entry = greedy_search(query, entry, ef=1, layer=l)
4. results = search_layer(query, entry, ef_search, layer=0)
5. return top_k(results)
```

## Performance Notes

### Memory Usage
- Each vector: dimension * 4 bytes (float32)
- HNSW edges: ~M * 8 bytes per node per layer
- LSH: num_tables * num_hyperplanes * 4 bytes per hyperplane + hash table overhead

### Optimization Opportunities (Future)
- Batch distance computation using NumPy broadcasting
- Use FAISS or Annoy for production workloads
- Add IVF-PQ index for very large datasets
- Implement incremental HNSW updates
- Add disk-based storage for datasets larger than memory

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `src/vector_db.py` | ~280 | Main API class |
| `src/metrics.py` | ~90 | Distance metrics |
| `src/filter.py` | ~180 | Metadata filtering |
| `src/index/base.py` | ~120 | Abstract base index |
| `src/index/brute_force.py` | ~60 | Exact search |
| `src/index/lsh.py` | ~140 | LSH approximate search |
| `src/index/hnsw.py` | ~280 | HNSW approximate search |
| `src/utils/helpers.py` | ~80 | Test utilities |
| `tests/test_vector_db.py` | ~200 | CRUD tests |
| `tests/test_metrics.py` | ~90 | Metric tests |
| `tests/test_filter.py` | ~150 | Filter tests |
| `tests/test_indexes.py` | ~180 | Index tests |
| `examples/image_search.py` | ~120 | Image search demo |
| `examples/semantic_search.py` | ~140 | Semantic search demo |
| `examples/recommendation.py` | ~180 | Recommendation demo |

## Lessons Learned

1. **Template Method Pattern**: The BaseIndex with hook methods (_on_add, _on_remove) makes it easy to add new index types without duplicating CRUD logic.

2. **HNSW Complexity**: HNSW is the most complex index. The key insight is the multi-layer graph where each layer acts as a "zoom level" for the search.

3. **LSH Tradeoffs**: More hash tables improve recall but use more memory. The number of hyperplanes controls bucket granularity.

4. **Metric Normalization**: For HNSW, similarity metrics must be converted to distances (negate cosine similarity) so the search algorithm works uniformly.

5. **Metadata Filtering**: Filtering after distance computation is simple but correct. Production systems use pre-filtering for better performance.
