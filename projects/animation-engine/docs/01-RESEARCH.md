# Research: CSS/JS Animation Engine

## Problem Analysis

Web animations are fundamental to modern user interfaces. Understanding how animation engines work internally is crucial for:
- Building performant UI frameworks
- Creating custom animation libraries
- Debugging animation-related performance issues

## Core Concepts

### 1. Animation Loop (requestAnimationFrame)

The browser provides `requestAnimationFrame` (rAF) as the primary mechanism for smooth animations:
- Syncs with the display refresh rate (typically 60fps = ~16.67ms per frame)
- Automatically pauses when the tab is not visible
- Provides a high-resolution timestamp
- More efficient than `setTimeout`/`setInterval` for visual updates

### 2. Easing Functions

Easing functions map linear progress (0-1) to non-linear curves:
- **Polynomial**: Quad, Cubic, Quart, Quint (t^n)
- **Trigonometric**: Sine (sin/cos based)
- **Exponential**: Power of 2 curves
- **Circular**: Quarter-circle curves
- **Elastic**: Spring-like overshoot
- **Back**: Slight overshoot then return
- **Bounce**: Simulates bouncing

All proper easing functions satisfy: f(0) = 0, f(1) = 1

### 3. Keyframe Animation

Keyframe animations define states at specific progress points:
- CSS `@keyframes` defines 0% to 100% states
- JavaScript keyframes use offset values (0 to 1)
- Interpolation happens between keyframes
- Properties can be numeric, color, or transform-based

### 4. Animation Timing

```
Timeline: |--delay--|--duration × iterations--|
                    |---iter1---|---iter2---|---iter3---|
Progress: 0         0.0        1.0        0.0        1.0
```

- **Delay**: Time before animation starts
- **Duration**: Length of one iteration
- **Iterations**: Number of times to repeat (or Infinity)
- **Direction**: Normal, Reverse, Alternate

## Existing Solutions

### CSS Transitions
- Simple property changes
- Limited control (no pause/resume)
- GPU-accelerated transforms

### CSS Animations
- Keyframe-based
- `animation-play-state` for pause/resume
- Limited programmatic control

### Web Animations API
- Browser-native JavaScript animation API
- `element.animate()` method
- Timeline control, pause, reverse
- Not fully supported in all browsers

### Libraries
- **GSAP**: Industry standard, very powerful
- **anime.js**: Lightweight, good API
- **Velocity.js**: jQuery animation replacement
- **Popmotion**: Functional animation library
- **Framer Motion**: React-specific

## Design Decisions

### Why Build Custom?
1. **Learning**: Understanding internals of animation engines
2. **Control**: Full control over timing and easing
3. **Size**: Minimal footprint for specific needs
4. **TypeScript**: Type-safe animation definitions

### Architecture Goals
1. **Modular**: Separate easing, animation, queue, engine
2. **Type-safe**: Full TypeScript support
3. **Performant**: Minimal overhead per frame
4. **Extensible**: Custom easing functions, plugins

## References

- [MDN: requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame)
- [MDN: Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)
- [Easing Functions Cheat Sheet](https://easings.net/)
- [CSS Triggers](https://csstriggers.com/) - Performance impact of CSS properties
