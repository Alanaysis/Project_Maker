# Market Research: Rich Text Editors with Collaborative Editing

## Overview

This document analyzes existing rich text editors and collaborative editing solutions to inform our implementation decisions.

## Existing Projects

### 1. Yjs
- **GitHub**: [yjs/yjs](https://github.com/yjs/yjs)
- **Language**: TypeScript
- **Approach**: CRDT-based
- **Strengths**: High performance, extensive ecosystem, used in production by many companies
- **Used by**: Notion, Linear, many others

### 2. ProseMirror
- **GitHub**: [ProseMirror/prosemirror](https://github.com/ProseMirror/prosemirror)
- **Language**: TypeScript
- **Approach**: Modular editor framework
- **Strengths**: Well-designed API, extensible, used in production
- **Used by**: New York Times, The Guardian, Atlassian

### 3. Tiptap
- **GitHub**: [ueberdosis/tiptap](https://github.com/ueberdosis/tiptap)
- **Language**: TypeScript
- **Approach**: Headless editor framework built on ProseMirror
- **Strengths**: Easy to use, Vue/React integrations, good DX
- **Used by**: many startups

### 4. CKEditor 5
- **GitHub**: [ckeditor/ckeditor5](https://github.com/ckeditor/ckeditor5)
- **Language**: TypeScript
- **Approach**: Custom MVC architecture
- **Strengths**: Mature, feature-rich, good documentation
- **Used by**: many enterprises

### 5. Monaco Editor
- **GitHub**: [microsoft/monaco-editor](https://github.com/microsoft/monaco-editor)
- **Language**: TypeScript
- **Approach**: Code editor (not rich text)
- **Strengths**: VS Code integration, excellent for code editing
- **Used by**: VS Code, many code editors

### 6. Automerge
- **GitHub**: [automerge/automerge](https://github.com/automerge/automerge)
- **Language**: Rust (core), TypeScript (bindings)
- **Approach**: CRDT-based
- **Strengths**: Strong consistency, good for local-first apps
- **Used by**: Ink & Switch projects

## Technical Approaches

### OT (Operational Transformation)
- Used by Google Docs, Apache Wave
- Requires central server
- Complex transformation functions
- Battle-tested at scale

### CRDT (Conflict-free Replicated Data Types)
- Used by Figma, Yjs, Automerge
- No central server needed
- Simpler correctness proofs
- Better for offline-first apps

## Key Insights

1. **CRDTs are winning**: The trend is toward CRDTs for new projects
2. **Local-first software**: Driving CRDT adoption
3. **Hybrid approaches**: CRDT + server coordination emerging
4. **Block-level CRDTs**: Simplify architecture (like in BlockNote, Tiptap)
5. **Performance gaps narrowing**: CRDTs catching up to OT

## Our Approach

We chose:
- **CRDT (RGA)** for conflict-free text storage
- **Flat spans model** for rich text formatting
- **Snapshot-based** version control
- **Client-server** collaboration with relay server

This gives us:
- Simple merge logic
- Good learning value
- Foundation for real-world systems
