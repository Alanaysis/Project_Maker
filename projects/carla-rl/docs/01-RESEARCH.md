# 01 - Research Phase

## Research Objectives

Research the key components needed for CARLA RL integration:
1. CARLA simulator Python API
2. OpenAI Gymnasium environment interface
3. Stable-Baselines3 PPO implementation
4. Autonomous driving reward functions
5. State representation approaches

## Key Findings

### 1. CARLA Simulator Python API

**Connection Pattern:**
```python
import carla
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
world = client.get_world()
```

**Key Components:**
- `carla.World`: Central simulation handle for actors, weather, map
- `carla.VehicleControl`: Control interface (throttle, steer, brake)
- `carla.BlueprintLibrary`: Actor templates for spawning
- `carla.Map`: Waypoint querying for navigation

**Sensors Available:**
| Sensor | Output | Use Case |
|--------|--------|----------|
| RGB Camera | Image (BGRA) | Visual observations |
| LiDAR | Point cloud | 3D spatial awareness |
| IMU | Accelerometer, Gyroscope | Motion tracking |
| Collision | Collision events | Safety detection |
| Lane Invasion | Lane crossing | Lane keeping |

**Synchronous Mode:**
- Required for reproducible training
- `fixed_delta_seconds` controls simulation step
- `world.tick()` advances simulation

### 2. Gymnasium Interface

**Required Methods:**
- `__init__()`: Define action/observation spaces
- `reset()`: Return (observation, info)
- `step()`: Return (observation, reward, terminated, truncated, info)
- `close()`: Cleanup resources

**Space Types:**
- `Box`: Continuous values
- `Discrete`: Integer actions
- `Dict`: Multiple observation types

**Key Changes from Old Gym:**
- `step()` returns 5 values (added truncated)
- `reset()` accepts seed and options kwargs

### 3. Stable-Baselines3 PPO

**Policy Options:**
| Policy | Use Case |
|--------|----------|
| MlpPolicy | Low-dimensional features |
| CnnPolicy | Image observations |
| MultiInputPolicy | Dict observations |

**Key Hyperparameters:**
- `learning_rate`: 3e-4 (default)
- `n_steps`: 2048 (steps per update)
- `batch_size`: 64
- `n_epochs`: 10
- `gamma`: 0.99 (discount)
- `clip_range`: 0.2

**Best Practices:**
- Use `SubprocVecEnv` for parallel collection
- Normalize images to [0, 1] for CNN
- Use `check_env()` to validate compatibility

### 4. Reward Functions

**Common Components:**
| Component | Formula | Purpose |
|-----------|---------|---------|
| Progress | delta_distance | Forward movement |
| Speed | -(v - v_target)^2 | Target speed |
| Collision | -large_penalty | Safety |
| Lane | -offset^2 | Lane keeping |
| Time | -small_constant | Efficiency |

**Design Principles:**
- Collision penalties should be 10-100x larger
- Use quadratic penalties for smooth gradients
- Consider curriculum learning for difficulty scaling

### 5. State Representations

**Options:**
| Type | Input | Network | Pros | Cons |
|------|-------|---------|------|------|
| Camera | 84x84x3 RGB | CNN | Rich info | Expensive |
| LiDAR | Point cloud | CNN | 3D awareness | Sparse |
| Features | State vector | MLP | Fast, efficient | Manual engineering |
| Hybrid | Images + Features | Multi-input | Best of both | Complex |

**Recommendation:** Start with feature vectors for fast iteration, then add camera.

## Architecture Decision

Based on research, the architecture will be:

1. **Mock Environment** for development and testing
2. **CARLA Environment** for actual training
3. **Feature-based observations** initially (extendable to camera)
4. **Composite reward** with configurable weights
5. **PPO training** with SB3

## References

- [CARLA Python API](https://carla.readthedocs.io/en/latest/python_api/)
- [CARLA Sensors](https://carla.readthedocs.io/en/latest/ref_sensors/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
- [SB3 Custom Env Guide](https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html)
