# Document Editor

A rich text editor built from scratch with collaborative editing support using CRDT (Conflict-free Replicated Data Types).

## Overview

This project implements a document editor that supports:
- **Rich text editing** with formatting (bold, italic, underline, strikethrough, code)
- **Collaborative editing** using CRDT for conflict-free merging
- **Version control** with commits, tags, and diffs

## Learning Objectives

- Understand rich text editor architecture
- Master CRDT algorithms for conflict-free collaboration
- Learn real-time collaborative editing patterns
- Implement version control for documents

## Tech Stack

- **Language**: TypeScript (learning difficulty: ⭐⭐ medium)
- **Framework**: None (from scratch)
- **Algorithm**: CRDT (RGA - Replicated Growable Array)

## Architecture

```
┌─────────────────────────────────────┐
│         User Interface              │  (Rendered output)
├─────────────────────────────────────┤
│         DocumentEditor              │  (Public API)
├─────────────────────────────────────┤
│  CRDT  │  Format  │  History       │  (Core modules)
├─────────────────────────────────────┤
│       Collaboration                 │  (Sync layer)
└─────────────────────────────────────┘
```

## Core Modules

### 1. CRDT Document (`src/crdt/CRDTDocument.ts`)
⭐ **Key concept**: Conflict-free Replicated Data Types

Each character gets a globally unique ID (siteId + logical clock). Characters are ordered by their position ID, not array index. Insertions and deletions commute naturally.

```typescript
// Insert a character
const { node, op } = doc.insert(position, 'A');

// Apply remote operation
doc.applyRemoteOp(remoteOp);
```

### 2. Format Manager (`src/formatting/FormatTypes.ts`)
⭐ **Key concept**: Flat spans model for rich text

Formatting is stored as marks on character ranges. When characters are inserted/deleted, mark positions are adjusted automatically.

```typescript
// Apply bold to range
formatManager.applyMark('bold', 0, 5, 'site1');

// Get formatted spans for rendering
const spans = formatManager.getFormattedSpans(text);
```

### 3. Version History (`src/history/VersionHistory.ts`)
⭐ **Key concept**: Snapshot-based version control

Each version stores the full document state. Supports commits, tags, diffs, and reverting.

```typescript
// Create a version
history.commit(text, formatMarks, 'Alice', 'Initial commit', 'v1.0');

// Revert to a version
history.revertTo(versionId);
```

### 4. Collaboration Manager (`src/collaboration/CollaborationManager.ts`)
⭐ **Key concept**: Broadcast pattern for real-time sync

When a local edit happens, the operation is broadcast to all peers. Each peer applies the operation to their local CRDT replica.

```typescript
// Join a session
collab.join('Alice');

// Broadcast operation
collab.broadcastOperation(op);

// Receive remote operation
collab.receiveMessage(message);
```

## Quick Start

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run examples
npm run example:basic
npm run example:collab
npm run example:history
```

## Project Structure

```
document-editor/
├── src/
│   ├── core/           # Core types and utilities
│   ├── crdt/           # CRDT implementation
│   │   └── CRDTDocument.ts
│   ├── formatting/     # Rich text formatting
│   │   └── FormatTypes.ts
│   ├── history/        # Version control
│   │   └── VersionHistory.ts
│   ├── collaboration/  # Real-time collaboration
│   │   └── CollaborationManager.ts
│   ├── editor/         # Main editor class
│   │   └── DocumentEditor.ts
│   └── index.ts        # Public API
├── tests/              # Test suites
├── examples/           # Usage examples
├── docs/               # Documentation
└── README.md
```

## Key Algorithms

### CRDT (RGA Algorithm)
⭐ **Difficulty**: Hard

RGA maintains an ordered sequence where:
1. Each element has a unique ID and a parent pointer
2. Insert "after X" means: find X, then insert at the position right after X
3. When two inserts happen after the same parent concurrently, we use (timestamp, siteId) to break ties deterministically
4. Deletions are logical (tombstones)

This ensures all replicas converge to the same sequence.

### Operational Transformation (OT)
💡 **Alternative approach**: OT transforms operations so they can be applied in any order while converging to the same state. Requires a central server.

**Trade-offs**:
- CRDT: More metadata per character, but simpler merge logic
- OT: Less metadata, but complex transform functions

## Worth Thinking About

💡 **Why CRDT over OT?**
- CRDTs can merge without coordination, enabling peer-to-peer collaboration
- OT requires a central server to transform operations
- CRDTs are better for offline-first and local-first applications

💡 **How to handle rich text formatting in CRDTs?**
- Peritext (Ink & Switch) proposes intent-preserving merge semantics
- Our implementation uses simple "last writer wins" for conflicts
- Real systems need more sophisticated merge strategies

💡 **Version control trade-offs:**
- Snapshot vs. operation log
- Snapshots: Simple, fast reads, large storage
- Operation log: Compact, slow reads, complex replay

## Resources

- [Yjs Documentation](https://docs.yjs.dev/) - Popular CRDT library
- [Automerge](https://automerge.org/) - Another CRDT implementation
- [ProseMirror](https://prosemirror.net/) - Rich text editor framework
- [Tiptap](https://tiptap.dev/) - Headless editor framework
- [Peritext Paper](https://www.inkandswitch.com/peritext/) - Rich text CRDT

## License

MIT
