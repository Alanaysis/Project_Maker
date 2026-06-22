# CARLA RL - Autonomous Driving Reinforcement Learning

A Gymnasium-compatible reinforcement learning environment for autonomous driving using the CARLA simulator.

## Features

- **Gymnasium Interface:** Standard RL environment interface
- **Mock Environment:** Development without CARLA installation
- **CARLA Integration:** Full CARLA simulator support
- **PPO Training:** Stable-Baselines3 PPO implementation
- **Configurable Rewards:** Multiple reward components
- **Observation Processing:** Feature extraction and normalization

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/carla-rl

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

### Training with Mock Environment

```bash
# Train with mock environment (no CARLA needed)
python scripts/train.py --mock

# Train with custom timesteps
python scripts/train.py --mock --timesteps 100000

# Train with custom config
python scripts/train.py --config configs/mock.yaml
```

### Training with CARLA

```bash
# Start CARLA simulator
./CarlaUE4.sh

# Train with CARLA
python scripts/train.py --host localhost --port 2000
```

### Evaluation

```bash
# Evaluate trained model
python scripts/evaluate.py --model models/ppo_mock_20240101_120000 --mock
```

## Project Structure

```
carla-rl/
├── configs/            # Configuration files
├── docs/               # Documentation
├── notebooks/          # Jupyter notebooks
├── scripts/            # Training scripts
├── src/                # Source code
│   ├── carla_rl/
│   │   ├── agents/     # RL agents
│   │   ├── envs/       # Gymnasium environments
│   │   └── utils/      # Utility functions
│   └── tests/          # Unit tests
├── README.md
├── LEARNING_NOTES.md
├── setup.py
└── requirements.txt
```

## Usage

### Basic Training

```python
from carla_rl.envs.mock_carla_env import MockCarlaRLEnv
from carla_rl.agents.ppo_agent import PPOTrainer

# Create environment
env = MockCarlaRLEnv(
    target_speed=30.0,
    max_steps=500,
    seed=42,
)

# Create trainer
trainer = PPOTrainer(
    env_class=MockCarlaRLEnv,
    env_kwargs={"target_speed": 30.0, "max_steps": 500},
    policy="MlpPolicy",
    learning_rate=3e-4,
    n_steps=512,
    batch_size=64,
    verbose=1,
)

# Train
trainer.train(total_timesteps=100000)

# Evaluate
results = trainer.evaluate(n_episodes=10)
print(f"Mean reward: {results['mean_reward']:.2f}")

# Save model
trainer.save("models/ppo_carla")
```

### Custom Environment

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CustomCarlaEnv(gym.Env):
    def __init__(self):
        super().__init__()
        
        # Define spaces
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32,
        )
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(16,),
            dtype=np.float32,
        )
    
    def reset(self, seed=None, options=None):
        # Reset logic
        obs = np.zeros(16, dtype=np.float32)
        info = {}
        return obs, info
    
    def step(self, action):
        # Step logic
        obs = np.zeros(16, dtype=np.float32)
        reward = 0.0
        terminated = False
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info
```

## Configuration

### Mock Environment Config

```yaml
env:
  target_speed: 30.0
  max_steps: 500
  road_width: 8.0

reward:
  progress: 1.0
  speed: 0.5
  lane: 0.3
  collision: -100.0

ppo:
  learning_rate: 0.0003
  n_steps: 512
  batch_size: 64
  gamma: 0.99
```

### CARLA Config

```yaml
env:
  host: "localhost"
  port: 2000
  town: "Town01"
  vehicle_model: "model3"
  target_speed: 30.0

reward:
  progress: 1.0
  speed: 0.5
  lane: 0.3
  collision: -100.0

ppo:
  learning_rate: 0.0003
  n_steps: 2048
  batch_size: 64
  gamma: 0.99
```

## Testing

```bash
# Run all tests
pytest src/tests/ -v

# Run with coverage
pytest src/tests/ --cov=carla_rl

# Run specific test
pytest src/tests/test_mock_env.py::TestMockCarlaRLEnv::test_reset -v
```

## Documentation

- [01-RESEARCH.md](docs/01-RESEARCH.md) - Research findings
- [02-DESIGN.md](docs/02-DESIGN.md) - Architecture design
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - Implementation details
- [04-TESTING.md](docs/04-TESTING.md) - Testing guide
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - Development guide
- [LEARNING_NOTES.md](LEARNING_NOTES.md) - Learning notes

## Requirements

- Python 3.8+
- PyTorch 2.0+
- Stable-Baselines3 2.1+
- Gymnasium 0.29+
- NumPy 1.24+

## License

MIT License

## Acknowledgments

- [CARLA Simulator](https://carla.org/)
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
- [Gymnasium](https://gymnasium.farama.org/)
