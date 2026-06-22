/**
 * ============================================================
 * Version History - Document Version Control
 * ============================================================
 *
 * ⭐ VERSION CONTROL CONCEPTS:
 * Inspired by Git, each "commit" captures a snapshot of the document
 * at a point in time, along with metadata about what changed.
 *
 * Key features:
 * - Snapshot-based storage (full document state at each version)
 * - Branch and merge support
 * - Diff computation between versions
 * - Named versions (tags)
 *
 * 💡 DESIGN DECISION: Snapshot vs. Operation Log
 * - Snapshot: Store full document state. Simple, fast reads, large storage.
 * - Operation log: Store only operations. Compact, slow reads, complex replay.
 * - We use snapshots for simplicity. Real systems often use a hybrid.
 */

import { CRDTDocument } from '../crdt/CRDTDocument';
import { FormatMark } from '../formatting/FormatTypes';

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

/**
 * Manages document version history.
 */
export class VersionHistory {
  private versions: Map<string, Version> = new Map();
  private currentVersionId: string | null = null;
  private versionCounter: number = 0;

  /**
   * Create a new version (commit)
   */
  commit(
    text: string,
    formatMarks: FormatMark[],
    author: string,
    message: string,
    tag?: string
  ): Version {
    const id = `v${++this.versionCounter}`;
    const version: Version = {
      id,
      parentId: this.currentVersionId,
      timestamp: Date.now(),
      author,
      message,
      text,
      formatMarks: [...formatMarks],
      tag,
    };

    this.versions.set(id, version);
    this.currentVersionId = id;

    return version;
  }

  /**
   * Get a specific version
   */
  getVersion(id: string): Version | undefined {
    return this.versions.get(id);
  }

  /**
   * Get the current version
   */
  getCurrentVersion(): Version | undefined {
    return this.currentVersionId ? this.versions.get(this.currentVersionId) : undefined;
  }

  /**
   * Get all versions in chronological order
   */
  getAllVersions(): Version[] {
    const result: Version[] = [];
    let current = this.currentVersionId;

    while (current) {
      const version = this.versions.get(current);
      if (!version) break;
      result.unshift(version);
      current = version.parentId;
    }

    return result;
  }

  /**
   * Revert to a specific version
   */
  revertTo(versionId: string): Version | undefined {
    const version = this.versions.get(versionId);
    if (!version) return undefined;

    // Create a new version that copies the old content
    return this.commit(
      version.text,
      version.formatMarks,
      'system',
      `Reverted to ${versionId}`,
    );
  }

  /**
   * Tag a version with a name
   */
  tagVersion(versionId: string, tag: string): boolean {
    const version = this.versions.get(versionId);
    if (!version) return false;
    version.tag = tag;
    return true;
  }

  /**
   * Get a version by tag name
   */
  getVersionByTag(tag: string): Version | undefined {
    for (const version of this.versions.values()) {
      if (version.tag === tag) return version;
    }
    return undefined;
  }

  /**
   * Compute a simple diff between two text strings
   *
   * ⭐ DIFF ALGORITHM:
   * This is a simplified diff. Production systems use Myers' diff algorithm
   * (used by Git) or more advanced algorithms like patience diff.
   */
  computeDiff(oldText: string, newText: string): Diff[] {
    const diffs: Diff[] = [];

    // Find common prefix
    let prefixLen = 0;
    while (prefixLen < oldText.length && prefixLen < newText.length &&
           oldText[prefixLen] === newText[prefixLen]) {
      prefixLen++;
    }

    // Find common suffix
    let suffixLen = 0;
    while (suffixLen < oldText.length - prefixLen &&
           suffixLen < newText.length - prefixLen &&
           oldText[oldText.length - 1 - suffixLen] === newText[newText.length - 1 - suffixLen]) {
      suffixLen++;
    }

    const removed = oldText.substring(prefixLen, oldText.length - suffixLen);
    const added = newText.substring(prefixLen, newText.length - suffixLen);

    if (removed.length > 0 || added.length > 0) {
      diffs.push({
        type: removed.length > 0 && added.length > 0 ? 'replace' :
              removed.length > 0 ? 'delete' : 'insert',
        position: prefixLen,
        removed,
        added,
      });
    }

    return diffs;
  }

  /**
   * Get the number of versions
   */
  get size(): number {
    return this.versions.size;
  }

  /**
   * Export version history
   */
  exportState(): { versions: Version[]; currentVersionId: string | null } {
    return {
      versions: Array.from(this.versions.values()),
      currentVersionId: this.currentVersionId,
    };
  }

  /**
   * Import version history
   */
  importState(state: { versions: Version[]; currentVersionId: string | null }): void {
    this.versions.clear();
    for (const version of state.versions) {
      this.versions.set(version.id, version);
    }
    this.currentVersionId = state.currentVersionId;
  }
}
