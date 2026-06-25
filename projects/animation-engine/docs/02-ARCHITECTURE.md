# Architecture: Animation Engine

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                   AnimationEngine                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │Animation │  │  Tween   │  │ AnimationQueue   │  │
│  │          │  │          │  │                  │  │
│  │Keyframes │  │ Numeric  │  │ Sequential exec  │  │
│  │Interpol. │  │ lerp     │  │ Promise-based    │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                 │             │
│       └──────────────┼─────────────────┘             │
│                      │                               │
│              ┌───────┴───────┐                       │
│              │ Easing Module │                       │
│              │ 30+ functions │                       │
│              └───────────────┘                       │
│                                                      │
│              ┌───────────────┐                       │
│              │  rAF Loop     │                       │
│              │  Batching     │                       │
│              │  Metrics      │                       │
│              └───────────────┘                       │
└─────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. Types (`types.ts`)
- All TypeScript interfaces and enums
- Configuration types for animations
- Callback signatures
- Performance metrics types

### 2. Easing Functions (`easing.ts`)
- 30+ easing functions organized by family
- Registry for named easing functions
- Custom easing registration
- Resolution function (name → function)

### 3. Utilities (`utils.ts`)
- `lerp()`: Linear interpolation
- `clamp()`: Value clamping
- `parseColor()`: Color string parsing
- `interpolateStyle()`: Smart style interpolation
- `applyStyles()`: DOM style application
- `requestAnimationFramePolyfill()`: rAF wrapper

### 4. Animation (`animation.ts`)
- Keyframe-based animation
- State machine (IDLE → RUNNING → COMPLETED)
- Direction support (normal, reverse, alternate)
- Fill modes
- Callback system

### 5. Tween (`tween.ts`)
- Simple numeric property interpolation
- More efficient than keyframe animations
- Direct value updates

### 6. Queue (`queue.ts`)
- Sequential animation execution
- Promise-based API
- Delay support
- Pause/resume control

### 7. Engine (`engine.ts`)
- Central manager for all animations
- Main rAF loop
- Performance metrics tracking
- Automatic cleanup of completed animations

## Animation Loop Flow

```
requestAnimationFrame
         │
         ▼
┌─────────────────┐
│  Calculate dt   │ ← timestamp - lastFrameTime
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Metrics  │ ← FPS, frame time
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ For each anim:  │
│  - Check state  │
│  - Calc progress│
│  - Apply easing │
│  - Interpolate  │
│  - Apply styles │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cleanup done    │
│ Request next    │
└─────────────────┘
```

## State Machine

```
         start()
IDLE ──────────► RUNNING
  ▲                 │
  │     reset()     │ pause()
  │    ┌────────────┤
  │    │            ▼
  │    │        PAUSED
  │    │            │
  │    │    start() │
  │    │            ▼
  │    │        RUNNING ────► COMPLETED
  │    │                         │
  │    └─────────────────────────┘
  │                    reset()
  └──────────────────────────────── CANCELLED
                       cancel()
```

## Key Design Patterns

### 1. Builder Pattern
Animations are configured through options objects:
```typescript
engine.animate({
  target: '#box',
  keyframes: [...],
  duration: 1000,
  easing: 'ease-out-cubic'
});
```

### 2. Promise-based Queue
Queue operations return promises for chaining:
```typescript
await queue.animate(config1);
await queue.wait(500);
await queue.animate(config2);
```

### 3. Registry Pattern
Easing functions are stored in a registry:
```typescript
registerEasing('custom', myEasingFn);
const fn = resolveEasing('custom');
```

## Performance Considerations

1. **Batch updates**: Process all animations in single rAF callback
2. **Avoid layout thrashing**: Read then write styles
3. **Use transforms**: `transform` and `opacity` are GPU-accelerated
4. **Cleanup**: Remove completed animations to avoid memory leaks
5. **Frame budget**: Keep per-frame work under 16ms
