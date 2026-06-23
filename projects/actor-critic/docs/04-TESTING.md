# Actor-Critic 测试策略

## 1. 测试框架

使用 pytest 作为测试框架，支持：
- 参数化测试
- 临时目录
- 断言检查

## 2. 测试覆盖

### 2.1 单元测试

#### Actor 网络测试

```python
class TestActorNetwork:
    def test_init(self):
        """测试网络初始化"""
        network = ActorNetwork(state_dim=4, action_dim=2)
        assert network is not None

    def test_forward_shape(self):
        """测试前向传播输出形状"""
        network = ActorNetwork(state_dim=4, action_dim=2)
        state = torch.randn(1, 4)
        output = network(state)
        assert output.shape == (1, 2)

    def test_get_action_probs(self):
        """测试动作概率和为 1"""
        network = ActorNetwork(state_dim=4, action_dim=2)
        state = torch.randn(1, 4)
        probs = network.get_action_probs(state)
        assert torch.allclose(probs.sum(dim=-1), torch.ones(1), atol=1e-6)

    def test_get_action(self):
        """测试动作选择"""
        network = ActorNetwork(state_dim=4, action_dim=2)
        state = torch.randn(4)
        action, log_prob = network.get_action(state)
        assert 0 <= action < 2
        assert log_prob.dim() == 0
```

#### Critic 网络测试

```python
class TestCriticNetwork:
    def test_forward_shape(self):
        """测试前向传播输出形状"""
        network = CriticNetwork(state_dim=4)
        state = torch.randn(1, 4)
        output = network(state)
        assert output.shape == (1, 1)

    def test_get_value(self):
        """测试价值估计"""
        network = CriticNetwork(state_dim=4)
        state = torch.randn(4)
        value = network.get_value(state)
        assert value.dim() == 0
```

#### 优势函数测试

```python
class TestComputeReturns:
    def test_single_reward(self):
        """测试单个奖励的回报计算"""
        returns = compute_returns([1.0], gamma=0.99)
        assert returns[0] == pytest.approx(1.0)

    def test_multiple_rewards(self):
        """测试多个奖励的回报计算"""
        rewards = [1.0, 1.0, 1.0]
        returns = compute_returns(rewards, gamma=0.99)
        assert returns[0] == pytest.approx(1.0 + 0.99 + 0.99**2)

class TestComputeAdvantages:
    def test_simple_advantage(self):
        """测试简单优势计算"""
        rewards = [1.0, 1.0, 1.0]
        values = [0.5, 0.5, 0.5]
        advantages = compute_advantages(rewards, values, gamma=0.99)
        assert len(advantages) == 3
```

#### Agent 测试

```python
class TestActorCriticAgent:
    def test_select_action(self):
        """测试动作选择"""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        state = np.array([1.0, 2.0, 3.0, 4.0])
        action = agent.select_action(state)
        assert 0 <= action < 2

    def test_update(self):
        """测试网络更新"""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)

        # 模拟 episode
        for _ in range(10):
            state = np.random.randn(4)
            agent.select_action(state)
            agent.store_reward(np.random.randn())

        losses = agent.update()
        assert "actor_loss" in losses
        assert "critic_loss" in losses
        assert "entropy" in losses

    def test_save_load(self, tmp_path):
        """测试模型保存和加载"""
        agent = ActorCriticAgent(state_dim=4, action_dim=2)
        save_path = tmp_path / "checkpoint.pt"

        agent.save(str(save_path))
        assert save_path.exists()

        agent2 = ActorCriticAgent(state_dim=4, action_dim=2)
        agent2.load(str(save_path))

        # 验证参数匹配
        for p1, p2 in zip(agent.actor.parameters(), agent2.actor.parameters()):
            assert torch.allclose(p1, p2)
```

## 3. 集成测试

### 3.1 CartPole 训练测试

```python
def test_cartpole_training():
    """测试 CartPole 环境训练"""
    env = gym.make("CartPole-v1")
    agent = ActorCriticAgent(
        state_dim=env.observation_space.shape[0],
        action_dim=env.action_space.n,
    )

    # 训练几个 episode
    for episode in range(5):
        state, _ = env.reset()
        total_reward = 0

        for step in range(200):
            action = agent.select_action(state)
            next_state, reward, done, _, _ = env.step(action)
            agent.store_reward(reward)
            total_reward += reward
            state = next_state
            if done:
                break

        losses = agent.update()
        assert total_reward > 0

    env.close()
```

## 4. 测试运行

### 4.1 运行所有测试

```bash
cd projects/actor-critic
pytest tests/ -v
```

### 4.2 运行特定测试

```bash
# 运行 Actor 网络测试
pytest tests/test_actor_network.py -v

# 运行 Agent 测试
pytest tests/test_agent.py -v
```

### 4.3 生成覆盖率报告

```bash
pytest tests/ --cov=actor_critic --cov-report=html
```

## 5. 测试结果

### 5.1 预期输出

```
tests/test_actor_network.py::TestActorNetwork::test_init PASSED
tests/test_actor_network.py::TestActorNetwork::test_forward_shape PASSED
tests/test_actor_network.py::TestActorNetwork::test_get_action_probs PASSED
tests/test_actor_network.py::TestActorNetwork::test_get_action PASSED
tests/test_critic_network.py::TestCriticNetwork::test_forward_shape PASSED
tests/test_agent.py::TestActorCriticAgent::test_select_action PASSED
tests/test_agent.py::TestActorCriticAgent::test_update PASSED
tests/test_advantages.py::TestComputeReturns::test_single_reward PASSED

========================= 8 passed in 0.15s =========================
```

## 6. 持续集成

在 CI 流程中：
1. 安装依赖：`pip install -e .[dev]`
2. 运行测试：`pytest tests/ -v`
3. 检查覆盖率：确保核心模块覆盖率 > 80%
