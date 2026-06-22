# 策略梯度测试文档

## 测试策略

### 测试层次

1. **单元测试**：测试单个组件的功能
2. **集成测试**：测试组件之间的交互
3. **系统测试**：测试完整的训练流程

### 测试覆盖

- 策略网络：初始化、前向传播、动作选择、梯度流
- 基线：各种基线实现、优势计算
- REINFORCE：轨迹采集、回报计算、策略更新

## 单元测试

### 策略网络测试

```python
class TestPolicyNetwork:
    def test_init():
        # 测试网络初始化

    def test_forward_shape():
        # 测试前向传播输出形状

    def test_log_softmax():
        # 测试输出是对数概率

    def test_get_action():
        # 测试动作选择

    def test_gradient_flow():
        # 测试梯度可以流过网络
```

**关键测试点**：
1. 输出形状正确
2. 输出是合法的对数概率（exp 后和为 1）
3. 梯度可以正常计算

### 基线测试

```python
class TestNoBaseline:
    def test_get_baseline():
        # 测试返回零

class TestMovingAverageBaseline:
    def test_first_update():
        # 测试第一次更新

    def test_subsequent_updates():
        # 测试后续更新

    def test_alpha_effect():
        # 测试 alpha 系数的影响
```

**关键测试点**：
1. 无基线返回零
2. 移动平均正确更新
3. 优势计算正确

### REINFORCE 测试

```python
class TestREINFORCE:
    def test_compute_returns():
        # 测试折扣回报计算

    def test_select_action():
        # 测试动作选择

    def test_collect_episode():
        # 测试轨迹采集

    def test_update():
        # 测试策略更新
```

**关键测试点**：
1. 折扣回报计算正确
2. 轨迹数据完整
3. 策略参数被更新

## 集成测试

### 完整训练测试

```python
def test_short_training():
    # 创建环境和智能体
    # 训练几个 episode
    # 检查训练历史
```

### 带基线的训练测试

```python
def test_training_with_baseline():
    # 使用价值网络基线训练
    # 检查策略和价值网络都被更新
```

## 测试工具

### Mock 环境

```python
class MockEnv:
    def __init__(self, episode_length=10):
        self.episode_length = episode_length
        self.step_count = 0

    def reset(self):
        self.step_count = 0
        return np.zeros(4), {}

    def step(self, action):
        self.step_count += 1
        done = self.step_count >= self.episode_length
        return np.zeros(4), 1.0, done, False, {}
```

**优点**：
- 快速测试
- 确定性行为
- 不依赖外部环境

### 测试夹具

```python
@pytest.fixture
def policy():
    return PolicyNetwork(state_dim=4, action_dim=2)

@pytest.fixture
def optimizer(policy):
    return torch.optim.Adam(policy.parameters(), lr=0.01)

@pytest.fixture
def agent(policy, optimizer):
    return REINFORCE(policy=policy, optimizer=optimizer)
```

## 运行测试

### 命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_policy_network.py

# 运行特定测试类
pytest tests/test_policy_network.py::TestPolicyNetwork

# 运行特定测试方法
pytest tests/test_policy_network.py::TestPolicyNetwork::test_forward_shape

# 显示详细输出
pytest -v tests/

# 显示打印输出
pytest -s tests/
```

### 测试覆盖率

```bash
# 安装覆盖率工具
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest --cov=src tests/

# 生成 HTML 报告
pytest --cov=src --cov-report=html tests/
```

## 测试结果解读

### 成功标准

1. 所有测试通过
2. 覆盖率 > 80%
3. 没有警告或错误

### 常见失败原因

1. **形状不匹配**：检查张量维度
2. **数值错误**：检查梯度和损失计算
3. **初始化问题**：检查随机种子

## 调试技巧

### 使用断点

```python
import pdb; pdb.set_trace()
```

### 打印调试

```python
print(f"Shape: {tensor.shape}")
print(f"Value: {tensor}")
print(f"Grad: {tensor.grad}")
```

### 可视化调试

```python
import matplotlib.pyplot as plt

plt.plot(rewards)
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.show()
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
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
```

## 测试最佳实践

1. **测试独立**：每个测试应该独立运行
2. **测试快速**：单元测试应该快速完成
3. **测试清晰**：测试名称应该清晰描述测试内容
4. **测试全面**：覆盖正常和边界情况
5. **测试可维护**：测试代码应该易于理解和维护
