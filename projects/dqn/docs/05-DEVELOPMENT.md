# 05 - 开发指南

## 开发环境设置

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install torch gymnasium numpy matplotlib pytest pytest-cov
```

### 2. 项目结构

```
dqn/
├── src/
│   ├── __init__.py
│   ├── dqn.py            # DQN 神经网络
│   ├── replay_buffer.py   # 经验回放
│   ├── agent.py           # DQN 代理
│   └── train.py           # 训练脚本
├── tests/
│   ├── __init__.py
│   └── test_dqn.py        # 单元测试
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
└── LEARNING_NOTES.md
```

## 开发流程

### 1. 功能开发

#### 添加新功能

1. **创建分支**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **实现功能**
   - 编写代码
   - 添加测试
   - 更新文档

3. **测试**
   ```bash
   python -m pytest tests/ -v
   ```

4. **提交**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```

5. **合并**
   ```bash
   git checkout master
   git merge feature/new-feature
   ```

#### 代码规范

- 使用 Python 类型提示
- 遵循 PEP 8 规范
- 编写文档字符串
- 添加必要的注释

### 2. Bug 修复

#### 修复流程

1. **重现问题**
   ```bash
   # 运行测试重现问题
   python -m pytest tests/test_dqn.py::TestDQN -v
   ```

2. **定位问题**
   - 检查错误信息
   - 添加调试输出
   - 使用断点调试

3. **修复问题**
   - 修改代码
   - 添加测试用例
   - 验证修复

4. **提交修复**
   ```bash
   git add .
   git commit -m "fix: 修复问题描述"
   ```

### 3. 重构

#### 重构原则

- 保持功能不变
- 提高代码质量
- 改善可读性
- 优化性能

#### 重构步骤

1. **确保测试通过**
   ```bash
   python -m pytest tests/ -v
   ```

2. **进行重构**
   - 提取函数
   - 重命名变量
   - 简化逻辑

3. **再次测试**
   ```bash
   python -m pytest tests/ -v
   ```

4. **提交重构**
   ```bash
   git add .
   git commit -m "refactor: 重构描述"
   ```

## 代码质量

### 1. 类型提示

```python
from typing import Optional, Tuple

def train(self) -> Optional[float]:
    """训练一步"""
    pass

def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
    """采样批次"""
    pass
```

### 2. 文档字符串

```python
class DQNAgent:
    """
    DQN 代理

    实现 DQN 算法，包括：
    - 当前网络和目标网络
    - 经验回放
    - epsilon-greedy 探索策略

    Args:
        state_dim: 状态空间维度
        action_dim: 动作空间维度
        hidden_dim: 隐藏层维度
        learning_rate: 学习率
        gamma: 折扣因子
    """
```

### 3. 错误处理

```python
def train(self) -> Optional[float]:
    # 检查缓冲区是否有足够样本
    if len(self.replay_buffer) < self.batch_size:
        return None

    try:
        # 训练逻辑
        pass
    except Exception as e:
        print(f"训练错误: {e}")
        return None
```

### 4. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train(self) -> Optional[float]:
    logger.info("开始训练")
    # 训练逻辑
    logger.info(f"训练完成，损失: {loss}")
    return loss
```

## 性能优化

### 1. GPU 加速

```python
# 检查 GPU 可用性
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 移动模型到 GPU
model = model.to(device)

# 移动数据到 GPU
state = state.to(device)
```

### 2. 批量处理

```python
# 批量前向传播
states = torch.FloatTensor(states).to(device)
q_values = model(states)

# 批量计算损失
loss = nn.MSELoss()(q_values, target_q_values)
```

### 3. 内存优化

```python
# 使用 torch.no_grad() 避免计算梯度
with torch.no_grad():
    target_q = target_net(next_state)

# 定期清理缓存
torch.cuda.empty_cache()
```

### 4. 并行处理

```python
# 使用 DataLoader 进行批量采样
from torch.utils.data import DataLoader, Dataset

class ReplayDataset(Dataset):
    def __init__(self, buffer):
        self.buffer = buffer

    def __getitem__(self, idx):
        return self.buffer[idx]

    def __len__(self):
        return len(self.buffer)

dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
```

## 调试技巧

### 1. 打印调试

```python
# 打印变量值
print(f"State shape: {state.shape}")
print(f"Q values: {q_values}")

# 打印梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: {param.grad.mean()}")
```

### 2. 断点调试

```python
# 使用 pdb
import pdb; pdb.set_trace()

# 使用 breakpoint()
breakpoint()
```

### 3. 可视化调试

```python
import matplotlib.pyplot as plt

# 绘制奖励曲线
plt.plot(rewards)
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.show()

# 绘制 Q 值分布
plt.hist(q_values.detach().numpy())
plt.xlabel('Q Value')
plt.ylabel('Frequency')
plt.show()
```

### 4. 性能分析

```python
import cProfile

# 分析训练函数
cProfile.run('train(num_episodes=100)')

# 使用 timeit
import timeit
timeit.timeit('agent.train()', number=1000)
```

## 部署

### 1. 模型导出

```python
# 保存模型
torch.save(model.state_dict(), 'model.pth')

# 加载模型
model.load_state_dict(torch.load('model.pth'))
```

### 2. ONNX 导出

```python
# 导出为 ONNX
dummy_input = torch.randn(1, 4)
torch.onnx.export(model, dummy_input, 'model.onnx')
```

### 3. 模型服务

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
model = DQN(4, 2)
model.load_state_dict(torch.load('model.pth'))

@app.route('/predict', methods=['POST'])
def predict():
    state = request.json['state']
    state = torch.FloatTensor(state).unsqueeze(0)
    with torch.no_grad():
        q_values = model(state)
    action = q_values.argmax().item()
    return jsonify({'action': action})
```

## 最佳实践

### 1. 代码组织

- 按功能模块化
- 保持函数简洁
- 避免重复代码
- 使用配置文件

### 2. 测试驱动开发

- 先写测试
- 再写实现
- 重构代码
- 重复循环

### 3. 版本控制

- 使用有意义的提交信息
- 保持提交原子性
- 使用分支管理功能
- 定期合并主分支

### 4. 文档

- 编写清晰的 README
- 添加代码注释
- 维护变更日志
- 记录设计决策

## 常见问题

### 1. 训练不收敛

**原因：**
- 学习率过大
- 探索率不足
- 网络结构不合适

**解决方案：**
- 减小学习率
- 增加探索率
- 调整网络结构

### 2. 内存溢出

**原因：**
- 缓冲区过大
- 批次过大
- 网络过大

**解决方案：**
- 减小缓冲区容量
- 减小批次大小
- 简化网络结构

### 3. 训练速度慢

**原因：**
- 没有使用 GPU
- 批次过小
- 网络过大

**解决方案：**
- 使用 GPU 加速
- 增大批次大小
- 简化网络结构

### 4. 测试失败

**原因：**
- 代码错误
- 环境问题
- 依赖缺失

**解决方案：**
- 检查错误信息
- 验证环境配置
- 安装缺失依赖
