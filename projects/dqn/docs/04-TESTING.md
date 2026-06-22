# 04 - 测试说明

## 测试策略

### 1. 单元测试

测试各个组件的正确性，确保每个函数按预期工作。

### 2. 集成测试

测试组件之间的交互，确保整个系统正常工作。

### 3. 性能测试

测试训练性能和收敛性。

## 测试文件

### 测试结构

```
tests/
├── __init__.py
└── test_dqn.py
```

### 运行测试

```bash
# 运行所有测试
cd projects/dqn
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_dqn.py::TestDQN

# 运行带详细输出
python -m pytest tests/ -v

# 运行带覆盖率
python -m pytest tests/ --cov=src
```

## 单元测试详解

### 1. DQN 网络测试

#### 测试前向传播

```python
class TestDQN:
    def test_forward(self):
        """测试前向传播"""
        model = DQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(1, 4)
        q_values = model(state)

        assert q_values.shape == (1, 2)
        assert not torch.isnan(q_values).any()
```

**验证点：**
- 输出形状正确
- 没有 NaN 值

#### 测试批量前向传播

```python
def test_batch_forward(self):
    """测试批量前向传播"""
    model = DQN(state_dim=4, action_dim=2, hidden_dim=64)
    states = torch.randn(32, 4)
    q_values = model(states)

    assert q_values.shape == (32, 2)
```

**验证点：**
- 批量处理正确
- 输出形状匹配批次大小

#### 测试动作选择

```python
def test_get_action(self):
    """测试动作选择"""
    model = DQN(state_dim=4, action_dim=2, hidden_dim=64)
    state = torch.randn(4)

    # 测试贪婪策略
    action = model.get_action(state, epsilon=0.0)
    assert 0 <= action < 2

    # 测试随机策略
    actions = set()
    for _ in range(100):
        action = model.get_action(state, epsilon=1.0)
        actions.add(action)
    assert len(actions) == 2  # 应该两个动作都被选择过
```

**验证点：**
- 贪婪策略选择有效动作
- 随机策略探索所有动作

### 2. 经验回放缓冲区测试

#### 测试添加和采样

```python
class TestReplayBuffer:
    def test_push_and_sample(self):
        """测试添加和采样"""
        buffer = ReplayBuffer(capacity=1000)

        # 添加经验
        for i in range(100):
            state = np.random.randn(4)
            action = np.random.randint(2)
            reward = np.random.randn()
            next_state = np.random.randn(4)
            done = i % 10 == 0
            buffer.push(state, action, reward, next_state, done)

        assert len(buffer) == 100

        # 采样
        batch_size = 32
        states, actions, rewards, next_states, dones = buffer.sample(batch_size)

        assert states.shape == (batch_size, 4)
        assert actions.shape == (batch_size,)
        assert rewards.shape == (batch_size,)
        assert next_states.shape == (batch_size, 4)
        assert dones.shape == (batch_size,)
```

**验证点：**
- 添加经验后长度正确
- 采样形状正确
- 各组件类型正确

#### 测试容量限制

```python
def test_capacity(self):
    """测试容量限制"""
    buffer = ReplayBuffer(capacity=10)

    # 添加超过容量的经验
    for i in range(20):
        state = np.array([i, i, i, i])
        buffer.push(state, 0, 0.0, state, False)

    assert len(buffer) == 10
```

**验证点：**
- 缓冲区不超过容量
- 自动移除最旧的经验

#### 测试就绪状态

```python
def test_is_ready(self):
    """测试缓冲区就绪状态"""
    buffer = ReplayBuffer(capacity=10)

    assert not buffer.is_ready

    for i in range(10):
        buffer.push(np.zeros(4), 0, 0.0, np.zeros(4), False)

    assert buffer.is_ready
```

**验证点：**
- 未满时返回 False
- 满时返回 True

### 3. DQN 代理测试

#### 测试动作选择

```python
class TestDQNAgent:
    def test_select_action(self):
        """测试动作选择"""
        agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)

        state = np.random.randn(4)

        # 测试训练模式
        action = agent.select_action(state, training=True)
        assert 0 <= action < 2

        # 测试评估模式
        action = agent.select_action(state, training=False)
        assert 0 <= action < 2
```

**验证点：**
- 训练模式动作有效
- 评估模式动作有效

#### 测试经验存储

```python
def test_store_experience(self):
    """测试经验存储"""
    agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)

    state = np.random.randn(4)
    agent.store_experience(state, 0, 1.0, state, False)

    assert len(agent.replay_buffer) == 1
```

