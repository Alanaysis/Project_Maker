# 04 - Product: Vector Database

## Product Overview

A lightweight, educational vector database implementation that demonstrates core concepts of similarity search, indexing, and metadata filtering. Designed for learning, prototyping, and small-scale applications.

## Target Users

1. **ML Engineers**: Prototyping vector search before choosing a production system
2. **Students**: Learning how vector databases work internally
3. **Developers**: Building small-scale applications that need similarity search
4. **Researchers**: Experimenting with ANN algorithms

## Use Cases

### UC1: Similar Image Search
**Scenario**: A photo library app wants to find visually similar images.
**Flow**:
1. Extract feature vectors from images using a pre-trained CNN
2. Insert vectors into the database with metadata (filename, category, date)
3. Given a query image, find the most similar images
4. Optionally filter by category or date range

### UC2: Semantic Document Search
**Scenario**: A knowledge base wants to find relevant documents by meaning.
**Flow**:
1. Embed documents using a text embedding model (e.g., Sentence-BERT)
2. Store embeddings with metadata (title, author, topic, date)
3. Embed user queries and find semantically similar documents
4. Filter by topic, author, or date range

### UC3: Recommendation System
**Scenario**: A streaming service wants to recommend movies to users.
**Flow**:
1. Embed movies and user preferences into the same vector space
2. Find movies closest to a user's preference vector
3. Filter by genre, rating, or release year
4. Present top-k recommendations

## User Stories

### Core Operations
- **US1**: As a user, I can insert a vector with metadata so I can retrieve it later
- **US2**: As a user, I can search for the k most similar vectors to a query
- **US3**: As a user, I can filter search results by metadata conditions
- **US4**: As a user, I can update or delete vectors by ID
- **US5**: As a user, I can save and load the database to/from disk

### Index Selection
- **US6**: As a user, I can choose between brute-force, LSH, or HNSW indexing
- **US7**: As a user, I can select the distance metric (Euclidean, cosine, inner product)

### Advanced Features
- **US8**: As a user, I can perform range searches (all vectors within a distance)
- **US9**: As a user, I can search by existing vector ID without knowing the vector
- **US10**: As a user, I can use complex filters with AND/OR logic

## Acceptance Criteria

### AC1: Insert and Retrieve
- Given a vector with ID "v1", when I insert it and query by ID, I get the same vector back
- Metadata is preserved and retrievable

### AC2: Similarity Search
- Given 100 random vectors, when I search for k=5 nearest neighbors, I get 5 results
- Results are sorted by distance (closest first for Euclidean)

### AC3: Metadata Filtering
- Given vectors with category="A" and category="B", when I search with category filter, all results match the filter

### AC4: Index Correctness
- Brute force returns exact results
- HNSW achieves >90% recall@10 compared to brute force on typical datasets
- LSH achieves reasonable recall with enough hash tables

### AC5: Persistence
- Save database to disk, load it back, all vectors and metadata are preserved

## Demo Scenarios

### Demo 1: Image Search (`examples/image_search.py`)
- Simulates 500 images with 128-dim feature vectors
- Shows search, filtered search, and range search
- Demonstrates HNSW index with cosine similarity

### Demo 2: Semantic Search (`examples/semantic_search.py`)
- 10 simulated documents with text embeddings
- Shows semantic query matching
- Demonstrates topic, year, and author filtering

### Demo 3: Recommendation (`examples/recommendation.py`)
- 200 simulated movies with genre embeddings
- 5 simulated users with preference vectors
- Shows personalized recommendations with genre/rating filters
- Demonstrates similar-item lookup

## Performance Characteristics

| Dataset Size | Brute Force | LSH | HNSW |
|-------------|-------------|-----|------|
| 1K vectors | ~1ms | ~0.5ms | ~0.3ms |
| 10K vectors | ~10ms | ~1ms | ~0.5ms |
| 100K vectors | ~100ms | ~2ms | ~1ms |
| 1M vectors | ~1s | ~5ms | ~2ms |

*Approximate values for 128-dim vectors on modern hardware*

## Limitations

- Single-machine only (no distributed support)
- JSON persistence (not optimized for large datasets)
- No concurrent access support
- No incremental index updates for LSH (rebuilds needed)
- Educational implementation, not production-hardened
