/**
 * Timeline
 *
 * Core timeline class that manages keyframe animations,
 * animation clips, playback state, and state computation.
 */

import { KeyframeConfig, KeyframeEntry, TimelineState, TimelineEvent, TimelineOptions, AnimationHandle, TimelineStateOutput, EasingFunction, TimelineEventListener } from './types';
import { KeyframeTrack } from './keyframe';
import { AnimationClip } from './animation_clip';
import { TimelinePlayer } from './timeline_player';
import { resolveEasing, clamp } from './easing';

export class Timeline {
  private keyframeAnimations: Map<string, KeyframeConfig>;
  private clips: Map<string, AnimationClip>;
  private player: TimelinePlayer;
  private state: TimelineState;
  private currentTime: number;
  private totalDuration: number;
  private fps: number;
  private loop: boolean;
  private listeners: Map<string, Array<TimelineEventListener>>;
  private lastFrameTime: number;
  private rafId: number | null;

  constructor(options: TimelineOptions = {}) {
    this.keyframeAnimations = new Map();
    this.clips = new Map();
    this.player = new TimelinePlayer();
    this.state = TimelineState.IDLE;
    this.currentTime = 0;
    this.totalDuration = options.duration || 1000;
    this.fps = options.fps || 60;
    this.loop = options.loop || false;
    this.listeners = new Map();
    this.lastFrameTime = 0;
    this.rafId = null;

    this.player.setTotalDuration(this.totalDuration);

    if (options.autoplay) {
      this.play();
    }
  }

  /**
   * Add a keyframe animation.
   */
  addKeyframe(config: KeyframeConfig): AnimationHandle {
    const duration = config.duration || this.totalDuration;
    // Keyframe times are in 0-1 progress range; player will normalize by duration
    const timeBasedKeyframes = config.keyframes.map(kf => ({
      time: kf.time * duration,
      value: kf.value,
    }));

    const track = new KeyframeTrack(timeBasedKeyframes, config.easing);
    this.keyframeAnimations.set(config.property, {
      ...config,
      duration,
      keyframes: timeBasedKeyframes,
    });

    this.player.addKeyframeAnimation({
      name: config.name || config.property,
      property: config.property,
      keyframes: timeBasedKeyframes,
      duration,
      easing: config.easing,
      delay: config.delay,
    });

    return {
      name: config.name || config.property,
      property: config.property,
      remove: () => this.removeKeyframe(config.property),
      updateKeyframes: (kfs: KeyframeEntry[]) => this.updateKeyframes(config.property, kfs),
      updateEasing: (easing: EasingFunction | string) => this.updateEasing(config.property, easing),
    };
  }

  /**
   * Remove a keyframe animation.
   */
  removeKeyframe(property: string): void {
    this.keyframeAnimations.delete(property);
    this.player.removeKeyframeAnimation(property);
  }

  /**
   * Add an animation clip.
   */
  addClip(clip: AnimationClip): void {
    this.clips.set(clip.getName(), clip);
    this.player.addClip(clip);
  }

  /**
   * Remove an animation clip.
   */
  removeClip(name: string): void {
    this.clips.delete(name);
    this.player.removeClip(name);
  }

  /**
   * Play the timeline.
   */
  play(): void {
    this.state = TimelineState.PLAYING;
    this.lastFrameTime = performance.now();
    this.rafId = requestAnimationFrame(this.tick.bind(this));
    this.emit('play', { time: this.currentTime });
  }

  /**
   * Pause the timeline.
   */
  pause(): void {
    if (this.state !== TimelineState.PLAYING) return;
    this.state = TimelineState.PAUSED;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.emit('pause', { time: this.currentTime });
  }

  /**
   * Stop the timeline and reset.
   */
  stop(): void {
    this.pause();
    this.currentTime = 0;
    this.state = TimelineState.STOPPED;
    this.player.reset();
    this.emit('stop', { time: 0 });
  }

  /**
   * Toggle play/pause.
   */
  toggle(): void {
    if (this.state === TimelineState.PLAYING) {
      this.pause();
    } else {
      this.play();
    }
  }

  /**
   * Seek to a specific progress (0-1) or time (ms).
   */
  seek(target: number): void {
    if (target >= 0 && target <= 1) {
      // Progress
      this.currentTime = target * this.totalDuration;
    } else {
      // Absolute time
      this.currentTime = Math.max(0, Math.min(target, this.totalDuration));
    }

    // Check completion
    if (this.currentTime >= this.totalDuration - 0.1) {
      if (this.loop) {
        this.currentTime = this.currentTime % this.totalDuration;
      } else {
        this.currentTime = this.totalDuration;
        if (this.state === TimelineState.PLAYING) {
          this.state = TimelineState.COMPLETED;
          this.emit('complete', { time: this.currentTime });
        }
      }
    }

    this.player.setTotalDuration(this.totalDuration);
  }

