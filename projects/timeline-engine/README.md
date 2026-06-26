# Timeline Engine

A TypeScript timeline/animation engine with keyframe-based animation, easing functions, and timeline management.

## Features

- **Timeline Management**: Create, play, pause, stop, seek
- **Keyframe System**: Position, scale, rotation, opacity keyframes
- **Easing Functions**: Linear, ease-in, ease-out, ease-in-out (and many more)
- **Animation Clips**: Reusable animation definitions
- **Timeline Player**: Interpolation and state computation
- **Property Interpolation**: Automatic interpolation of numeric and color values

## Building

```bash
pnpm install
pnpm build
```

## Running Tests

```bash
pnpm test
```

## Quick Start

```typescript
import { Timeline, Keyframe, Easing } from '@timeline-engine/core';

const timeline = new Timeline();

// Add keyframe animation
timeline.addKeyframe({
  property: 'x',
  keyframes: [
    { time: 0, value: 0 },
    { time: 1, value: 100 },
  ],
  duration: 1000,
  easing: Easing.easeOutCubic,
});

// Play
timeline.play();

// Seek
timeline.seek(0.5); // 50% progress

// Get current state
const state = timeline.getState();
console.log(state.x); // ~50
```

## Project Structure

```
timeline-engine/
├── src/
│   ├── index.ts             # Public API exports
│   ├── types.ts             # Type definitions
│   ├── easing.ts            # Easing functions
│   ├── keyframe.ts          # Keyframe system
│   ├── timeline.ts          # Timeline management
│   ├── timeline_player.ts   # Interpolation & state
│   └── animation_clip.ts    # Animation clips
├── tests/
│   ├── test_easing.ts       # Easing function tests
│   ├── test_keyframe.ts     # Keyframe tests
│   ├── test_timeline.ts     # Timeline tests
│   └── test_timeline_player.ts # Player tests
├── examples/
│   ├── basic.ts             # Basic usage
│   ├── easing_demo.ts       # Easing functions
│   └── timeline_demo.ts     # Timeline demo
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-API.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── package.json
├── tsconfig.json
├── README.md
└── LEARNING_NOTES.md
```

## Dependencies

- TypeScript 5.0+
- Node.js 18+
- pnpm (recommended) or npm

## License

MIT
