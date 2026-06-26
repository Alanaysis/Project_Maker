# Design Document: Timeline Engine

## Architecture

### Core Components

1. **Easing**: Easing function library and registry
2. **Keyframe**: Keyframe definition and lookup
3. **AnimationClip**: Reusable animation definition
4. **Timeline**: Container for animations with global time
5. **TimelinePlayer**: Computes state from timeline at current time

### Data Flow

```
Timeline
  ├── animations: Map<name, KeyframeAnimation>
  ├── currentTime: number
  ├── state: Map<property, number>
  ├── play()
  ├── pause()
  ├── stop()
  ├── seek(time)
  └── getState() -> TimelinePlayer.compute()

TimelinePlayer
  ├── compute(currentTime)
  │   ├── For each animation:
  │   │   ├── Get progress = (currentTime - startTime) / duration
  │   │   ├── Apply easing
  │   │   ├── Find keyframe bounds
  │   │   └── Interpolate value
  │   └── Return state object
```

### Design Patterns

- **Observer**: Timeline notifies listeners on state change
- **Strategy**: Easing as pluggable strategy
- **Factory**: Timeline creates animations
- **Builder**: Build keyframes and clips programmatically

## API Design

### Timeline
```typescript
const timeline = new Timeline();
timeline.play();
timeline.pause();
timeline.stop();
timeline.seek(0.5); // 50% progress
timeline.getState(); // Current computed state
```

### Keyframe Animation
```typescript
timeline.addKeyframe({
  property: 'x',
  keyframes: [
    { time: 0, value: 0 },
    { time: 1, value: 100 },
  ],
  duration: 1000,
  easing: Easing.easeOutCubic,
});
```

### Animation Clip
```typescript
const clip = new AnimationClip('slide-in', [
  { property: 'x', keyframes: [...] },
  { property: 'opacity', keyframes: [...] },
]);

timeline.addClip(clip);
```

## Performance Considerations

- Compute state only when needed (lazy evaluation)
- Cache interpolated values for same time range
- Use requestAnimationFrame for smooth playback
- Minimize object allocation during frame updates

## Future Extensions

- Splines (Catmull-Rom, Bezier) for smooth interpolation
- Spring physics animations
- Timeline nesting
- Reverse playback
- Time scaling
- Keyframe easing per-keyframe
- Web Animation API integration
