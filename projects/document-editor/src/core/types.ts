/**
 * Core types for the document editor
 */

/** Unique identifier for a character in the CRDT */
export interface CharId {
  /** The site (peer) that created this character */
  siteId: string;
  /** Logical clock value at creation time */
  clock: number;
}

/** A single character node in the CRDT sequence */
export interface CharNode {
  /** Unique identifier */
  id: CharId;
  /** The actual character value (empty string = tombstone/deleted) */
  value: string;
  /** Whether this character has been deleted (tombstone) */
  deleted: boolean;
  /** The ID of the character this was inserted after (null = beginning) */
  parentId: CharId | null;
  /** Timestamp for tie-breaking */
  timestamp: number;
}

/** An operation that can be applied to the CRDT */
export interface CRDTOperation {
  /** Type of operation */
  type: 'insert' | 'delete';
  /** The character node (for insert) */
  char?: CharNode;
  /** The ID of the character to delete (for delete) */
  targetId?: CharId;
  /** ID of the site that generated this operation */
  siteId: string;
  /** Logical clock when this operation was created */
  clock: number;
}

/** Types of formatting marks */
export type MarkType = 'bold' | 'italic' | 'underline' | 'strikethrough' | 'code';

/** A formatting mark applied to a range of characters */
export interface FormatMark {
  /** The type of formatting */
  type: MarkType;
  /** Start position (inclusive) */
  start: number;
  /** End position (exclusive) */
  end: number;
  /** The site that applied this mark */
  siteId: string;
  /** When this mark was applied */
  timestamp: number;
  /** Whether this mark is active (false = removed) */
  active: boolean;
}

/** A formatting span for rendering */
export interface FormatSpan {
  /** The text content */
  text: string;
  /** Active marks on this span */
  marks: MarkType[];
  /** Start position in the document */
  startPos: number;
  /** End position in the document */
  endPos: number;
}

/** A formatting command */
export interface FormatCommand {
  type: 'apply' | 'remove';
  mark: MarkType;
  start: number;
  end: number;
  siteId: string;
}

/** A version snapshot */
export interface Version {
  /** Unique version identifier */
  id: string;
  /** Parent version ID (null for initial version) */
  parentId: string | null;
  /** When this version was created */
  timestamp: number;
  /** Who created this version */
  author: string;
  /** Commit message */
  message: string;
  /** Document text at this version */
  text: string;
  /** Formatting state at this version */
  formatMarks: FormatMark[];
  /** Optional tag name */
  tag?: string;
}

/** A diff between two versions */
export interface Diff {
  /** The type of change */
  type: 'insert' | 'delete' | 'replace';
  /** Position of the change */
  position: number;
  /** Text that was removed */
  removed: string;
  /** Text that was added */
  added: string;
}

/** A peer in the collaboration session */
export interface Peer {
  /** Unique peer identifier */
  id: string;
  /** Display name */
  name: string;
  /** Whether the peer is currently connected */
  connected: boolean;
  /** Last activity timestamp */
  lastActivity: number;
  /** Cursor position (for awareness) */
  cursorPosition?: number;
}

/** A message sent between peers */
export interface CollabMessage {
  /** Message type */
  type: 'operation' | 'format' | 'awareness' | 'sync' | 'join' | 'leave';
  /** Sender's peer ID */
  senderId: string;
  /** The CRDT operation (for operation messages) */
  operation?: CRDTOperation;
  /** The format command (for format messages) */
  formatCommand?: FormatCommand;
  /** Awareness info (cursor position, selection, etc.) */
  awareness?: { cursorPosition: number; selection?: { start: number; end: number } };
  /** Timestamp */
  timestamp: number;
}

/** Editor configuration */
export interface EditorConfig {
  /** Site ID for this editor instance */
  siteId: string;
  /** Author name */
  authorName: string;
  /** Enable automatic versioning */
  autoVersion?: boolean;
  /** Auto-version interval in milliseconds */
  autoVersionInterval?: number;
}

/** Editor event types */
export type EditorEventType =
  | 'text:change'
  | 'format:change'
  | 'version:created'
  | 'peer:join'
  | 'peer:leave'
  | 'cursor:change';

/** Editor event data */
export interface EditorEvent {
  type: EditorEventType;
  data: any;
  timestamp: number;
}
