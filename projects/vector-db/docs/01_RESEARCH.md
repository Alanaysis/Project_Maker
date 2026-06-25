# 01 - Research: Vector Database

## What is a Vector Database?

A vector database is a specialized database designed to store, index, and query high-dimensional vector embeddings. Unlike traditional databases that work with structured data (rows and columns), vector databases are optimized for similarity search in embedding spaces.

## Why Vector Databases?

### The Embedding Revolution
Modern ML models (BERT, CLIP, GPT, ResNet) convert unstructured data (text, images, audio) into dense vector representations called embeddings. These embeddings capture semantic meaning, enabling:

- **Semantic Search**: Find documents by meaning, not keywords
- **Recommendation**: Find items similar to what a user likes
- **Image Search**: Find visually similar images
- **Anomaly Detection**: Find outliers in embedding space

### Traditional Databases Fall Short
- SQL databases cannot efficiently compute similarity across millions of high-dimensional vectors
- Keyword search misses semantic relationships
- Brute-force comparison is O(n) per query, too slow for production

## Core Concepts

### 1. Vector Embeddings
- Fixed-length numerical representations of data
- Typical dimensions: 128 to 4096
- Similar items have nearby vectors in the embedding space

### 2. Similarity Metrics

| Metric | Formula | Properties |
|--------|---------|------------|
| Euclidean | \|\|a-b\|\| | Scale-sensitive, measures absolute distance |
| Cosine | 1 - cos(a,b) | Scale-invariant, measures angle between vectors |
| Inner Product | a . b | Combines magnitude and direction |

### 3. Approximate Nearest Neighbor (ANN)
Exact nearest neighbor search is O(n*d) per query. ANN algorithms trade a small amount of accuracy for massive speed improvements:

- **LSH**: Hash similar vectors to same buckets
- **HNSW**: Graph-based navigation through vector space
- **IVF**: Partition space into clusters, search relevant clusters
- **PQ**: Compress vectors using product quantization

## Existing Solutions

### Production Systems
| System | Index Types | Language | License |
|--------|------------|---------|---------|
| Pinecone | Proprietary | Cloud | SaaS |
| Milvus | IVF, HNSW, DiskANN | Go/C++ | Apache 2.0 |
| Qdrant | HNSW | Rust | Apache 2.0 |
| Weaviate | HNSW | Go | BSD-3 |
| ChromaDB | HNSW | Python | Apache 2.0 |
| FAISS | IVF, HNSW, PQ | C++/Python | MIT |

### Academic Algorithms
- **LSH (Locality-Sensitive Hashing)**: Indyk & Motwani, 1998
- **Annoy (Approximate Nearest Neighbors Oh Yeah)**: Spotify
- **HNSW**: Malkov & Yashunin, 2016
- **IVF-PQ**: Jégou et al., 2011

## Design Decisions

### Target Use Cases
1. Learning and prototyping
2. Small to medium datasets (< 1M vectors)
3. Single-machine deployment
4. Educational reference implementation

### Architecture Choices
- Pure Python + NumPy for simplicity
- Pluggable index architecture
- Metadata filtering integrated into search
- JSON persistence for portability

## References

1. Malkov, Y. A., & Yashunin, D. A. (2016). Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs.
2. Indyk, P., & Motwani, R. (1998). Approximate nearest neighbors: towards removing the curse of dimensionality.
3. Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. (FAISS)
4. Various vector database documentation (Milvus, Qdrant, Pinecone, ChromaDB)
