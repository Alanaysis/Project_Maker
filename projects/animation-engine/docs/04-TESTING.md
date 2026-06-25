# Testing: Animation Engine

## Test Strategy

The animation engine uses a comprehensive testing approach covering unit tests, integration tests, and manual browser testing.

## Test Categories

### 1. Easing Function Tests (`easing.test.ts`)

**Boundary Conditions**: All easing functions must satisfy f(0) = 0 and f(1) = 1.
```typescript
test.each(allEasings)('$name(0) = 0', ({ fn }) => {
  expect(fn(0)).toBeCloseTo(0, 10);
});
```

**Monotonicity**: Ease-in functions should be monotonically increasing.
```typescript
test('easeInQuad is monotonically increasing', () => {
  for (let t = 0.01; t <= 1; t += 0.01) {
    expect(easeInQuad(t)).toBeGreaterThan(easeInQuad(t - 0.01));
  }
});
```

**Specific Values**: Known values for common easing functions.
```typescript
test('easeInQuad at midpoint', () => {
  expect(easeInQuad(0.5)).toBe(0.25);
});
```

**Registry**: Named easing resolution and custom registration.

### 2. Utility Tests (`utils.test.ts`)

- `lerp`: Start/end values, midpoint, negative ranges
- `clamp`: Below min, above max, within range
- `parseNumericValue`: Numbers, px, %, em, negative
- `parseColor`: 3/6/8-digit hex, rgb(), rgba()
- `interpolateColor`: Color blending
- `interpolateStyle`: Auto-detection of value types
- `generateId`: Uniqueness

### 3. Animation Tests (`animation.test.ts`)

**State Transitions**:
- IDLE → RUNNING (start)
- RUNNING → PAUSED (pause)
- PAUSED → RUNNING (resume)
- RUNNING → CANCELLED (cancel)
- RUNNING → COMPLETED (end)

**Callbacks**: onStart, onUpdate, onComplete, onCancel

**Animation Logic**:
- Progress calculation
- Direction (normal, reverse, alternate)
- Iterations
- Delay handling

### 4. Tween Tests (`tween.test.ts`)

- Value interpolation at various progress points
- Multiple property interpolation
- Easing function application
- Delay handling
- Completion detection

### 5. Queue Tests (`queue.test.ts`)

- Sequential execution order
- Delay (wait) support
- Cancel clears pending tasks
- Clear rejects pending promises

### 6. Engine Tests (`engine.test.ts`)

- Animation and tween creation
- Named queue management
- Start/pause/resume/stop lifecycle
- Performance metrics
- Cleanup of completed animations

## Running Tests

```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Mocking Strategy

Since the engine runs in browsers, tests mock DOM APIs:

```typescript
// Mock HTMLElement
(global as any).document = {
  querySelector: jest.fn().mockReturnValue({
    style: {},
  }),
};

// Mock requestAnimationFrame
(global as any).requestAnimationFrame = (callback) => {
  return setTimeout(() => callback(performance.now()), 16);
};
```

## Manual Testing

Browser examples in `examples/` directory:
- `basic.html`: Basic keyframe animations
- `easing-demo.html`: Visual easing function comparison
- `queue-demo.html`: Sequential animation queue

## Coverage Goals

| Module | Target | Focus |
|--------|--------|-------|
| easing.ts | 100% | All functions tested |
| utils.ts | 95% | Color/numeric parsing |
| animation.ts | 90% | State machine paths |
| tween.ts | 90% | Interpolation logic |
| queue.ts | 85% | Async execution |
| engine.ts | 80% | Integration |
