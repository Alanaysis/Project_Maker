# Learning Notes: Timeline Engine

## Key Concepts Learned

### 1. Timeline vs Animation
- **Timeline**: Container for multiple animations with global time
- **Animation**: Single property animation with keyframes
- **Keyframe**: Value at a specific time point
- **Clip**: Reusable animation definition

### 2. Easing Functions
- Map time progress (0-1) to eased progress (0-1)
- Categories: Linear, Quad, Cubic, Quart, Quint, Sine, Expo, Circ, Elastic, Back, Bounce
- Each category has ease-in, ease-out, and ease-in-out variants
- Ease-in: Slow start, fast end
- Ease-out: Fast start, slow end
- Ease-in-out: Slow start, fast middle, slow end

### 3. Interpolation
- **Linear**: `start + (end - start) * t`
- **Color**: RGB channel interpolation
- **Numeric**: Parse units, interpolate values, preserve units
- **Keyframe lookup**: Find surrounding keyframes, calculate local progress

### 4. Timeline State Machine
- **Idle**: Not playing, at start
- **Playing**: Actively animating
- **Paused**: Paused at current time
- **Completed**: Animation finished
- **Stopped**: Stopped and reset

### 5. Timeline Player
- Computes current time from playback state
- For each animation, finds relevant keyframes
- Interpolates values at current time
- Returns computed state object

## Design Decisions

1. **Time-based**: Use absolute time rather than frame-based for precision
2. **Easing as function**: Flexible, allows custom easings
3. **Keyframe offset**: Use 0-1 offset for relative timing within animation
4. **State object**: Return plain object for easy consumption
5. **Immutability**: Don't modify keyframe data during playback

## Challenges

1. **Frame rate independence**: Need consistent behavior across refresh rates
2. **Easing edge cases**: Functions must map 0->0 and 1->1 exactly
3. **Color interpolation**: Handle hex, rgb, rgba formats
4. **Unit preservation**: CSS units must be preserved during interpolation

## Future Improvements

1. Splines for smooth keyframe transitions
2. Spring physics animations
3. Timeline nesting/chaining
4. Reverse playback
5. Time scaling (slow motion, fast forward)
6. Keyframe easing per-keyframe
7. Web Animation API integration
