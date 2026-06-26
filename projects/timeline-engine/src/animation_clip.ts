/**
 * Animation Clip
 *
 * Reusable animation definition containing multiple keyframe tracks.
 */

import { AnimationClipConfig, KeyframeEntry, EasingFunction } from './types';
import { KeyframeTrack } from './keyframe';
import { resolveEasing } from './easing';

export class AnimationClip {
  private name: string;
  private animations: Map<string, KeyframeTrack>;
  private duration: number;

  constructor(config: AnimationClipConfig) {
    this.name = config.name;
    this.duration = config.duration;
    this.animations = new Map();

    for (const anim of config.animations) {
      this.animations.set(anim.property, new KeyframeTrack(anim.keyframes, anim.easing));
    }
  }

  getName(): string {
    return this.name;
  }

  getAnimations(): Map<string, KeyframeTrack> {
    return new Map(this.animations);
  }

  getDuration(): number {
    return this.duration;
  }

  /**
   * Compute the value for a specific property at a given time.
   */
  getValueAt(property: string, time: number): number {
    const track = this.animations.get(property);
    if (!track) {
      return 0;
    }
    const normalizedTime = (time % this.duration) / this.duration;
    return track.interpolate(normalizedTime);
  }

  /**
   * Get all properties in this clip.
   */
  getProperties(): string[] {
    return Array.from(this.animations.keys());
  }

  /**
   * Update a track's keyframes.
   */
  updateAnimation(property: string, keyframes: KeyframeEntry[], easing?: EasingFunction | string): void {
    const track = this.animations.get(property);
    if (track) {
      track.updateKeyframes(keyframes);
      if (easing) {
        track.updateEasing(easing);
      }
    }
  }
}
