# 03 - Implementation Details

## Implementation Overview

This document describes the implementation details of the CARLA RL system.

## Core Components

### 1. MockCarlaRLEnv

**Purpose:** Development environment without CARLA dependency.

**Key Features:**
- Simple 2D vehicle physics (bicycle model)
- Procedural road generation with obstacles
- Same Gymnasium interface as real CARLA env
- Configurable reward weights

**Physics Model:**
```python
# Bicycle model
turning_radius = wheelbase / tan(steer)
angular_velocity = speed / turning_radius
heading += angular_velocity * dt

# Position update
x += speed * sin(heading) * dt
y += speed * cos(heading) * dt
```

**Obstacle Generation:**
- Random obstacles appear with 1% probability per step
- Obstacles are removed when passed
- Collision detection uses Euclidean distance

### 2. CarlaRLEnv

**Purpose:** Real CARLA simulator integration.

**Key Features:**
- CARLA client connection with timeout
- Synchronous mode for reproducibility
- Vehicle spawning at random locations
- Sensor callbacks (collision, lane invasion, camera)
- Waypoint-based navigation features

**Connection Setup:**
```python
client = carla.Client(host, port)
client.set_timeout(30.0)
world = client.load_world(town)

# Enable synchronous mode
settings = world.get_settings()
settings.synchronous_mode = True
settings.fixed_delta_seconds = 0.05  # 20 FPS
world.apply_settings(settings)
```

**Sensor Callbacks:**
```python
# Collision detection
collision_sensor.listen(lambda event: self._on_collision(event))

# Lane invasion detection
lane_sensor.listen(lambda event: self._on_lane_invasion(event))

# Camera (optional)
camera.listen(lambda image: self._on_camera(image))
```

**Waypoint Extraction:**
```python
# Get next 5 waypoints
waypoint = map.get_waypoint(vehicle_location)
for i in range(5):
    next_wps = waypoint.next(2.0)
    # Transform to vehicle-relative coordinates
    # Add to observation
```

### 3. ObservationProcessor

**Feature Vector:**
- 6 basic features (speed, steer, throttle, brake, dist_to_center, heading_error)
- 10 waypoint features (5 waypoints x 2 coordinates)
- Total: 16 features

**Normalization:**
```python
normalized = (value - mean) / std
```

**Image Processing:**
- Resize to target size (default 84x84)
- Optional grayscale conversion
- Optional frame stacking (4 frames)

### 4. RewardCalculator

**Reward Components:**

| Component | Weight | Formula |
|-----------|--------|---------|
| Progress | 1.0 | Forward distance |
| Speed | 0.5 | -(v - v_target)^2 / v_target^2 |
| Lane | 0.3 | -(dist / max_dist)^2 |
| Heading | 0.2 | -|error| / pi |
| Collision | -100 | Binary penalty |
| Time | -0.01 | Per-step penalty |
| Comfort | 0.1 | -jerk / 100 |

**Shaped Reward:**
- Potential-based shaping preserves optimal policy
- Potential function combines speed, lane, and heading
- Shaping = gamma * potential(next) - potential(current)

### 5. PPOTrainer

**Environment Vectorization:**
```python
# Single environment
env = DummyVecEnv([make_env])

# Multiple environments
env = SubprocVecEnv([make_env for _ in range(n_envs)])
```

**Training Loop:**
```python
model = PPO("MlpPolicy", env, **kwargs)
model.learn(
    total_timesteps=1_000_000,
    callback=[eval_callback, checkpoint_callback],
)
```

**Callbacks:**
- `EvalCallback`: Periodic evaluation
- `CheckpointCallback`: Model saving

## Configuration System

**YAML Configuration:**
```yaml
env:
  host: "localhost"
  port: 2000
  town: "Town01"
  target_speed: 30.0

ppo:
  learning_rate: 0.0003
  n_steps: 2048
  batch_size: 64
```

**Loading:**
```python
with open("config.yaml") as f:
    config = yaml.safe_load(f)
```

## Testing Strategy

### Unit Tests

**test_mock_env.py:**
- Environment initialization
- Observation space validation
- Action space validation
- Reset functionality
- Step functionality
- Termination conditions
- Reward computation

**test_utils.py:**
- Feature processing
- Image processing
- Reward calculation
- Normalization

**test_agent.py:**
- Trainer initialization
- Training loop
- Prediction
- Save/load

### Integration Tests

**SB3 Compatibility:**
```python
from stable_baselines3.common.env_checker import check_env
check_env(env)  # Validates Gymnasium interface
```

**Training Integration:**
```python
model = PPO("MlpPolicy", env)
model.learn(total_timesteps=128)  # Short training run
```

## Error Handling

**CARLA Connection:**
```python
try:
    import carla
except ImportError:
    raise ImportError(
        "CARLA Python API not found. "
        "Use MockCarlaRLEnv for testing."
    )
```

**Timeout Handling:**
```python
client.set_timeout(30.0)  # 30 second timeout
```

**Actor Cleanup:**
```python
def _cleanup(self):
    if self.vehicle is not None:
        self.vehicle.destroy()
        self.vehicle = None
```

## Performance Considerations

1. **Synchronous Mode:** Required for reproducibility
2. **Sensor Tick Rate:** Match simulation step (0.05s = 20 FPS)
3. **Vectorized Environments:** Use SubprocVecEnv for parallel collection
4. **Image Preprocessing:** Resize before storing
5. **Feature Normalization:** Improves training stability

## Future Extensions

1. **Camera Observations:** Add CNN policy support
2. **Multi-Agent:** Multiple vehicles in simulation
3. **Curriculum Learning:** Progressive difficulty
4. **Domain Randomization:** Random weather, traffic
5. **Transfer Learning:** Pre-trained visual features
