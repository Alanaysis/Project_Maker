/**
 * ============================================================
 * CRDT Document - Conflict-free Replicated Data Type for Text
 * ============================================================
 *
 * ⭐ KEY CONCEPT: CRDT (Conflict-free Replicated Data Types)
 *
 * A CRDT is a data structure that can be replicated across multiple
 * computers, modified independently and concurrently, and then merged
 * such that all replicas converge to the same state.
 *
 * This implementation uses a "sequence CRDT" approach similar to LSEQ/RGA:
 * - Each character gets a globally unique ID (siteId + logical clock)
 * - Characters are ordered by their position ID, not by array index
 * - Insertions and deletions commute naturally
 *
 * 💡 WHY CRDT over OT (Operational Transformation)?
 *
 * OT requires a central server to transform operations, which adds
 * complexity and a single point of failure. CRDTs can merge without
 * coordination, enabling peer-to-peer collaboration.
 *
 * Trade-offs:
 * - CRDT: More metadata per character, but simpler merge logic
 * - OT: Less metadata, but complex transform functions
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

/**
 * The main CRDT document implementation.
 *
 * ⭐ ALGORITHM: RGA (Replicated Growable Array)
 *
 * RGA maintains an ordered sequence where:
 * 1. Each element has a unique ID and a parent pointer
 * 2. Insert "after X" means: find X, then insert at the position
 *    right after X in the total order
 * 3. When two inserts happen after the same parent concurrently,
 *    we use (timestamp, siteId) to break ties deterministically
 * 4. Deletions are logical (tombstones) - we don't physically remove
 *
 * This ensures all replicas converge to the same sequence.
 */
export class CRDTDocument {
  /** All character nodes indexed by their ID */
  private nodes: Map<string, CharNode> = new Map();
  /** The logical clock for this site */
  private clock: number = 0;
  /** This site's unique identifier */
  public readonly siteId: string;
  /** Ordered list of node IDs (the sequence) */
  private sequence: string[] = [];

  constructor(siteId: string) {
    this.siteId = siteId;
    // Create a sentinel root node
    const rootId = this.makeId('__root__');
    const rootNode: CharNode = {
      id: rootId,
      value: '',
      deleted: false,
      parentId: null,
      timestamp: 0,
    };
    this.nodes.set(this.idToKey(rootId), rootNode);
    this.sequence.push(this.idToKey(rootId));
  }

  /**
   * Create a unique character ID combining site ID and clock
   */
  private makeId(siteId?: string): CharId {
    return { siteId: siteId || this.siteId, clock: this.clock++ };
  }

  /**
   * Convert a CharId to a string key for Map storage
   */
  private idToKey(id: CharId): string {
    return `${id.siteId}:${id.clock}`;
  }

  /**
   * Find the index of a character in the sequence by its ID
   */
  private findIndex(id: CharId): number {
    const key = this.idToKey(id);
    return this.sequence.indexOf(key);
  }

  /**
   * Insert a character at a specific position in the document.
   *
   * ⭐ INSERTION ALGORITHM:
   * 1. Create a new CharNode with a unique ID
   * 2. Set its parentId to the character at position-1
   * 3. Find where to place it in the total order
   * 4. Use (timestamp, siteId) for deterministic tie-breaking
   *
   * @param position - The position to insert at (0-based)
   * @param value - The character to insert
   * @returns The created CharNode and the operation
   */
  insert(position: number, value: string): { node: CharNode; op: CRDTOperation } {
    const id = this.makeId();
    const parentKey = this.sequence[position] || this.sequence[this.sequence.length - 1];
    const parentId = this.nodes.get(parentKey)?.id || null;

    const node: CharNode = {
      id,
      value,
      deleted: false,
      parentId,
      timestamp: Date.now(),
    };

    this.nodes.set(this.idToKey(id), node);

    // Find insertion point: after parent, before next
    const parentIndex = this.findIndex(parentId!);
    let insertIndex = parentIndex + 1;

    // Tie-breaking: if there are concurrent inserts at the same position,
    // order by (timestamp DESC, siteId ASC) for deterministic convergence
    while (insertIndex < this.sequence.length) {
      const existing = this.nodes.get(this.sequence[insertIndex]);
      if (!existing) break;

      // If existing node also has the same parent (concurrent insert)
      if (existing.parentId && parentId &&
          this.idToKey(existing.parentId) === this.idToKey(parentId)) {
        if (node.timestamp > existing.timestamp) {
          break; // Newer goes before older
        } else if (node.timestamp === existing.timestamp &&
                   node.id.siteId < existing.id.siteId) {
          break; // Same time: smaller siteId goes first
        }
        insertIndex++;
      } else {
        break;
      }
    }

    this.sequence.splice(insertIndex, 0, this.idToKey(id));

    const op: CRDTOperation = {
      type: 'insert',
      char: node,
      siteId: this.siteId,
      clock: id.clock,
    };

    return { node, op };
  }

