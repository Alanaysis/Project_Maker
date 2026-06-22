# Quick Start Guide

## Installation

```bash
cd projects/document-editor
npm install
```

## Running Tests

```bash
npm test
```

## Running Examples

```bash
# Basic editing
npm run example:basic

# Collaborative editing
npm run example:collab

# Version history
npm run example:history
```

## Basic Usage

```typescript
import { DocumentEditor } from './src/editor/DocumentEditor';

// Create an editor
const editor = new DocumentEditor({
  siteId: 'user-1',
  authorName: 'Alice',
});

// Insert text
editor.insertText('Hello World');

// Apply formatting
editor.applyFormat('bold', 0, 5);

// Create a version
editor.commit('Initial version');

// Get formatted content
const spans = editor.getFormattedContent();
```

## Collaborative Editing

```typescript
// Create two editors
const alice = new DocumentEditor({ siteId: 'alice', authorName: 'Alice' });
const bob = new DocumentEditor({ siteId: 'bob', authorName: 'Bob' });

// Alice inserts text
alice.insertText('Hello');

// Sync to Bob (in real app, this would be over network)
const op = alice.getDocument().getCharacters()[0];
bob.applyRemoteOperation({
  type: 'insert',
  char: op,
  siteId: 'alice',
  clock: op.id.clock,
});

// Both converge to same text
console.log(alice.getText()); // "Hello"
console.log(bob.getText());   // "Hello"
```

## Version Control

```typescript
// Create versions
editor.insertText('Hello');
const v1 = editor.commit('Version 1');

editor.insertText(' World');
const v2 = editor.commit('Version 2');

// View history
console.log(editor.getVersions());

// Revert to v1
editor.revertTo(v1.id);

// Compute diff
const diffs = editor.diffWith(v1.id);
```

## Key Concepts

### CRDT (Conflict-free Replicated Data Types)
- Each character has a unique ID
- Operations commute naturally
- No central coordinator needed

### Rich Text Formatting
- Marks applied to character ranges
- Positions adjust automatically
- Flat spans model for rendering

### Version Control
- Snapshot-based storage
- Commits, tags, diffs
- Revert to any version

## Next Steps

1. Read the [README](README.md) for overview
2. Check [docs/03-DESIGN.md](docs/03-DESIGN.md) for architecture
3. Review [LEARNING_NOTES.md](LEARNING_NOTES.md) for insights
4. Explore the examples for usage patterns
