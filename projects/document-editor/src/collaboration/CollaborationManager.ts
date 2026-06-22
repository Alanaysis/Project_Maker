/**
 * ============================================================
 * Collaboration Manager - Real-time Collaborative Editing
 * ============================================================
 *
 * ⭐ COLLABORATION ARCHITECTURE:
 *
 * This module implements a simplified collaboration protocol
 * that enables multiple users to edit the same document simultaneously.
 *
 * Architecture: Client-Server with CRDT merge
 *
 *   Peer A ──┐                    ┌── Peer A'
 *            ├──▶  Server  ──▶   ├── Peer B'
 *   Peer B ──┘    (relay)        └── Peer C'
 *
 * The server acts as a relay and ordering authority.
 * Each peer maintains its own CRDT replica.
 * Operations are broadcast to all peers.
 *
 * 💡 WHY NOT PURE P2P?
 * Pure P2P requires complex discovery and NAT traversal.
 * A relay server simplifies the architecture while still
 * leveraging CRDT's conflict-free merge properties.
 */

import { CRDTOperation, CRDTDocument } from '../crdt/CRDTDocument';
import { FormatCommand, FormatManager } from '../formatting/FormatTypes';

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

/** Event handler type */
type EventHandler = (event: string, data: any) => void;

/**
 * Manages collaborative editing sessions.
 *
 * ⭐ BROADCAST PATTERN:
 * When a local edit happens:
 * 1. Apply the operation to the local CRDT
 * 2. Broadcast the operation to all peers
 * 3. Each peer applies the operation to their local CRDT
 *
 * Because CRDT operations commute, order doesn't matter!
 */
export class CollaborationManager {
  /** The local CRDT document */
  private document: CRDTDocument;
  /** The local format manager */
  private formatManager: FormatManager;
  /** Known peers */
  private peers: Map<string, Peer> = new Map();
  /** Event handlers */
  private handlers: Map<string, EventHandler[]> = new Map();
  /** Local peer ID */
  public readonly localPeerId: string;
  /** Whether we're connected to a session */
  private connected: boolean = false;
  /** Operation history for debugging */
  private operationLog: CollabMessage[] = [];

  constructor(siteId: string, document: CRDTDocument, formatManager: FormatManager) {
    this.localPeerId = siteId;
    this.document = document;
    this.formatManager = formatManager;
  }

  /**
   * Register an event handler
   */
  on(event: string, handler: EventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  /**
   * Emit an event to all registered handlers
   */
  private emit(event: string, data: any): void {
    const handlers = this.handlers.get(event) || [];
    for (const handler of handlers) {
      handler(event, data);
    }
  }

  /**
   * Join a collaboration session
   */
  join(peerName: string): void {
    const peer: Peer = {
      id: this.localPeerId,
      name: peerName,
      connected: true,
      lastActivity: Date.now(),
    };
    this.peers.set(this.localPeerId, peer);
    this.connected = true;

    this.emit('peer:join', peer);
  }

  /**
   * Leave the collaboration session
   */
  leave(): void {
    this.connected = false;
    const peer = this.peers.get(this.localPeerId);
    if (peer) {
      peer.connected = false;
    }
    this.emit('peer:leave', { peerId: this.localPeerId });
  }

  /**
   * Add a remote peer (simulating peer discovery)
   */
  addRemotePeer(peer: Peer): void {
    this.peers.set(peer.id, peer);
    this.emit('peer:join', peer);
  }

  /**
   * Remove a remote peer
   */
  removeRemotePeer(peerId: string): void {
    this.peers.delete(peerId);
    this.emit('peer:leave', { peerId });
  }

  /**
   * Broadcast a local operation to all peers.
   *
   * In a real system, this would send over WebSocket/WebRTC.
   * Here we use a callback pattern for simulation.
   */
  broadcastOperation(op: CRDTOperation): CollabMessage {
    const message: CollabMessage = {
      type: 'operation',
      senderId: this.localPeerId,
      operation: op,
      timestamp: Date.now(),
    };

    this.operationLog.push(message);
    this.emit('operation:sent', message);
    return message;
  }

  /**
   * Broadcast a format command
   */
  broadcastFormat(cmd: FormatCommand): CollabMessage {
    const message: CollabMessage = {
      type: 'format',
      senderId: this.localPeerId,
      formatCommand: cmd,
      timestamp: Date.now(),
    };

    this.operationLog.push(message);
    this.emit('format:sent', message);
    return message;
  }

  /**
   * Broadcast awareness info (cursor position, etc.)
   */
  broadcastAwareness(cursorPosition: number, selection?: { start: number; end: number }): CollabMessage {
    const message: CollabMessage = {
      type: 'awareness',
      senderId: this.localPeerId,
      awareness: { cursorPosition, selection },
      timestamp: Date.now(),
    };

    this.emit('awareness:sent', message);
    return message;
  }

  /**
   * Receive and process a message from a remote peer.
   *
   * ⭐ REMOTE OPERATION PROCESSING:
   * When we receive an operation from a remote peer:
   * 1. Apply it to our local CRDT (guaranteed to converge)
   * 2. Update formatting if needed
   * 3. Notify UI to re-render
   */
  receiveMessage(message: CollabMessage): void {
    this.operationLog.push(message);

    switch (message.type) {
      case 'operation':
        if (message.operation) {
          this.document.applyRemoteOp(message.operation);
          this.emit('operation:received', message);
          this.emit('document:changed', { source: 'remote', peerId: message.senderId });
        }
        break;

      case 'format':
        if (message.formatCommand) {
          this.formatManager.applyRemoteCommand(message.formatCommand);
          this.emit('format:received', message);
          this.emit('document:changed', { source: 'remote', peerId: message.senderId });
        }
        break;

      case 'awareness':
        if (message.awareness) {
          const peer = this.peers.get(message.senderId);
          if (peer) {
            peer.cursorPosition = message.awareness.cursorPosition;
            peer.lastActivity = Date.now();
          }
          this.emit('awareness:received', message);
        }
        break;

      case 'join':
        if (message.senderId !== this.localPeerId) {
          this.addRemotePeer({
            id: message.senderId,
            name: `Peer-${message.senderId}`,
            connected: true,
            lastActivity: Date.now(),
          });
        }
        break;

      case 'leave':
        this.removeRemotePeer(message.senderId);
        break;
    }
  }

  /**
   * Get all connected peers
   */
  getPeers(): Peer[] {
    return Array.from(this.peers.values()).filter(p => p.connected);
  }

  /**
   * Get the operation log (for debugging)
   */
  getOperationLog(): CollabMessage[] {
    return [...this.operationLog];
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connected;
  }
}
