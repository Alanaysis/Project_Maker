# Implementation: Animation Engine

## Implementation Overview

The animation engine is built in TypeScript with a modular architecture. Each module handles a specific concern and exports a clean API.

## Module Implementation Details

### 1. Easing Functions

Each easing function follows the signature `(t: number) => number` where:
- Input `t` is progress from 0 to 1
- Output is the eased value (usually 0 to 1)

**Polynomial Easing** (Quad, Cubic, Quart, Quint):
```typescript
// Ease-in: t^n
export const easeInCubic: EasingFunction = (t) => t * t * t;

// Ease-out: reverse of ease-in
export const easeOutCubic: EasingFunction = (t) => (--t) * t * t + 1;

// Ease-in-out: combine both halves
export const easeInOutCubic: EasingFunction = (t) =>
  t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
```

**Elastic Easing** (spring-like):
```typescript
export const easeOutElastic: EasingFunction = (t) => {
  if (t === 0 || t === 1) return t;
  const p = 0.3; // period
  const s = p / 4;
  return Math.pow(2, -10 * t) * Math.sin(((t - s) * (2 * Math.PI)) / p) + 1;
};
```

**Bounce Easing** (simulates bouncing ball):
```typescript
const bounceOut: EasingFunction = (t) => {
  const n1 = 7.5625;
  const d1 = 2.75;
  if (t < 1 / d1) return n1 * t * t;
  // ... progressive bounces
};
```

### 2. Style Interpolation

The engine handles multiple value types:

**Numeric values**: Direct lerp
```typescript
lerp(0, 100, 0.5) // → 50
```

**CSS units**: Parse, interpolate, reassemble
```typescript
interpolateNumeric('0px', '100px', 0.5) // → '50px'
```

**Colors**: Parse hex/rgb, interpolate channels
```typescript
interpolateColor('#000', '#fff', 0.5) // → 'rgb(128, 128, 128)'
```

**Auto-detection**: `interpolateStyle()` detects type automatically

### 3. Animation State Machine

The Animation class implements a state machine:
- `IDLE`: Initial state, not started
- `RUNNING`: Actively updating each frame
- `PAUSED`: Paused, can resume
- `COMPLETED`: Finished all iterations
- `CANCELLED`: Stopped early

### 4. Animation Queue

The queue uses Promises for sequential execution:
```typescript
class AnimationQueue {
  async animate(config): Promise<void> {
    // Add to queue, wait for completion
    return new Promise((resolve) => {
      this.queue.push({ config, resolve });
      this.processNext();
    });
  }
}
```

### 5. Engine Main Loop

The engine runs a single rAF loop for all animations:
```typescript
private loop(timestamp: number): void {
  // Update all registered animations
  this.animations.forEach(anim => anim.update(timestamp));
  this.tweens.forEach(tween => tween.update(timestamp));

  // Cleanup completed
  this.cleanup();

  // Continue if active
  if (hasActive) {
    this.rafId = requestAnimationFrame(this.boundLoop);
  }
}
```

## Testing Strategy

### Unit Tests
- **Easing functions**: Boundary conditions (0, 1), monotonicity
- **Utils**: Color parsing, numeric parsing, interpolation
- **Animation**: State transitions, callbacks, progress calculation
- **Tween**: Value interpolation, completion
- **Queue**: Sequential execution, cancellation

### Integration Tests
- **Engine**: Multiple animations running simultaneously
- **Queue + Animation**: Chained animations with delays

## Known Limitations

1. **No DOM in Node.js**: Tests mock DOM APIs
2. **No CSS transform parsing**: Only simple numeric/color interpolation
3. **No GPU acceleration**: All calculations are JavaScript-based
4. **No timeline scrubbing**: Only forward playback
5. **No spring physics**: Elastic is approximate, not physics-based
