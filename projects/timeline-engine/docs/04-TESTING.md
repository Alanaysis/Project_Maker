# Testing Strategy: Timeline Engine

## Test Framework
Jest for TypeScript unit testing.

## Test Categories

### 1. Easing Function Tests
- All easing functions map 0->0 and 1->1
- Monotonicity: values increase monotonically
- Specific value tests at t=0.5
- Edge cases: t<0, t>1

### 2. Keyframe Tests
- Keyframe creation and accessors
- Keyframe sorting by time
- Keyframe bounds lookup
- Interpolation between keyframes
- Single keyframe handling
- Multiple keyframe interpolation

### 3. Timeline Tests
- Timeline creation and state
- Play/pause/stop lifecycle
- Seek functionality
- Keyframe animation registration
- Animation clip management
- Progress calculation
- Event emission
- Loop mode
- Delay handling

### 4. Timeline Player Tests
- State computation at various times
- Interpolation accuracy
- Easing application
- Multiple property computation
- Edge cases (before start, after end)

## Test Coverage Goals
- All easing functions tested
- All timeline states tested
- Interpolation accuracy to 4 decimal places
- Edge cases (zero duration, single keyframe, etc.)

## Running Tests
```bash
pnpm test
```
