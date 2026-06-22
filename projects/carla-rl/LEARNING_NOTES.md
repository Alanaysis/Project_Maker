# Learning Notes - CARLA RL Project

## What I Learned

### 1. Reinforcement Learning Fundamentals

**Key Concepts:**
- **Agent-Environment Loop:** Agent observes state, takes action, receives reward
- **Policy:** Mapping from states to actions
- **Value Function:** Expected cumulative reward
- **Exploration vs Exploitation:** Balance between trying new actions and using known good actions

**PPO Algorithm:**
- Proximal Policy Optimization
- Clipped surrogate objective prevents large policy updates
- Uses Generalized Advantage Estimation (GAE)
- Stable and efficient for continuous control

### 2. Gymnasium Interface

**Standard RL Interface:**
```python
obs, info = env.reset()
while True:
    action = agent.predict(obs)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
```

**Key Design Patterns:**
- `observation_space` defines valid observations
- `action_space` defines valid actions
- `step()` returns 5 values (new API)
- `terminated` vs `truncated` distinction

### 3. CARLA Simulator

**Architecture:**
- Client-server model
- Python API connects to CARLA server
- Synchronous mode for reproducibility
- Sensor callbacks for async data

**Key Components:**
- World: Simulation environment
- Actors: Vehicles, pedestrians, sensors
- Blueprints: Templates for spawning actors
- Waypoints: Road network navigation

**Vehicle Control:**
- Throttle/brake: [0, 1] / [0, 1]
- Steering: [-1, 1]
- Applied via `VehicleControl` object

### 4. Reward Engineering

**Design Principles:**
- Balance multiple objectives
- Use quadratic penalties for smooth gradients
- Large penalties for unsafe behavior
- Normalize rewards for stable training

**Components Used:**
| Component | Purpose | Weight |
|-----------|---------|--------|
| Progress | Forward movement | 1.0 |
| Speed | Target speed | 0.5 |
| Lane | Stay centered | 0.3 |
| Heading | Correct direction | 0.2 |
| Collision | Safety | -100 |
| Time | Efficiency | -0.01 |

**Potential-Based Shaping:**
- Preserves optimal policy
- Provides denser reward signal
- Improves convergence

### 5. State Representation

**Feature Vector Approach:**
- 6 basic features (speed, steering, etc.)
- 10 waypoint features (5 waypoints x 2 coordinates)
- Total: 16 features
- Normalized for stable training

**Why Features Over Images:**
- Faster training
- Lower compute requirements
- Easier to debug
- Good for initial development

### 6. Environment Design

**Mock Environment:**
- Simulates CARLA behavior
- Simple 2D physics
- No external dependencies
- Fast iteration

**Real Environment:**
- Connects to CARLA server
- Full 3D simulation
- Sensor data processing
- More realistic

### 7. Stable-Baselines3

**Key Features:**
- Clean API for RL algorithms
- Vectorized environments
- Callbacks for monitoring
- TensorBoard integration

**PPO Usage:**
```python
from stable_baselines3 import PPO

model = PPO("MlpPolicy", env, learning_rate=3e-4)
model.learn(total_timesteps=1_000_000)
```

## Challenges Faced

### 1. CARLA Installation

**Challenge:** CARLA requires specific system dependencies and GPU support.

**Solution:** Created mock environment for development without CARLA.

### 2. Reward Balancing

**Challenge:** Balancing multiple reward components is difficult.

**Solution:** Configurable weights with sensible defaults, potential-based shaping.

### 3. Training Stability

**Challenge:** RL training can be unstable and hard to debug.

**Solution:** Proper normalization, clipping, and monitoring with TensorBoard.

### 4. Environment Compatibility

**Challenge:** Ensuring compatibility with Gymnasium and SB3.

**Solution:** Used `check_env()` for validation, followed API specifications.

## Best Practices Learned

### 1. Start Simple

- Begin with feature vectors, not images
- Use mock environment first
- Short episodes for debugging
- Simple reward functions

### 2. Iterative Development

- Test each component independently
- Add complexity gradually
- Monitor training metrics
- Adjust hyperparameters

### 3. Code Organization

- Separate concerns (env, agent, utils)
- Use configuration files
- Write comprehensive tests
- Document as you go

### 4. Training Tips

- Normalize observations
- Use appropriate learning rate
- Monitor with TensorBoard
- Save checkpoints regularly

## Future Improvements

### 1. Camera Observations

- Add CNN policy support
- Implement frame stacking
- Use pre-trained features

### 2. Advanced Algorithms

- SAC for continuous control
- TD3 for better sample efficiency
- HER for goal-conditioned tasks

### 3. Curriculum Learning

- Start with simple scenarios
- Gradually increase difficulty
- Better convergence

### 4. Multi-Agent

- Multiple vehicles
- Cooperative/competitive scenarios
- Traffic simulation

## Resources

### Papers
- PPO: https://arxiv.org/abs/1707.06347
- SAC: https://arxiv.org/abs/1801.01290
- GAE: https://arxiv.org/abs/1506.02438

### Documentation
- CARLA: https://carla.readthedocs.io/
- Gymnasium: https://gymnasium.farama.org/
- SB3: https://stable-baselines3.readthedocs.io/

### Tutorials
- CARLA Examples: https://github.com/carla-simulator/carla/tree/master/PythonAPI/examples
- SB3 Tutorials: https://github.com/araffin/rl-tutorial-jnrr19
