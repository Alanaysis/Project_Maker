# Learning Notes: Animation Engine

## What I Learned

### 1. Animation Fundamentals

**requestAnimationFrame (rAF)** is the browser's mechanism for smooth animations:
- Syncs with display refresh rate (typically 60fps)
- Provides high-resolution timestamps
- Automatically pauses when tab is hidden
- More efficient than `setTimeout`/`setInterval`

Key insight: The animation loop is a simple cycle:
```
requestAnimationFrame(callback) → calculate elapsed time → update state → render → repeat
```

### 2. Easing Functions

Easing functions transform linear progress into non-linear motion. The key properties:
- **f(0) = 0**: Animation starts at the beginning
- **f(1) = 1**: Animation ends at the destination
- **Monotonic for ease-in/out**: No backward motion (except elastic/back)

**Mathematical patterns**:
- **Polynomial**: `t^n` for ease-in, `1 - (1-t)^n` for ease-out
- **Trigonometric**: `1 - cos(t * PI/2)` for sine easing
- **Exponential**: `2^(10*(t-1))` for exponential easing
- **Elastic**: Combines exponential decay with sine oscillation
- **Bounce**: Piecewise quadratic functions simulating bouncing

### 3. Interpolation

Different value types require different interpolation strategies:
- **Numbers**: Simple linear interpolation `lerp(a, b, t)`
- **CSS units**: Parse value and unit, interpolate value, reassemble
- **Colors**: Parse to RGB channels, interpolate each channel
- **Transforms**: Parse matrix/decompose, interpolate components

### 4. State Machine Pattern

The Animation class uses a state machine:
```
IDLE → RUNNING → COMPLETED
         ↓
       PAUSED → RUNNING
         ↓
     CANCELLED
```

This pattern cleanly handles all animation lifecycle events and prevents invalid state transitions.

### 5. Promise-based Queue

Using Promises for the animation queue enables clean sequential code:
```typescript
await queue.animate(config1);
await queue.wait(500);
await queue.animate(config2);
```

This is much cleaner than callback-based approaches and integrates well with async/await.

### 6. Performance Optimization

Key performance considerations:
1. **Single rAF loop**: One loop for all animations, not one per animation
2. **Transform/opacity**: These properties don't trigger layout recalculation
3. **Cleanup**: Remove completed animations to avoid iterating over dead objects
4. **Frame budget**: Each frame has ~16ms; keep work minimal

### 7. TypeScript API Design

Designing a type-safe animation API:
- Use discriminated unions for config types
- Generic types for tween values `Tween<T extends Record<string, number>>`
- Callback types with proper signatures
- Enum types for animation states and directions

## Challenges Overcome

### Challenge 1: Pause/Resume Timing
**Problem**: When pausing and resuming, elapsed time calculation was incorrect.
**Solution**: Track accumulated pause duration and subtract it from elapsed time:
```typescript
this.elapsed = timestamp - this.startTime - this.pauseDuration;
```

### Challenge 2: Direction Handling
**Problem**: Alternate direction needs to reverse on odd iterations.
**Solution**: Calculate effective direction per iteration:
```typescript
private getEffectiveDirection(direction, iteration) {
  switch (direction) {
    case 'alternate':
      return iteration % 2 === 0 ? 'normal' : 'reverse';
    // ...
  }
}
```

### Challenge 3: Color Interpolation
**Problem**: Colors can be in hex, rgb, or rgba format.
**Solution**: Parse all formats to a common RGB structure, interpolate, then output:
```typescript
function interpolateColor(start, end, t) {
  const s = parseColor(start); // → {r, g, b, a}
  const e = parseColor(end);
  return `rgb(${lerp(s.r, e.r, t)}, ...)`;
}
```

### Challenge 4: Testing Animations in Node.js
**Problem**: No DOM or requestAnimationFrame in Node.js.
**Solution**: Mock browser APIs and use timestamp-based updates:
```typescript
anim.start(1000);  // Provide explicit timestamp
anim.update(1500); // 500ms later
```

## Key Takeaways

1. **Animation is math**: Easing functions are pure math functions mapping [0,1] to [0,1]
2. **Timing is critical**: Small errors in timing accumulate and cause visual glitches
3. **State machines prevent bugs**: Explicit states make animation lifecycle predictable
4. **Promises simplify sequencing**: Async/await makes animation chains readable
5. **Performance matters**: Every microsecond counts when running at 60fps

## Further Reading

- [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)
- [CSS Triggers](https://csstriggers.com/) - Which CSS properties trigger layout/paint
- [Easings.net](https://easings.net/) - Visual easing function reference
- [GSAP Documentation](https://greensock.com/docs/) - Industry-standard animation library
