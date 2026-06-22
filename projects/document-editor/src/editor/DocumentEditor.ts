/**
 * ============================================================
 * Document Editor - Main Editor Class
 * ============================================================
 *
 * ⭐ EDITOR ARCHITECTURE:
 *
 * The editor follows a layered architecture:
 *
 *   ┌─────────────────────────────────┐
 *   │         User Interface          │  (Rendered output)
 *   ├─────────────────────────────────┤
 *   │         DocumentEditor          │  (Public API)
 *   ├─────────────────────────────────┤
 *   │  CRDT  │  Format  │  History   │  (Core modules)
 *   ├─────────────────────────────────┤
 *   │       Collaboration             │  (Sync layer)
 *   └─────────────────────────────────┘
 *
 * Each layer only depends on layers below it.
 *
 * 💡 DESIGN PRINCIPLE: Separation of Concerns
 * - CRDT handles conflict-free text storage
 * - FormatManager handles rich text formatting
 * - VersionHistory handles snapshots and undo
 * - CollaborationManager handles real-time sync
 * - DocumentEditor provides a unified API
 */

import { CRDTDocument, CRDTOperation } from '../crdt/CRDTDocument';
import { FormatManager, FormatCommand, MarkType, FormatMark } from '../formatting/FormatTypes';
import { VersionHistory, Version, Diff } from '../history/VersionHistory';
import { CollaborationManager, Peer, CollabMessage } from '../collaboration/CollaborationManager';

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

/**
 * The main document editor class.
 *
 * This is the primary entry point for all editor operations.
 * It orchestrates the CRDT, formatting, history, and collaboration modules.
 */
export class DocumentEditor {
  /** The CRDT document for conflict-free text storage */
  private document: CRDTDocument;
  /** Formatting manager for rich text */
  private formatManager: FormatManager;
  /** Version history for snapshots */
  private history: VersionHistory;
  /** Collaboration manager for real-time sync */
  private collab: CollaborationManager;
  /** Editor configuration */
  private config: EditorConfig;
  /** Current cursor position */
  private cursorPosition: number = 0;
  /** Event listeners */
  private listeners: Map<string, Array<(event: EditorEvent) => void>> = new Map();

  constructor(config: EditorConfig) {
    this.config = config;
    this.document = new CRDTDocument(config.siteId);
    this.formatManager = new FormatManager();
    this.history = new VersionHistory();
    this.collab = new CollaborationManager(config.siteId, this.document, this.formatManager);

    // Set up collaboration event forwarding
    this.collab.on('document:changed', () => {
      this.emit('text:change', { source: 'remote' });
    });
    this.collab.on('peer:join', (_, peer) => {
      this.emit('peer:join', peer);
    });
    this.collab.on('peer:leave', (_, data) => {
      this.emit('peer:leave', data);
    });
  }

  // ─── Text Operations ───────────────────────────────────

  /**
   * Insert text at the current cursor position.
   *
   * ⭐ INSERT FLOW:
   * 1. Insert into local CRDT
   * 2. Broadcast operation to peers
   * 3. Update cursor position
   * 4. Notify listeners
   */
  insertText(text: string): void {
    for (let i = 0; i < text.length; i++) {
      const { node, op } = this.document.insert(this.cursorPosition + i, text[i]);
      this.collab.broadcastOperation(op);
    }
    this.cursorPosition += text.length;
    this.emit('text:change', { source: 'local', text, position: this.cursorPosition - text.length });
  }

  /**
   * Insert text at a specific position
   */
  insertTextAt(position: number, text: string): void {
    this.cursorPosition = position;
    this.insertText(text);
  }

  /**
   * Delete characters before the cursor (backspace)
   */
  deleteBefore(count: number = 1): void {
    for (let i = 0; i < count; i++) {
      if (this.cursorPosition > 0) {
        const op = this.document.delete(this.cursorPosition - 1);
        if (op) {
          this.collab.broadcastOperation(op);
          this.cursorPosition--;
        }
      }
    }
    this.emit('text:change', { source: 'local', action: 'delete', count });
  }

  /**
   * Delete characters after the cursor (delete key)
   */
  deleteAfter(count: number = 1): void {
    for (let i = 0; i < count; i++) {
      const op = this.document.delete(this.cursorPosition);
      if (op) {
        this.collab.broadcastOperation(op);
      }
    }
    this.emit('text:change', { source: 'local', action: 'delete', count });
  }

  /**
   * Delete a range of text
   */
  deleteRange(start: number, end: number): void {
    const count = end - start;
    for (let i = 0; i < count; i++) {
      const op = this.document.delete(start);
      if (op) {
        this.collab.broadcastOperation(op);
      }
    }
    this.cursorPosition = start;
    this.emit('text:change', { source: 'local', action: 'deleteRange', start, end });
  }

  // ─── Formatting Operations ─────────────────────────────

  /**
   * Apply formatting to a range of text
   *
   * ⭐ FORMATTING FLOW:
   * 1. Apply mark to FormatManager
   * 2. Broadcast format command to peers
   * 3. Notify listeners
   */
  applyFormat(markType: MarkType, start: number, end: number): void {
    this.formatManager.applyMark(markType, start, end, this.config.siteId);
    const cmd: FormatCommand = {
      type: 'apply',
      mark: markType,
      start,
      end,
      siteId: this.config.siteId,
    };
    this.collab.broadcastFormat(cmd);
    this.emit('format:change', { type: 'apply', mark: markType, start, end });
  }