  /**
   * Delete a character at a specific position (logical deletion / tombstone).
   *
   * ⭐ TOMBSTONE PATTERN:
   * We don't physically remove the character because:
   * 1. Other replicas might reference it for ordering
   * 2. We need to preserve the ID for concurrent operation resolution
   * 3. Cleanup (garbage collection) can happen later via a separate protocol
   *
   * @param position - The position of the character to delete
   * @returns The operation, or null if position is invalid
   */
  delete(position: number): CRDTOperation | null {
    if (position < 0 || position >= this.sequence.length) return null;

    const key = this.sequence[position];
    const node = this.nodes.get(key);
    if (!node || node.id.siteId === '__root__') return null;

    node.deleted = true;

    const op: CRDTOperation = {
      type: 'delete',
      targetId: node.id,
      siteId: this.siteId,
      clock: this.clock++,
    };

    return op;
  }

  /**
   * Apply an operation received from a remote site.
   *
   * ⭐ REMOTE OPERATION APPLICATION:
   * This is where CRDT magic happens. When we receive an operation
   * from another peer, we apply it in a way that guarantees convergence.
   *
   * For inserts: We apply the same insertion algorithm locally
   * For deletes: We mark the target character as deleted
   *
   * Because the algorithm is deterministic, all replicas converge.
   */
  applyRemoteOp(op: CRDTOperation): void {
    if (op.type === 'insert' && op.char) {
      // Update our clock to be at least as high as the remote clock
      this.clock = Math.max(this.clock, op.clock + 1);

      const charKey = this.idToKey(op.char.id);

      // Skip if we already have this character
      if (this.nodes.has(charKey)) return;

      // Store the node
      this.nodes.set(charKey, op.char);

      // Find insertion position
      if (op.char.parentId) {
        const parentIndex = this.findIndex(op.char.parentId);
        if (parentIndex === -1) {
          // Parent not found yet, append at end
          this.sequence.push(charKey);
          return;
        }

        let insertIndex = parentIndex + 1;

        // Same tie-breaking as local insert
        while (insertIndex < this.sequence.length) {
          const existing = this.nodes.get(this.sequence[insertIndex]);
          if (!existing) break;

          if (existing.parentId && op.char.parentId &&
              this.idToKey(existing.parentId) === this.idToKey(op.char.parentId)) {
            if (op.char.timestamp > existing.timestamp) {
              break;
            } else if (op.char.timestamp === existing.timestamp &&
                       op.char.id.siteId < existing.id.siteId) {
              break;
            }
            insertIndex++;
          } else {
            break;
          }
        }

        this.sequence.splice(insertIndex, 0, charKey);
      } else {
        this.sequence.push(charKey);
      }
    } else if (op.type === 'delete' && op.targetId) {
      this.clock = Math.max(this.clock, op.clock + 1);
      const key = this.idToKey(op.targetId);
      const node = this.nodes.get(key);
      if (node) {
        node.deleted = true;
      }
    }
  }

  /**
   * Get the current text content (excluding tombstones)
   */
  getText(): string {
    return this.sequence
      .map(key => this.nodes.get(key))
      .filter((n): n is CharNode => n !== undefined && !n.deleted && n.id.siteId !== '__root__')
      .map(n => n.value)
      .join('');
  }

  /**
   * Get the full document as an array of character info
   */
  getCharacters(): Array<{ char: string; position: number; id: CharId; deleted: boolean }> {
    let position = 0;
    return this.sequence
      .map(key => this.nodes.get(key))
      .filter((n): n is CharNode => n !== undefined && n.id.siteId !== '__root__')
      .map(n => ({
        char: n.value,
        position: position++,
        id: n.id,
        deleted: n.deleted,
      }));
  }

  /**
   * Get the length of the document (excluding tombstones)
   */
  get length(): number {
    return this.sequence
      .map(key => this.nodes.get(key))
      .filter(n => n !== undefined && !n.deleted && n.id.siteId !== '__root__')
      .length;
  }

  /**
   * Check if the document is empty
   */
  get isEmpty(): boolean {
    return this.length === 0;
  }

  /**
   * Export the document state for persistence or transfer
   */
  exportState(): { nodes: CharNode[]; clock: number; siteId: string } {
    return {
      nodes: Array.from(this.nodes.values()),
      clock: this.clock,
      siteId: this.siteId,
    };
  }

  /**
   * Import a previously exported document state
   */
  importState(state: { nodes: CharNode[]; clock: number; siteId: string }): void {
    this.nodes.clear();
    this.sequence = [];
    this.clock = state.clock;

    for (const node of state.nodes) {
      const key = this.idToKey(node.id);
      this.nodes.set(key, node);
      if (!node.deleted) {
        this.sequence.push(key);
      }
    }
  }
}
