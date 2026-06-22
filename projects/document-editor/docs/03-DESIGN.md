# Technical Design

## Architecture Overview

```
┌─────────────────────────────────────┐
│         User Interface              │
├─────────────────────────────────────┤
│         DocumentEditor              │
├─────────────────────────────────────┤
│  CRDT  │  Format  │  History       │
├─────────────────────────────────────┤
│       Collaboration                 │
└─────────────────────────────────────┘
```

## Core Data Structures

### CRDT Character Node
```typescript
interface CharNode {
  id: CharId;          // Unique ID (siteId + clock)
  value: string;       // The character
  deleted: boolean;    // Tombstone flag
  parentId: CharId;    // Parent for ordering
  timestamp: number;   // For tie-breaking
}
```

### Format Mark
```typescript
interface FormatMark {
  type: MarkType;      // 'bold' | 'italic' | ...
  start: number;       // Start position
  end: number;         // End position
  siteId: string;      // Who applied it
  timestamp: number;   // When applied
  active: boolean;     // Whether active
}
```

### Version
```typescript
interface Version {
  id: string;          // Version ID
  parentId: string;    // Parent version
  text: string;        // Document text
  formatMarks: [];     // Formatting state
  author: string;      // Who created it
  message: string;     // Commit message
  tag?: string;        // Optional tag
}
```

## Algorithm: RGA (Replicated Growable Array)

⭐ **Key Insight**: RGA maintains an ordered sequence where each element has a unique ID and a parent pointer.

### Insert Algorithm
1. Create a new CharNode with unique ID
2. Set parentId to the character at position-1
3. Find insertion point in total order
4. Use (timestamp DESC, siteId ASC) for tie-breaking
5. Insert into sequence

### Delete Algorithm
1. Find the character at the position
2. Set deleted = true (tombstone)
3. Don't physically remove

### Convergence
Because:
- Each character has a unique ID
- Insertions are deterministic (same parent, same tie-breaking)
- Deletions are idempotent (setting deleted=true twice is same as once)

All replicas converge to the same sequence.

## Rich Text Model

⭐ **Flat Spans Model**: Each character can have formatting marks. When rendering, we group consecutive characters with the same marks into spans.

```typescript
// Example: "Hello World" with "Hello" bold
[
  { text: "Hello", marks: ["bold"], startPos: 0, endPos: 5 },
  { text: " World", marks: [], startPos: 5, endPos: 11 }
]
```

### Position Adjustment
When characters are inserted/deleted, we adjust mark positions:
- Insert at position P with length L: shift marks after P by +L
- Delete at position P with length L: shift marks after P by -L

## Collaboration Protocol

### Message Types
- `operation`: CRDT insert/delete
- `format`: Format command
- `awareness`: Cursor position
- `join/leave`: Peer management

### Broadcast Pattern
```
Local Edit → Apply to Local CRDT → Broadcast to Peers → Peers Apply
```

Because CRDT operations commute, order doesn't matter!

## Version Control

### Snapshot vs. Operation Log
We use **snapshots** for simplicity:
- Store full document state at each version
- Fast reads (no replay needed)
- Larger storage (but acceptable for small documents)

### Diff Algorithm
Simple prefix/suffix matching for now. Production systems use Myers' algorithm.

## Interfaces

### DocumentEditor (Main API)
```typescript
class DocumentEditor {
  // Text operations
  insertText(text: string): void;
  deleteBefore(count: number): void;
  deleteAfter(count: number): void;
  deleteRange(start: number, end: number): void;

  // Formatting
  applyFormat(mark: MarkType, start: number, end: number): void;
  removeFormat(mark: MarkType, start: number, end: number): void;
  toggleFormat(mark: MarkType, start: number, end: number): void;

  // Cursor
  setCursor(position: number): void;
  getCursor(): number;

  // Version control
  commit(message: string, tag?: string): Version;
  revertTo(versionId: string): boolean;
  diffWith(versionId: string): Diff[];

  // Collaboration
  joinSession(name: string): void;
  leaveSession(): void;
  receiveCollabMessage(msg: CollabMessage): void;
}
```

## Error Handling

- Invalid positions: Clamp to valid range
- Missing versions: Return undefined/null
- Network errors: Queue operations for retry
- Conflicts: CRDT handles automatically

## Performance Considerations

- Tombstone cleanup: Periodic garbage collection
- Large documents: Pagination/virtual scrolling
- Many peers: Operation batching
