# Learning Notes - Document Editor

## What I Learned

### 1. CRDT (Conflict-free Replicated Data Types)

⭐ **Key Insight**: CRDTs are data structures that can be replicated across multiple computers, modified independently and concurrently, and then merged such that all replicas converge to the same state.

**How it works in our editor**:
- Each character gets a unique ID (siteId + logical clock)
- Characters are ordered by their ID, not by array index
- Insertions and deletions commute naturally
- No central coordinator needed

**Why CRDT over OT?**
- OT requires a central server to transform operations
- CRDTs can merge without coordination (peer-to-peer friendly)
- CRDTs are better for offline-first applications

### 2. Rich Text Formatting

⭐ **Key Insight**: Rich text is stored as a flat sequence of characters, where each character can have formatting "marks" applied to it.

**The flat spans model**:
- Each character position can have multiple marks (bold, italic, etc.)
- When rendering, group consecutive characters with same marks into spans
- When text is inserted/deleted, adjust mark positions

**Alternative approaches**:
- Tree-based (nested spans): harder to merge
- Peritext: designed specifically for CRDT + rich text

### 3. Version Control

⭐ **Key Insight**: Document version control can use snapshots (full state) or operation logs (only changes).

**Our approach**: Snapshots
- Store full document state at each version
- Simple implementation
- Fast reads (no replay needed)
- Trade-off: more storage

**Alternative**: Operation log
- Store only operations
- Compact storage
- Slow reads (need to replay)
- Complex implementation

### 4. Collaborative Editing

⭐ **Key Insight**: The broadcast pattern enables real-time collaboration.

**Flow**:
1. User makes edit
2. Edit applied to local CRDT
3. Operation broadcast to all peers
4. Each peer applies operation to their CRDT
5. All replicas converge

**Why it works**: CRDT operations commute, so order doesn't matter!

## Challenges Faced

### 1. CRDT Convergence
**Problem**: Ensuring all replicas converge to same state
**Solution**: Deterministic tie-breaking rules (timestamp, siteId)

### 2. Position Adjustment
**Problem**: Formatting marks need adjustment when text changes
**Solution**: adjustForInsert/adjustForDelete methods

### 3. Tombstone Management
**Problem**: Deleted characters still take up space
**Solution**: Logical deletion (tombstones), with potential garbage collection

## Worth Thinking About

### 💡 Why CRDTs are winning over OT
- Local-first software trend
- Better for offline-first apps
- Simpler correctness proofs
- No single point of failure

### 💡 How to handle rich text in CRDTs
- Peritext paper proposes intent-preserving merge
- "Last writer wins" is too simple for real use
- Need to consider user intent (e.g., "I want this bold" vs "I want this not bold")

### 💡 Version control trade-offs
- Snapshots: simple but large storage
- Operation log: compact but complex replay
- Hybrid: store snapshots periodically, replay operations between

## Resources

- [Yjs Documentation](https://docs.yjs.dev/)
- [Automerge](https://automerge.org/)
- [Peritext Paper](https://www.inkandswitch.com/peritext/)
- [ProseMirror](https://prosemirror.net/)
- [Tiptap](https://tiptap.dev/)

## Next Steps

1. Implement more formatting options
2. Add real server implementation
3. Implement persistent storage
4. Add block-level editing (paragraphs, lists, headings)
5. Performance optimization (tombstone cleanup, operation batching)
