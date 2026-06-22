# 02 - Architecture Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CARLA RL System                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│  │   CARLA     │     │   Gymnasium │     │   PPO       │      │
│  │  Simulator  │◄───►│  Environment│◄───►│   Agent     │      │
│  └─────────────┘     └─────────────┘     └─────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│  │  Sensors    │     │ Observation │     │  Training   │      │
│  │  & Control  │     │  Processor  │     │   Loop      │      │
│  └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Module Architecture

### 1. Environment Module (`carla_rl.envs`)

```
envs/
├── __init__.py
├── carla_env.py        # CARLA Gymnasium environment
└── mock_carla_env.py   # Mock environment for testing
```

**CarlaRLEnv:**
- Wraps CARLA simulator
- Implements Gymnasium interface
- Handles vehicle spawning and control
- Manages sensors and callbacks
- Computes rewards

**MockCarlaRLEnv:**
- Simulates CARLA behavior
- Simple 2D physics
- For development without CARLA
- Same interface as CarlaRLEnv

### 2. Agent Module (`carla_rl.agents`)

```
agents/
├── __init__.py
└── ppo_agent.py        # PPO trainer wrapper
```

**PPOTrainer:**
- Wraps Stable-Baselines3 PPO
- Manages environment vectorization
- Handles training loop
- Provides save/load functionality
- Evaluation interface

### 3. Utility Module (`carla_rl.utils`)

```
utils/
├── __init__.py
├── observation.py      # Observation processing
└── reward.py           # Reward calculation
```

**ObservationProcessor:**
- Feature extraction and normalization
- Image preprocessing
- Frame stacking

**RewardCalculator:**
- Composite reward function
- Configurable weights
- Multiple reward components

## Data Flow

### Training Loop

```
1. Environment Reset
   └─► Spawn vehicle at random location
   └─► Initialize sensors
   └─► Return initial observation

2. Agent Decision
   └─► Process observation
   └─► Select action via policy

3. Environment Step
   └─► Apply vehicle control
   └─► Tick simulation
   └─► Collect sensor data
   └─► Compute reward
   └─► Check termination

4. Repeat until done
```

### Observation Format

```python
observation = {
    "features": np.array([
        speed,           # km/h (normalized)
        steer,           # [-1, 1]
        throttle,        # [0, 1]
        brake,           # [0, 1]
        dist_to_center,  # meters (normalized)
        heading_error,   # radians (normalized)
        waypoint_1_x,    # vehicle-relative (normalized)
        waypoint_1_y,
        ...
        waypoint_5_x,
        waypoint_5_y,
    ], dtype=np.float32),
    "image": np.array([...], dtype=np.uint8)  # Optional
}
```

### Action Format

```python
action = np.array([
    throttle_brake,  # [-1, 1]: positive=throttle, negative=brake
    steer,           # [-1, 1]: left=negative, right=positive
], dtype=np.float32)
```

### Reward Components

```python
reward = (
    w_progress * progress_reward +
    w_speed * speed_reward +
    w_lane * lane_keeping_reward +
    w_heading * heading_reward +
    w_collision * collision_penalty +
    w_time * time_penalty +
    w_comfort * comfort_penalty
)
```

## Class Diagram

```
┌─────────────────────┐
│    gym.Env          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   CarlaRLEnv        │────►│ ObservationProcessor │
├─────────────────────┤     ├─────────────────────┤
│ - client            │     │ - image_size        │
│ - world             │     │ - feature_dim       │
│ - vehicle           │     │ + process_features()│
│ - sensors           │     │ + process_image()   │
├─────────────────────┤     └─────────────────────┘
│ + reset()           │
│ + step()            │     ┌─────────────────────┐
│ + close()           │────►│ RewardCalculator    │
└─────────────────────┘     ├─────────────────────┤
                            │ - target_speed      │
┌─────────────────────┐     │ - weights           │
│    PPOTrainer       │     │ + compute()         │
├─────────────────────┤     └─────────────────────┘
│ - model (PPO)       │
│ - env               │
│ - eval_env          │
├─────────────────────┤
│ + train()           │
│ + evaluate()        │
│ + predict()         │
│ + save() / load()   │
└─────────────────────┘
```

## Configuration Design

```yaml
# Environment
env:
  host: "localhost"
  port: 2000
  town: "Town01"
  target_speed: 30.0
  max_steps: 1000

# Reward weights
reward:
  progress: 1.0
  speed: 0.5
  lane: 0.3
  collision: -100.0

# PPO hyperparameters
ppo:
  learning_rate: 0.0003
  n_steps: 2048
  batch_size: 64
  gamma: 0.99
```

## Extension Points

1. **New Sensors**: Add sensor callbacks in `CarlaRLEnv._setup_sensors()`
2. **New Rewards**: Extend `RewardCalculator.compute()`
3. **New Agents**: Create new agent class following `PPOTrainer` pattern
4. **New Environments**: Subclass `gym.Env` with same interface
