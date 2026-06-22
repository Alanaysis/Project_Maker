# 05 - Development Guide

## Development Setup

### Prerequisites

- Python 3.8+
- pip or conda
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/carla-rl

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### CARLA Installation (Optional)

For actual CARLA training:

1. Download CARLA simulator from https://carla.org/
2. Extract and run `CarlaUE4.sh`
3. Add CARLA Python API to path:
   ```bash
   export PYTHONPATH=$PYTHONPATH:/path/to/carla/PythonAPI/carla/dist/carla-<version>-py3.x-linux-x86_64.egg
   ```

## Project Structure

```
carla-rl/
├── configs/            # Configuration files
│   ├── default.yaml    # CARLA configuration
│   └── mock.yaml       # Mock env configuration
├── docs/               # Documentation
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── notebooks/          # Jupyter notebooks
├── scripts/            # Training scripts
│   ├── train.py
│   └── evaluate.py
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

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ...

# Run tests
pytest src/tests/ -v

# Commit
git add .
git commit -m "Add new feature"
```

### 2. Testing

```bash
# Run all tests
pytest src/tests/

# Run specific test file
pytest src/tests/test_mock_env.py -v

# Run with coverage
pytest src/tests/ --cov=carla_rl
```

### 3. Training

```bash
# Train with mock environment
python scripts/train.py --mock

# Train with CARLA
python scripts/train.py --host localhost --port 2000

# Train with custom config
python scripts/train.py --config configs/mock.yaml

# Custom training
python scripts/train.py --mock --timesteps 100000 --seed 42
```

### 4. Evaluation

```bash
# Evaluate trained model
python scripts/evaluate.py --model models/ppo_mock_20240101_120000 --mock
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Maximum line length: 100 characters

### Formatting

```bash
# Format with black
black src/ scripts/

# Check with flake8
flake8 src/ scripts/
```

### Type Checking

```bash
# Run mypy
mypy src/
```

## Adding New Features

### New Environment

1. Create new environment class:
   ```python
   class NewEnv(gym.Env):
       def __init__(self):
           # Define spaces
           pass
       
       def reset(self):
           # Reset logic
           pass
       
       def step(self, action):
           # Step logic
           pass
   ```

2. Add to `envs/__init__.py`
3. Write tests
4. Update documentation

### New Reward Component

1. Add to `RewardCalculator`:
   ```python
   def _new_reward(self, state):
       return -penalty
   ```

2. Add weight to default weights
3. Update configuration
4. Write tests

### New Agent

1. Create new agent class:
   ```python
   class NewAgent:
       def __init__(self, env):
           # Initialize agent
           pass
       
       def train(self, timesteps):
           # Training logic
           pass
       
       def predict(self, obs):
           # Prediction logic
           pass
   ```

2. Add to `agents/__init__.py`
3. Write tests
4. Create training script

## Debugging

### Common Issues

**CARLA Connection Failed:**
```bash
# Check CARLA is running
ps aux | grep Carla

# Check port
netstat -tuln | grep 2000
```

**Import Errors:**
```bash
# Ensure package is installed
pip install -e .

# Check Python path
echo $PYTHONPATH
```

**Training Not Converging:**
- Check reward function
- Adjust hyperparameters
- Increase training time
- Use reward shaping

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use mock environment
env = MockCarlaRLEnv(seed=42)

# Short training
model.learn(total_timesteps=1000)
```

## Performance Optimization

### Training Speed

1. **Use SubprocVecEnv:**
   ```python
   from stable_baselines3.common.vec_env import SubprocVecEnv
   env = SubprocVecEnv([make_env for _ in range(4)])
   ```

2. **Increase batch size:**
   ```python
   model = PPO(..., batch_size=256)
   ```

3. **Use GPU:**
   ```python
   model = PPO(..., device="cuda")
   ```

### Memory Usage

1. **Reduce image size:**
   ```python
   env = MockCarlaRLEnv(image_size=(64, 64))
   ```

2. **Disable camera:**
   ```python
   env = MockCarlaRLEnv(use_camera=False)
   ```

3. **Shorter episodes:**
   ```python
   env = MockCarlaRLEnv(max_steps=500)
   ```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Run test suite
6. Submit pull request

## Resources

- [CARLA Documentation](https://carla.readthedocs.io/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [PPO Paper](https://arxiv.org/abs/1707.06347)
