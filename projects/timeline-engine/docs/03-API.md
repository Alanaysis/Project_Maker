# API Reference: Timeline Engine

## Timeline

### Constructor
```typescript
new Timeline(options?: TimelineOptions);
```

### Options
```typescript
interface TimelineOptions {
  duration?: number;        // Total duration in ms (default: 1000)
  fps?: number;             // Target FPS (default: 60)
  loop?: boolean;           // Loop animation (default: false)
  autoplay?: boolean;       // Start playing immediately (default: false)
}
```

### Methods
```typescript
// Playback control
play(): void;
pause(): void;
stop(): void;
toggle(): void;

// Seek
seek(progress: number): void;   // 0-1 progress
seek(time: number): void;       // Absolute time in ms

// Keyframe animation
addKeyframe(config: KeyframeConfig): AnimationHandle;
removeKeyframe(name: string): void;

// Animation clip
addClip(clip: AnimationClip): void;
removeClip(name: string): void;

// State
getState(): Record<string, number>;
getProgress(): number;
getCurrentTime(): number;
isPlaying(): boolean;
isPaused(): boolean;
isStopped(): boolean;

// Events
on(event: 'play' | 'pause' | 'stop' | 'complete' | 'frame', callback: Function): void;
off(event: string, callback: Function): void;

// Cleanup
destroy(): void;
```

## KeyframeConfig
```typescript
interface KeyframeConfig {
  name: string;
  property: string;
  keyframes: Array<{
    time: number;    // 0-1 progress or absolute time
    value: number;
  }>;
  duration?: number;  // ms
  easing?: EasingFunction;
  delay?: number;     // ms
}
```

## Easing Functions

### Linear
```typescript
Easing.linear(t: number): number;
```

### Quadratic
```typescript
Easing.easeInQuad(t: number): number;
Easing.easeOutQuad(t: number): number;
Easing.easeInOutQuad(t: number): number;
```

### Cubic
```typescript
Easing.easeInCubic(t: number): number;
Easing.easeOutCubic(t: number): number;
Easing.easeInOutCubic(t: number): number;
```

### Quartic
```typescript
Easing.easeInQuart(t: number): number;
Easing.easeOutQuart(t: number): number;
Easing.easeInOutQuart(t: number): number;
```

### Quintic
```typescript
Easing.easeInQuint(t: number): number;
Easing.easeOutQuint(t: number): number;
Easing.easeInOutQuint(t: number): number;
```

### Sine
```typescript
Easing.easeInSine(t: number): number;
Easing.easeOutSine(t: number): number;
Easing.easeInOutSine(t: number): number;
```

### Exponential
```typescript
Easing.easeInExpo(t: number): number;
Easing.easeOutExpo(t: number): number;
Easing.easeInOutExpo(t: number): number;
```

### Circular
```typescript
Easing.easeInCirc(t: number): number;
Easing.easeOutCirc(t: number): number;
Easing.easeInOutCirc(t: number): number;
```

### Elastic
```typescript
Easing.easeInElastic(t: number): number;
Easing.easeOutElastic(t: number): number;
Easing.easeInOutElastic(t: number): number;
```

### Back
```typescript
Easing.easeInBack(t: number): number;
Easing.easeOutBack(t: number): number;
Easing.easeInOutBack(t: number): number;
```

### Bounce
```typescript
Easing.easeInBounce(t: number): number;
Easing.easeOutBounce(t: number): number;
Easing.easeInOutBounce(t: number): number;
```

## AnimationClip
```typescript
class AnimationClip {
  constructor(name: string, animations: KeyframeConfig[]);
  getName(): string;
  getAnimations(): KeyframeConfig[];
  getDuration(): number;
}
```

## TimelinePlayer
```typescript
class TimelinePlayer {
  constructor(timeline: Timeline);
  compute(time: number): Record<string, number>;
  reset(): void;
}
```

## Keyframe
```typescript
class Keyframe {
  constructor(time: number, value: number);
  getTime(): number;
  getValue(): number;
  setTime(time: number): void;
  setValue(value: number): void;
}
```

## EasingFunction
```typescript
type EasingFunction = (t: number) => number;
// t: progress from 0 to 1
// returns: eased progress from 0 to 1
```

## Utility Functions
```typescript
// Register custom easing
registerEasing(name: string, fn: EasingFunction): void;

// Get all easing names
getEasingNames(): string[];

// Resolve easing by name or function
resolveEasing(easing: EasingFunction | string): EasingFunction;

// Linear interpolation
lerp(start: number, end: number, t: number): number;

// Clamp value
clamp(value: number, min: number, max: number): number;
```
