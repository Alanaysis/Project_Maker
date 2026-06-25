# Development: Animation Engine

## Setup

### Prerequisites
- Node.js >= 16
- npm or yarn

### Installation
```bash
cd projects/animation-engine
npm install
```

### Build
```bash
npm run build
```

### Test
```bash
npm test
npm run test:coverage
```

## Project Structure

```
animation-engine/
├── src/
│   ├── index.ts          # Public API exports
│   ├── types.ts           # TypeScript types and interfaces
│   ├── easing.ts          # 30+ easing functions
│   ├── utils.ts           # Utility functions (lerp, color parsing, etc.)
│   ├── animation.ts       # Keyframe animation class
│   ├── tween.ts           # Simple numeric tween class
│   ├── queue.ts           # Sequential animation queue
│   └── engine.ts          # Main engine with rAF loop
├── tests/
│   ├── easing.test.ts     # Easing function tests
│   ├── utils.test.ts      # Utility function tests
│   ├── animation.test.ts  # Animation class tests
│   ├── tween.test.ts      # Tween class tests
│   ├── queue.test.ts      # Queue tests
│   └── engine.test.ts     # Engine integration tests
├── examples/
│   ├── basic.html         # Basic animation demo
│   ├── easing-demo.html   # Easing visualizer
│   └── queue-demo.html    # Queue demo
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── package.json
├── tsconfig.json
├── jest.config.js
├── README.md
└── LEARNING_NOTES.md
```

## API Reference

### AnimationEngine

```typescript
const engine = new AnimationEngine();

// Create keyframe animation
const anim = engine.animate({
  target: '#box',
  keyframes: [
    { offset: 0, styles: { opacity: 1 } },
    { offset: 1, styles: { opacity: 0 } },
  ],
  duration: 1000,
  easing: 'ease-out-cubic',
});

// Create tween
const tween = engine.tween({
  from: { x: 0, y: 0 },
  to: { x: 100, y: 200 },
  duration: 500,
  onUpdate: (values) => console.log(values),
});

// Get named queue
const queue = engine.queue('sequence');

// Lifecycle
engine.start();
engine.pause();
engine.resume();
engine.stop();

// Metrics
const metrics = engine.getMetrics();
```

### AnimationQueue

```typescript
const queue = new AnimationQueue();

// Sequential animations
await queue.animate(config);
await queue.wait(500);
await queue.animate(config2);

// Control
queue.pause();
queue.resume();
queue.cancel();
```

### Easing Functions

```typescript
import { easeOutBounce, resolveEasing, registerEasing } from 'animation-engine';

// Direct use
const value = easeOutBounce(0.5);

// By name
const fn = resolveEasing('ease-out-bounce');

// Register custom
registerEasing('my-easing', (t) => t * t);
```

## Extending the Engine

### Custom Easing Functions

```typescript
import { registerEasing, EasingFunction } from 'animation-engine';

const mySpring: EasingFunction = (t) => {
  return 1 - Math.cos(t * Math.PI * 4.5) * Math.exp(-t * 6);
};

registerEasing('spring', mySpring);
```

### Custom Property Types

To support new property types, extend `interpolateStyle()` in `utils.ts`.

## Performance Tips

1. **Use transforms**: `transform` and `opacity` are GPU-accelerated
2. **Batch reads/writes**: Avoid layout thrashing
3. **Limit active animations**: Use queue for sequential animations
4. **Cleanup**: Call `engine.cleanup()` or let it auto-clean
5. **Avoid Infinity iterations**: Use callbacks to restart instead

## Common Issues

### Animations not running
- Ensure `engine.start()` is called
- Check that target element exists
- Verify keyframe offsets are 0-1

### Janky animations
- Use `transform` instead of `left`/`top`
- Reduce number of simultaneous animations
- Check for layout-triggering properties

### Memory leaks
- Cancel animations when done
- Remove event listeners
- Let engine cleanup completed animations

## Contributing

1. Add tests for new features
2. Maintain test coverage above 80%
3. Update documentation for API changes
4. Follow existing code style
