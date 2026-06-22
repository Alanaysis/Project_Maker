/**
 * ============================================================
 * Rich Text Formatting Types
 * ============================================================
 *
 * ⭐ RICH TEXT MODEL:
 * Rich text is stored as a flat sequence of characters, where each
 * character can have formatting "marks" applied to it.
 *
 * This is the "flat spans" model (used by ProseMirror, Slate):
 * - Bold: each bold character has a "bold" mark
 * - Italic: each italic character has an "italic" mark
 * - Ranges: formatting is tracked as (start, end, mark) tuples
 *
 * 💡 ALTERNATIVE APPROACHES:
 * - Tree-based (like OTTI): Nested spans, harder to merge
 * - Peritext (Ink & Switch): Designed specifically for CRDT + rich text
 * - Our approach: Marks as metadata on character IDs
 */

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

/**
 * Manages formatting marks on a document.
 *
 * ⭐ CONFLICT RESOLUTION FOR FORMATTING:
 * When two users apply conflicting formatting (e.g., one applies bold,
 * the other removes it at the same range), we use timestamp-based
 * "last writer wins" semantics.
 *
 * 💡 This is a simplification. Real systems like Peritext use more
 * sophisticated semantics (e.g., "intent-preserving" merges).
 */
export class FormatManager {
  private marks: FormatMark[] = [];

  /**
   * Apply a formatting mark to a range
   */
  applyMark(type: MarkType, start: number, end: number, siteId: string): FormatMark {
    const mark: FormatMark = {
      type,
      start,
      end,
      siteId,
      timestamp: Date.now(),
      active: true,
    };
    this.marks.push(mark);
    return mark;
  }

  /**
   * Remove a formatting mark from a range
   */
  removeMark(type: MarkType, start: number, end: number, siteId: string): FormatMark {
    const mark: FormatMark = {
      type,
      start,
      end,
      siteId,
      timestamp: Date.now(),
      active: false,
    };
    this.marks.push(mark);
    return mark;
  }

  /**
   * Get active marks at a specific position
   */
  getMarksAt(position: number): MarkType[] {
    const activeMarks = new Set<MarkType>();

    // Process marks in order; later marks override earlier ones
    for (const mark of this.marks) {
      if (position >= mark.start && position < mark.end) {
        if (mark.active) {
          activeMarks.add(mark.type);
        } else {
          activeMarks.delete(mark.type);
        }
      }
    }

    return Array.from(activeMarks);
  }

  /**
   * Split text into formatted spans for rendering
   */
  getFormattedSpans(text: string): FormatSpan[] {
    if (text.length === 0) return [];

    const spans: FormatSpan[] = [];
    let currentStart = 0;
    let currentMarks = this.getMarksAt(0);

    for (let i = 1; i < text.length; i++) {
      const marks = this.getMarksAt(i);
      if (!this.marksEqual(marks, currentMarks)) {
        spans.push({
          text: text.substring(currentStart, i),
          marks: currentMarks,
          startPos: currentStart,
          endPos: i,
        });
        currentStart = i;
        currentMarks = marks;
      }
    }

    // Add the last span
    spans.push({
      text: text.substring(currentStart),
      marks: currentMarks,
      startPos: currentStart,
      endPos: text.length,
    });

    return spans;
  }

  /**
   * Adjust mark positions after an insertion
   *
   * ⭐ POSITION ADJUSTMENT:
   * When characters are inserted, marks after the insertion point
   * need their positions shifted. This is critical for maintaining
   * correct formatting during collaborative editing.
   */
  adjustForInsert(position: number, length: number): void {
    for (const mark of this.marks) {
      if (mark.start >= position) {
        mark.start += length;
        mark.end += length;
      } else if (mark.end > position) {
        mark.end += length;
      }
    }
  }

  /**
   * Adjust mark positions after a deletion
   */
  adjustForDelete(position: number, length: number): void {
    for (const mark of this.marks) {
      if (mark.start >= position + length) {
        mark.start -= length;
        mark.end -= length;
      } else if (mark.start >= position) {
        if (mark.end <= position + length) {
          // Entire mark is within deleted range
          mark.active = false;
        } else {
          mark.start = position;
          mark.end -= length;
        }
      } else if (mark.end > position) {
        mark.end -= Math.min(length, mark.end - position);
      }
    }
  }

  /**
   * Apply a remote formatting command
   */
  applyRemoteCommand(cmd: FormatCommand): void {
    if (cmd.type === 'apply') {
      this.applyMark(cmd.mark, cmd.start, cmd.end, cmd.siteId);
    } else {
      this.removeMark(cmd.mark, cmd.start, cmd.end, cmd.siteId);
    }
  }

  /**
   * Check if two mark arrays are equal
   */
  private marksEqual(a: MarkType[], b: MarkType[]): boolean {
    if (a.length !== b.length) return false;
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    return sortedA.every((v, i) => v === sortedB[i]);
  }

  /**
   * Export formatting state
   */
  exportState(): FormatMark[] {
    return [...this.marks];
  }

  /**
   * Import formatting state
   */
  importState(marks: FormatMark[]): void {
    this.marks = [...marks];
  }
}