  /**
   * Remove formatting from a range of text
   */
  removeFormat(markType: MarkType, start: number, end: number): void {
    this.formatManager.removeMark(markType, start, end, this.config.siteId);
    const cmd: FormatCommand = {
      type: 'remove',
      mark: markType,
      start,
      end,
      siteId: this.config.siteId,
    };
    this.collab.broadcastFormat(cmd);
    this.emit('format:change', { type: 'remove', mark: markType, start, end });
  }

  /**
   * Toggle formatting on a range
   */
  toggleFormat(markType: MarkType, start: number, end: number): void {
    const marks = this.formatManager.getMarksAt(start);
    if (marks.includes(markType)) {
      this.removeFormat(markType, start, end);
    } else {
      this.applyFormat(markType, start, end);
    }
  }

  // ─── Cursor Operations ─────────────────────────────────

  /**
   * Set the cursor position
   */
  setCursor(position: number): void {
    this.cursorPosition = Math.max(0, Math.min(position, this.document.length));
    this.collab.broadcastAwareness(this.cursorPosition);
    this.emit('cursor:change', { position: this.cursorPosition });
  }

  /**
   * Get the cursor position
   */
  getCursor(): number {
    return this.cursorPosition;
  }

  // ─── Version History ───────────────────────────────────

  /**
   * Create a version snapshot (commit)
   */
  commit(message: string, tag?: string): Version {
    const version = this.history.commit(
      this.document.getText(),
      this.formatManager.exportState(),
      this.config.authorName,
      message,
      tag,
    );
    this.emit('version:created', version);
    return version;
  }

  /**
   * Get all versions
   */
  getVersions(): Version[] {
    return this.history.getAllVersions();
  }

  /**
   * Revert to a specific version
   */
  revertTo(versionId: string): boolean {
    const version = this.history.revertTo(versionId);
    if (!version) return false;

    // Rebuild document from version text
    this.document = new CRDTDocument(this.config.siteId);
    this.formatManager = new FormatManager();

    // Insert the text from the version
    const text = version.text;
    for (let i = 0; i < text.length; i++) {
      this.document.insert(i, text[i]);
    }

    this.formatManager.importState(version.formatMarks);
    this.cursorPosition = text.length;

    this.emit('text:change', { source: 'revert', versionId });
    return true;
  }

  /**
   * Compute diff between current state and a version
   */
  diffWith(versionId: string): Diff[] {
    const version = this.history.getVersion(versionId);
    if (!version) return [];
    return this.history.computeDiff(version.text, this.document.getText());
  }

  // ─── Collaboration ─────────────────────────────────────

  /**
   * Join a collaboration session
   */
  joinSession(peerName: string): void {
    this.collab.join(peerName);
  }

  /**
   * Leave the collaboration session
   */
  leaveSession(): void {
    this.collab.leave();
  }

  /**
   * Receive a message from a remote peer
   */
  receiveCollabMessage(message: CollabMessage): void {
    this.collab.receiveMessage(message);
  }

  /**
   * Get connected peers
   */
  getPeers(): Peer[] {
    return this.collab.getPeers();
  }

  /**
   * Simulate receiving an operation from a remote peer
   * (for testing without a real server)
   */
  applyRemoteOperation(op: CRDTOperation): void {
    this.document.applyRemoteOp(op);
    this.emit('text:change', { source: 'remote' });
  }

  // ─── Query ─────────────────────────────────────────────

  /**
   * Get the current document text
   */
  getText(): string {
    return this.document.getText();
  }

  /**
   * Get formatted spans for rendering
   */
  getFormattedContent() {
    const text = this.document.getText();
    return this.formatManager.getFormattedSpans(text);
  }

  /**
   * Get the document length
   */
  get length(): number {
    return this.document.length;
  }

  /**
   * Get the CRDT document (for advanced operations)
   */
  getDocument(): CRDTDocument {
    return this.document;
  }

  /**
   * Get the format manager
   */
  getFormatManager(): FormatManager {
    return this.formatManager;
  }

  /**
   * Render the document as a string with formatting indicators
   */
  render(): string {
    const spans = this.getFormattedContent();
    return spans.map(span => {
      let text = span.text;
      for (const mark of span.marks) {
        switch (mark) {
          case 'bold': text = `**${text}**`; break;
          case 'italic': text = `*${text}*`; break;
          case 'underline': text = `__${text}__`; break;
          case 'strikethrough': text = `~~${text}~~`; break;
          case 'code': text = `\`${text}\``; break;
        }
      }
      return text;
    }).join('');
  }

  // ─── Events ────────────────────────────────────────────

  /**
   * Register an event listener
   */
  on(event: EditorEventType, listener: (event: EditorEvent) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }

  /**
   * Emit an event
   */
  private emit(type: EditorEventType, data: any): void {
    const event: EditorEvent = { type, data, timestamp: Date.now() };
    const listeners = this.listeners.get(type) || [];
    for (const listener of listeners) {
      listener(event);
    }
  }

  /**
   * Export the full editor state for persistence
   */
  exportState() {
    return {
      document: this.document.exportState(),
      formats: this.formatManager.exportState(),
      history: this.history.exportState(),
      cursorPosition: this.cursorPosition,
      config: this.config,
    };
  }
}
