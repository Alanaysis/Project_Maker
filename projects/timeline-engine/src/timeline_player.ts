/**
 * Timeline Player
 *
 * Computes the current state of a timeline at a given time.
 * Evaluates all registered keyframe animations and clips.
 */

import { KeyframeTrack } from './keyframe';
import { AnimationClip } from './animation_clip';
import { TimelineStateOutput, KeyframeConfig } from './types';

export class TimelinePlayer {
  private keyframeTracks: Map<string, KeyframeTrack>;
  private clips: Map<string, AnimationClip>;
  private currentTime: number;
  private totalDuration: number;

  constructor() {
    this.keyframeTracks = new Map();
    this.clips = new Map();
    this.currentTime = 0;
    this.totalDuration = 1000;
  }

  /**
   * Register a keyframe animation.
   */
  addKeyframeAnimation(config: KeyframeConfig): void {
    const track = new KeyframeTrack(
      config.keyframes.map(kf => ({ time: kf.time / (config.duration || 1000), value: kf.value })),
      config.easing
    );
    this.keyframeTracks.set(config.property, track);
    this.totalDuration = config.duration || 1000;
  }

  /**
   * Remove a keyframe animation.
   */
  removeKeyframeAnimation(property: string): void {
    this.keyframeTracks.delete(property);
  }

  /**
   * Register an animation clip.
   */
  addClip(clip: AnimationClip): void {
    this.clips.set(clip.getName(), clip);
  }

  /**
   * Remove an animation clip.
   */
  removeClip(name: string): void {
    this.clips.delete(name);
  }

  /**
   * Compute the state at the given time.
   */
  compute(time: number): TimelineStateOutput {
    this.currentTime = time;
    const state: TimelineStateOutput = {};

    // Evaluate keyframe tracks
    for (const [property, track] of this.keyframeTracks) {
      const progress = time / this.totalDuration;
      state[property] = track.interpolate(progress);
    }

    // Evaluate clips
    for (const [, clip] of this.clips) {
      const clipTime = time % clip.getDuration();
      for (const property of clip.getProperties()) {
        if (!state[property]) {
          state[property] = clip.getValueAt(property, clipTime);
        }
      }
    }

    return state;
  }

  /**
   * Get the current time.
   */
  getCurrentTime(): number {
    return this.currentTime;
  }

  /**
   * Get the total duration.
   */
  getTotalDuration(): number {
    return this.totalDuration;
  }

  /**
   * Reset the player.
   */
  reset(): void {
    this.currentTime = 0;
  }

  /**
   * Set the total duration.
   */
  setTotalDuration(duration: number): void {
    this.totalDuration = duration;
  }
}
