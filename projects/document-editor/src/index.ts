/**
 * Document Editor - A Rich Text Editor with Collaborative Editing
 *
 * This module exports all the core components of the document editor.
 */

// Core CRDT
export { CRDTDocument } from './crdt/CRDTDocument';
export type { CharId, CharNode, CRDTOperation } from './crdt/CRDTDocument';

// Formatting
export { FormatManager } from './formatting/FormatTypes';
export type { MarkType, FormatMark, FormatSpan, FormatCommand } from './formatting/FormatTypes';

// Version History
export { VersionHistory } from './history/VersionHistory';
export type { Version, Diff } from './history/VersionHistory';

// Collaboration
export { CollaborationManager } from './collaboration/CollaborationManager';
export type { Peer, CollabMessage } from './collaboration/CollaborationManager';

// Main Editor
export { DocumentEditor } from './editor/DocumentEditor';
export type { EditorConfig, EditorEventType, EditorEvent } from './editor/DocumentEditor';
