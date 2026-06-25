# Animation Engine - Research

## Core Concepts

### 1. Animation Fundamentals

Animation is the illusion of movement created by displaying a sequence of images
(frames) in rapid succession. In software, we interpolate between states over time.

Key principles from Disney's 12 principles of animation:
- **Squash and Stretch**: Deform objects to convey weight and flexibility
- **Anticipation**: Prepare the audience for an action
- **Staging**: Direct attention to what's important
- **Straight Ahead / Pose to Pose**: Two approaches to creating animation
- **Follow Through / Overlapping**: Parts continue moving after the main action
- **Slow In / Slow Out**: Ease in and out of keyframes (easing functions)
- **Arcs**: Natural motion follows arced paths
- **Secondary Action**: Supporting actions that add richness
- **Timing**: The number of frames between key poses determines speed
- **Exaggeration**: Push movements beyond realism for clarity
- **Solid Drawing**: Consider form and volume in animation
- **Appeal**: Characters should be engaging and charismatic

### 2. Keyframe Animation

Keyframe animation defines states at specific points in time. The system
interpolates between these states for intermediate frames.

**Keyframe representation:**
```
time: 0.0  ->  { x: 0,   opacity: 1.0 }
time: 0.5  ->  { x: 100, opacity: 0.5 }
time: 1.0  ->  { x: 200, opacity: 1.0 }
```

**Interpolation methods:**
- Linear interpolation (lerp)
- Cubic Bezier interpolation
- Hermite spline interpolation
- Catmull-Rom spline interpolation

### 3. Easing Functions

Easing functions modify the rate of change during animation, creating
more natural-feeling motion.

**Categories:**
- **Linear**: Constant speed
- **Ease-in**: Start slow, accelerate
- **Ease-out**: Start fast, decelerate
- **Ease-in-out**: Slow at both ends, fast in middle

**Mathematical families:**
- Quadratic: t^2
- Cubic: t^3
- Quartic: t^4
- Quintic: t^5
- Sinusoidal: sin(t)
- Exponential: 2^t
- Circular: sqrt(1 - t^2)
- Elastic: Damped oscillation
- Back: Overshoot
- Bounce: Bouncing effect

### 4. Skeletal Animation

Skeletal animation uses a hierarchy of bones (skeleton) to deform a mesh.

**Components:**
- **Bone hierarchy**: Tree structure where each bone has a parent
- **Bind pose**: The rest position of the skeleton
- **Skin weights**: Per-vertex weights that determine bone influence
- **Animation clips**: Per-bone keyframe sequences

**Skinning formula:**
```
vertex_pos = sum(weight_i * bone_i_transform * inv_bind_i * rest_pos)
```

### 5. Particle Systems

Particle systems simulate effects like fire, smoke, rain, and explosions.

**Components:**
- **Emitter**: Creates particles at a rate
- **Particle**: Individual element with position, velocity, color, size, lifetime
- **Forces**: Gravity, wind, turbulence
- **Renderer**: How particles are displayed

**Emitter shapes:**
- Point: Emit from a single point
- Circle/Sphere: Emit within a volume
- Cone: Emit in a cone shape
- Box: Emit within a box

### 6. Animation Timing

**Frame-based vs Time-based:**
- Frame-based: Advance by fixed frame count (e.g., 60fps)
- Time-based: Advance by real elapsed time (more flexible)

**Delta time:**
```
dt = current_time - previous_time
position += velocity * dt
```

**Time scaling:**
```
scaled_dt = dt * time_scale
```

### 7. Animation Queue / Sequencing

Sequential animation execution:
1. Play animation A
2. Wait 500ms
3. Play animation B
4. Call callback

This enables complex multi-step animations without manual timing.

## References

- [Robert Penner's Easing Functions](http://robertpenner.com/easing/)
- [CSS Easing Functions Level 1](https://www.w3.org/TR/css-easing-1/)
- [Pixar's Animation Principles](https://www.pixar.com/our-culture)
- [Game Engine Architecture by Jason Gregory](http://www.gameenginebook.com/)
- [Real-Time Rendering by Akenine-Moller et al.](http://www.realtimerendering.com/)
