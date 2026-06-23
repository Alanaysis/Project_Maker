# Actor-Critic 开发指南

## 1. 环境搭建

### 1.1 系统要求

- Python 3.8+
- PyTorch 2.0+
- Gymnasium 0.29+

### 1.2 安装依赖

```bash
cd projects/actor-critic
pip install -e .
```

### 1.3 开发依赖

```bash
pip install -e ".[dev]"
```

## 2. 代码规范

### 2.1 代码风格

- 遵循 PEP 8
- 使用类型注解
- 编写 docstring

### 2.2 命名规范

- 类名：PascalCase（如 `ActorNetwork`）
- 函数名：snake_case（如 `compute_advantages`）
- 常量：UPPER_CASE（如 `GAMMA`）

### 2.3 示例

```python
class ActorNetwork(nn.Module):
    """Actor network that outputs action probabilities.

    The actor network learns a policy π(a|s) that maps states to action
    probabilities.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
    ) -> None:
        """Initialize the actor network.

        Args:
            state_dim: Dimension of the state space.
            action_dim: Dimension of the action space.
            hidden_dim: Dimension of hidden layers.
        """
        super().__init__()
        # ...
```

## 3. 开发流程

### 3.1 添加新功能

1. 创建功能分支
2. 编写代码和测试
3. 运行测试确保通过
4. 提交代码
5. 创建 Pull Request

### 3.2 测试流程

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_actor_network.py -v

# 生成覆盖率报告
pytest tests/ --cov=actor_critic
```

### 3.3 代码检查

```bash
# 类型检查
mypy src/

# 代码风格检查
flake8 src/

# 代码格式化
black src/
```

## 4. 训练流程

### 4.1 基本训练

```bash
python scripts/train.py
```

### 4.2 自定义参数

```bash
python scripts/train.py \
    --episodes 1000 \
    --hidden-dim 256 \
    --actor-lr 1e-4 \
    --critic-lr 5e-4 \
    --gamma 0.995 \
    --entropy-coef 0.005
```

### 4.3 评估模型

```bash
python scripts/evaluate.py \
    --checkpoint checkpoints/actor_critic_cartpole.pt \
    --episodes 20
```

## 5. 调试技巧

### 5.1 监控训练

观察以下指标：
- **Actor Loss**：策略损失，应逐渐下降
- **Critic Loss**：价值损失，应逐渐下降
- **Entropy**：策略熵，应保持一定水平（不过低）
- **Average Score**：平均得分，应逐渐上升

### 5.2 常见问题

#### 训练不稳定

**症状**：得分波动大，不收敛

**解决方案**：
1. 降低学习率
2. 增加熵系数
3. 使用梯度裁剪
4. 使用 GAE（gae_lambda < 1.0）

#### 策略熵过低

**症状**：策略过早收敛，探索不足

**解决方案**：
1. 增加熵系数
2. 使用更小的学习率
3. 检查奖励函数

#### 价值估计不准

**症状**：Critic Loss 不下降

**解决方案**：
1. 增加 Critic 学习率
2. 使用更大的网络
3. 增加训练步数

## 6. 扩展方向

### 6.1 A2C 实现

使用多个并行环境：

```python
class A2CAgent:
    def __init__(self, num_envs=4, ...):
        self.envs = [gym.make("CartPole-v1") for _ in range(num_envs)]

    def collect_trajectories(self):
        # 并行收集数据
        pass
```

### 6.2 A3C 实现

使用多进程异步训练：

```python
import torch.multiprocessing as mp

def worker(global_model, ...):
    local_model = ActorCriticAgent(...)
    local_model.load_state_dict(global_model.state_dict())

    while True:
        # 本地训练
        local_model.update()

        # 同步到全局模型
        sync_gradients(local_model, global_model)
```

### 6.3 连续动作空间

使用高斯策略：

```python
class ContinuousActorNetwork(nn.Module):
    def forward(self, state):
        mean = self.mean_head(state)
        log_std = self.log_std_head(state)
        return mean, log_std

    def get_action(self, state):
        mean, log_std = self.forward(state)
        std = log_std.exp()
        dist = Normal(mean, std)
        action = dist.sample()
        return action, dist.log_prob(action)
```

## 7. 性能优化

### 7.1 GPU 加速

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
agent = ActorCriticAgent(..., device=device)
```

### 7.2 批量处理

```python
# 收集多个 episode 后批量更新
all_states = []
all_actions = []
all_rewards = []

for episode in range(batch_size):
    # 收集数据
    pass

# 批量更新
agent.update_batch(all_states, all_actions, all_rewards)
```

### 7.3 向量化环境

```python
import gymnasium as gym

# 使用向量化环境
envs = gym.vector.SyncVectorEnv([
    lambda: gym.make("CartPole-v1") for _ in range(4)
])
```

## 8. 部署

### 8.1 模型导出

```python
# 保存为 TorchScript
scripted_model = torch.jit.script(agent.actor)
scripted_model.save("actor_scripted.pt")
```

### 8.2 ONNX 导出

```python
torch.onnx.export(
    agent.actor,
    dummy_input,
    "actor.onnx",
    opset_version=11,
)
```

## 9. 参考资源

- [PyTorch 官方文档](https://pytorch.org/docs/stable/)
- [Gymnasium 文档](https://gymnasium.fauxpilot.ai/)
- [Spinning Up in Deep RL](https://spinningup.openai.com/)