**验证点：**
- 经验正确存储
- 缓冲区长度正确

#### 测试训练

```python
def test_train(self):
    """测试训练"""
    agent = DQNAgent(
        state_dim=4,
        action_dim=2,
        buffer_size=100,
        batch_size=32,
        epsilon_start=0.0,  # 禁用探索
    )

    # 填充缓冲区
    for _ in range(50):
        state = np.random.randn(4)
        agent.store_experience(state, 0, 1.0, state, False)

    # 训练
    loss = agent.train()
    assert loss is not None
    assert isinstance(loss, float)
    assert loss >= 0
```

**验证点：**
- 训练返回损失值
- 损失值类型正确
- 损失值非负

#### 测试目标网络更新

```python
def test_target_network_update(self):
    """测试目标网络更新"""
    agent = DQNAgent(
        state_dim=4,
        action_dim=2,
        buffer_size=100,
        batch_size=32,
        target_update_freq=5,
    )

    # 填充缓冲区
    for _ in range(50):
        state = np.random.randn(4)
        agent.store_experience(state, 0, 1.0, state, False)

    # 训练多次
    for _ in range(10):
        agent.train()

    # 检查目标网络是否更新
    assert agent.train_step == 10
```

**验证点：**
- 训练步数正确递增
- 目标网络按频率更新

#### 测试探索率衰减

```python
def test_epsilon_decay(self):
    """测试探索率衰减"""
    agent = DQNAgent(
        state_dim=4,
        action_dim=2,
        buffer_size=100,
        batch_size=32,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.9,
    )

    # 填充缓冲区
    for _ in range(50):
        state = np.random.randn(4)
        agent.store_experience(state, 0, 1.0, state, False)

    initial_epsilon = agent.epsilon

    # 训练多次
    for _ in range(10):
        agent.train()

    assert agent.epsilon < initial_epsilon
    assert agent.epsilon >= 0.01
```

**验证点：**
- 探索率衰减
- 不低于最小值

#### 测试模型保存和加载

```python
def test_save_load(self, tmp_path):
    """测试模型保存和加载"""
    agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)

    # 保存
    save_path = os.path.join(tmp_path, "model.pth")
    agent.save(save_path)
    assert os.path.exists(save_path)

    # 加载
    new_agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)
    new_agent.load(save_path)

    # 验证参数
    assert agent.epsilon == new_agent.epsilon
    assert agent.train_step == new_agent.train_step
```

**验证点：**
- 保存文件存在
- 加载后参数一致

## 集成测试

### 完整训练流程测试

```python
def test_full_training():
    """测试完整训练流程"""
    agent = DQNAgent(
        state_dim=4,
        action_dim=2,
        buffer_size=100,
        batch_size=32,
    )

    # 模拟训练
    for episode in range(10):
        state = np.random.randn(4)
        for step in range(20):
            action = agent.select_action(state, training=True)
            next_state = np.random.randn(4)
            reward = 1.0
            done = step == 19

            agent.store_experience(state, action, reward, next_state, done)
            loss = agent.train()

            state = next_state
            if done:
                break

    # 验证训练完成
    assert agent.train_step > 0
    assert agent.epsilon < 1.0
```

## 性能测试

### 训练收敛性测试

```python
def test_convergence():
    """测试训练收敛性"""
    rewards = train(num_episodes=200)

    # 检查是否收敛
    final_rewards = rewards[-50:]
    avg_reward = np.mean(final_rewards)

    # CartPole 应该能达到平均 400+ 奖励
    assert avg_reward > 400
```

### 内存使用测试

```python
def test_memory_usage():
    """测试内存使用"""
    agent = DQNAgent(
        state_dim=4,
        action_dim=2,
        buffer_size=10000,
        batch_size=64,
    )

    # 填充缓冲区
    for _ in range(10000):
        state = np.random.randn(4)
        agent.store_experience(state, 0, 1.0, state, False)

    # 检查内存使用
    assert len(agent.replay_buffer) == 10000
```

## 测试覆盖率

### 覆盖率目标

- **单元测试覆盖率**: > 90%
- **集成测试覆盖率**: > 80%
- **关键路径覆盖率**: 100%

### 生成覆盖率报告

```bash
# 安装覆盖率工具
pip install pytest-cov

# 运行测试并生成报告
python -m pytest tests/ --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 持续集成

### GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        pip install torch gymnasium numpy pytest pytest-cov

    - name: Run tests
      run: |
        python -m pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v1
```