  /**
   * Get the current timeline state output.
   */
  getState(): TimelineStateOutput {
    return this.player.compute(this.currentTime);
  }

  /**
   * Get current progress (0-1).
   */
  getProgress(): number {
    return this.currentTime / this.totalDuration;
  }

  /**
   * Get current time in ms.
   */
  getCurrentTime(): number {
    return this.currentTime;
  }

  /**
   * Get total duration in ms.
   */
  getTotalDuration(): number {
    return this.totalDuration;
  }

  /**
   * Set total duration.
   */
  setTotalDuration(duration: number): void {
    this.totalDuration = duration;
    this.player.setTotalDuration(duration);
  }

  /**
   * Check if timeline is playing.
   */
  isPlaying(): boolean {
    return this.state === TimelineState.PLAYING;
  }

  /**
   * Check if timeline is paused.
   */
  isPaused(): boolean {
    return this.state === TimelineState.PAUSED;
  }

  /**
   * Check if timeline is stopped.
   */
  isStopped(): boolean {
    return this.state === TimelineState.STOPPED;
  }

  /**
   * Check if timeline is completed.
   */
  isCompleted(): boolean {
    return this.state === TimelineState.COMPLETED;
  }

  /**
   * Update keyframes for a property.
   */
  updateKeyframes(property: string, keyframes: KeyframeEntry[]): void {
    const anim = this.keyframeAnimations.get(property);
    if (!anim) return;

    const duration = anim.duration || this.totalDuration;
    // Convert from progress (0-1) to time-based
    const timeBased = keyframes.map(kf => ({
      time: kf.time * duration,
      value: kf.value,
    }));

    this.keyframeAnimations.set(property, { ...anim, keyframes: timeBased });
    this.player.addKeyframeAnimation({
      name: anim.name,
      property,
      keyframes: timeBased,
      duration,
      easing: anim.easing,
      delay: anim.delay,
    });
  }

  /**
   * Update easing for a property.
   */
  updateEasing(property: string, easing: EasingFunction | string): void {
    const anim = this.keyframeAnimations.get(property);
    if (!anim) return;

    this.keyframeAnimations.set(property, { ...anim, easing });
    this.player.addKeyframeAnimation({
      name: anim.name,
      property,
      keyframes: anim.keyframes,
      duration: anim.duration || this.totalDuration,
      easing,
      delay: anim.delay,
    });
  }

  /**
   * Register an event listener.
   */
  on(event: TimelineEvent, callback: TimelineEventListener): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  /**
   * Remove an event listener.
   */
  off(event: TimelineEvent, callback: TimelineEventListener): void {
    const cbs = this.listeners.get(event);
    if (cbs) {
      const idx = cbs.indexOf(callback);
      if (idx !== -1) cbs.splice(idx, 1);
    }
  }

  /**
   * Destroy the timeline and clean up.
   */
  destroy(): void {
    this.pause();
    this.keyframeAnimations.clear();
    this.clips.clear();
    this.listeners.clear();
    this.state = TimelineState.STOPPED;
    this.currentTime = 0;
  }

  // === Private ===

  private emit(event: TimelineEvent, data?: any): void {
    const cbs = this.listeners.get(event);
    if (cbs) {
      for (const cb of cbs) {
        try {
          cb(data);
        } catch (e) {
          console.error(`Timeline event callback error: ${e}`);
        }
      }
    }
  }

  private tick(timestamp: number): void {
    if (this.state !== TimelineState.PLAYING) return;

    const delta = timestamp - this.lastFrameTime;
    this.lastFrameTime = timestamp;

    this.currentTime += delta;

    // Check completion
    if (this.currentTime >= this.totalDuration) {
      if (this.loop) {
        this.currentTime = this.currentTime % this.totalDuration;
        this.lastFrameTime = timestamp;
      } else {
        this.currentTime = this.totalDuration;
        this.state = TimelineState.COMPLETED;
        this.emit('complete', { time: this.currentTime });
        return;
      }
    }

    // Emit frame event
    this.emit('frame', {
      time: this.currentTime,
      progress: this.getProgress(),
      state: this.getState(),
    });

    // Continue
    this.rafId = requestAnimationFrame(this.tick.bind(this));
  }
}
