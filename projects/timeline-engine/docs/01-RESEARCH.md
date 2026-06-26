# Research Notes: Timeline and Animation Engines

## Overview
This research explores timeline-based animation systems used in web, game, and multimedia applications.

## Key Topics

### 1. Timeline Architecture
- **Global clock**: Single time source for all animations
- **Animation tracks**: Per-property animation streams
- **Keyframes**: Discrete values at specific times
- **Interpolation**: Continuous values between keyframes
- **Playback controls**: Play, pause, stop, seek, speed

### 2. Keyframe Systems
- **Time-based**: Absolute time (seconds, milliseconds)
- **Offset-based**: Relative progress (0-1)
- **Easing**: Per-keyframe or per-animation easing
- **Property types**: Position, scale, rotation, opacity, color

### 3. Easing Functions
- **Linear**: No easing, constant speed
- **Polynomial**: t^2, t^3, t^4, t^5 curves
- **Trigonometric**: sin, cos curves
- **Exponential**: 2^t curves
- **Circular**: sqrt(1-t^2) curves
- **Elastic**: Spring-like oscillation
- **Back**: Overshoot and return
- **Bounce**: Bounce at target

### 4. Animation Clips
- **Reusable**: Define once, play multiple times
- **Named properties**: Reference by property name
- **Looping**: Repeat animations
- **Offset**: Start at different times within clip

### 5. Timeline Player
- **Frame loop**: requestAnimationFrame or setInterval
- **State computation**: Evaluate all animations at current time
- **Batching**: Compute all states in one pass
- **Cleanup**: Remove completed animations
- **Performance**: FPS monitoring, frame budget

## References
- Web Animations API (W3C)
- CSS Transitions and Animations
- Adobe After Effects keyframe system
- Unity Animation Timeline
- GSAP (GreenSock Animation Platform)
