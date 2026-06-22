# Development Guide

## Environment Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
# Clone the repository
cd projects/document-editor

# Install dependencies
npm install

# Run tests
npm test

# Run examples
npm run example:basic
npm run example:collab
npm run example:history
```

## Core Module Breakdown

### 1. CRDT Document (`src/crdt/CRDTDocument.ts`)

⭐ **Key Class**: `CRDTDocument`

**Core Methods**:
- `insert(position, value)`: Insert a character
- `delete(position)`: Delete a character (tombstone)
- `applyRemoteOp(op)`: Apply operation from remote peer
- `getText()`: Get current text content

**Algorithm Details**:
```
Insert("A" at position 3):
1. Create CharNode {id: "site1:5", value: "A", parentId: charAt(2)}
2. Find insertion point after parent
3. Apply tie-breaking rules
4. Insert into sequence
```

### 2. Format Manager (`src/formatting/FormatTypes.ts`)

⭐ **Key Class**: `FormatManager`

**Core Methods**:
- `applyMark(type, start, end, siteId)`: Apply formatting
- `removeMark(type, start, end, siteId)`: Remove formatting
- `getMarksAt(position)`: Get marks at position
- `getFormattedSpans(text)`: Get spans for rendering

**Position Adjustment**:
When text is inserted/deleted, marks need their positions adjusted:
```typescript
// Insert 2 chars at position 3
adjustForInsert(3, 2);
// Marks after position 3 shift right by 2

// Delete 1 char at position 5
adjustForDelete(5, 1);
// Marks after position 5 shift left by 1
```

### 3. Version History (`src/history/VersionHistory.ts`)

⭐ **Key Class**: `VersionHistory`

**Core Methods**:
- `commit(text, marks, author, message)`: Create version
- `revertTo(versionId)`: Revert to version
- `computeDiff(oldText, newText)`: Compute diff

**Diff Algorithm**:
Simple prefix/suffix matching:
1. Find common prefix
2. Find common suffix
3. Middle part is the diff

### 4. Collaboration Manager (`src/collaboration/CollaborationManager.ts`)

⭐ **Key Class**: `CollaborationManager`

**Core Methods**:
- `join(name)`: Join session
- `broadcastOperation(op)`: Send operation to peers
- `receiveMessage(msg)`: Process incoming message

**Message Flow**:
```
User types "A"
  → Local CRDT.insert(0, "A")
  → broadcastOperation(op)
  → Remote peers receive message
  → Remote CRDT.applyRemoteOp(op)
  → All replicas converge
```

## Testing

### Test Structure
```
tests/
├── CRDTDocument.test.ts    # CRDT core tests
├── FormatManager.test.ts   # Formatting tests
├── VersionHistory.test.ts  # Version control tests
├── DocumentEditor.test.ts  # Integration tests
└── run-tests.ts            # Test runner
```

### Running Tests
```bash
# Run all tests
npm test

# Run specific test
npx ts-node tests/CRDTDocument.test.ts
```

### Writing Tests
```typescript
let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string): void {
  if (condition) {
    passed++;
    console.log(`  ✓ ${message}`);
  } else {
    failed++;
    console.log(`  ✗ ${message}`);
  }
}

// Test
assert(doc.getText() === 'Hello', 'Should have correct text');
```

## Common Issues

### Issue: CRDT not converging
**Cause**: Tie-breaking rules not deterministic
**Fix**: Ensure (timestamp, siteId) comparison is consistent

### Issue: Formatting positions wrong after edits
**Cause**: Position adjustment not called
**Fix**: Call adjustForInsert/adjustForDelete after each edit

### Issue: Versions not restoring correctly
**Cause**: Format state not imported
**Fix**: Import both text and format state

## Performance Tips

1. **Tombstone Cleanup**: Periodically remove deleted characters
2. **Operation Batching**: Batch multiple operations before broadcast
3. **Lazy Rendering**: Only re-render changed portions
4. **Memory Management**: Limit operation log size

## Debugging

### Enable Debug Logging
```typescript
// Add to DocumentEditor constructor
this.on('text:change', (event) => {
  console.log('Text changed:', event);
});
```

### Inspect CRDT State
```typescript
const doc = editor.getDocument();
console.log('Characters:', doc.getCharacters());
console.log('Text:', doc.getText());
console.log('State:', doc.exportState());
```
