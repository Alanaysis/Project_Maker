# Development Guide: Timeline Engine

## Prerequisites
- Node.js 18+
- pnpm 8+ (or npm)

## Building

### With pnpm
```bash
pnpm install
pnpm build
```

### With npm
```bash
npm install
npm run build
```

## Running Tests

```bash
pnpm test
```

## Project Structure

```
timeline-engine/
├── src/                    # TypeScript source
│   ├── index.ts            # Public API
│   ├── types.ts            # Type definitions
│   ├── easing.ts           # Easing functions
│   ├── keyframe.ts         # Keyframe class
│   ├── timeline.ts         # Timeline class
│   ├── timeline_player.ts  # State computation
│   └── animation_clip.ts   # Animation clips
├── tests/                  # Unit tests
│   ├── test_easing.ts
│   ├── test_keyframe.ts
│   ├── test_timeline.ts
│   └── test_timeline_player.ts
├── examples/               # Demo programs
├── docs/                   # Documentation
├── package.json
├── tsconfig.json
├── README.md
└── LEARNING_NOTES.md
```

## Adding New Features

### 1. Add new TypeScript file in src/
```typescript
// new_feature.ts
export class NewFeature {
  // Implementation
}
```

### 2. Export from index.ts
```typescript
export { NewFeature } from './new_feature';
```

### 3. Add tests in tests/
```typescript
// test_new_feature.ts
import { describe, it, expect } from '@jest/globals';
import { NewFeature } from '../src/new_feature';

describe('NewFeature', () => {
  it('should work', () => {
    expect(true).toBe(true);
  });
});
```

### 4. Add example in examples/

## Coding Conventions

- **Types**: Strict TypeScript with no any
- **Naming**: camelCase for variables/functions, PascalCase for types/classes
- **Files**: Single responsibility, one class per file
- **Exports**: Explicit exports, barrel exports in index.ts
- **Comments**: JSDoc for public API

## Debugging Tips

1. Print timeline state at each frame
2. Verify easing function boundaries (0->0, 1->1)
3. Check keyframe ordering
4. Monitor progress calculation
5. Verify interpolation accuracy

## Common Issues

### Easing functions not mapping 0->0, 1->1
- Check edge case handling
- Verify function composition

### Interpolation inaccurate
- Check keyframe bounds lookup
- Verify local progress calculation

### Timeline not updating
- Check play state
- Verify seek target is within range
