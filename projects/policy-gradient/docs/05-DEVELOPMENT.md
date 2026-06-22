# 策略梯度开发文档

## 开发环境

### 依赖

- Python 3.8+
- PyTorch 2.0+
- Gymnasium 0.29+
- NumPy 1.24+
- Matplotlib 3.7+
- pytest 7.0+

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd policy-gradient

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 开发流程

### 1. 环境搭建

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

### 2. 代码风格

使用 Black 格式化代码：

```bash
black src/ tests/
```

使用 Flake8 检查代码风格：

```bash
flake8 src/ tests/
```

### 3. 测试

```bash
# 运行测试
pytest tests/

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: 实现 REINFORCE 算法"
git push
```

## 代码规范

### 命名规范

- 类名：PascalCase（如 `PolicyNetwork`）
- 函数名：snake_case（如 `compute_returns`）
- 变量名：snake_case（如 `log_probs`）
- 常量名：UPPER_CASE（如 `GAMMA`）

### 文档规范

- 每个模块都有模块级文档
- 每个类都有类级文档
- 每个公共方法都有方法级文档
- 使用 Google 风格的文档字符串

### 测试规范

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头
- 使用 pytest 夹具（fixture）

## 调试技巧

### 1. 打印调试

```python
print(f"Log probs: {log_probs}")
print(f"Returns: {returns}")
print(f"Advantages: {advantages}")
```

### 2. 断点调试

```python
import pdb; pdb.set_trace()
```

### 3. 可视化调试

```python
import matplotlib.pyplot as plt

# 绘制训练曲线
plt.plot(rewards)
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.show()
```

### 4. TensorBoard

```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter()

# 记录标量
writer.add_scalar('Loss/train', loss, episode)

# 记录直方图
writer.add_histogram('Policy/logits', logits, episode)

writer.close()
```

## 常见问题

### Q1: 训练不稳定

**可能原因**：
- 学习率太大
- 梯度爆炸
- 基线不合适

**解决方案**：
- 减小学习率
- 使用梯度裁剪
- 尝试不同的基线

### Q2: 训练太慢

**可能原因**：
- 学习率太小
- 网络太大
- 样本效率低

**解决方案**：
- 增大学习率
- 减小网络规模
- 使用更高效的算法

### Q3: 不收敛

**可能原因**：
- 网络初始化问题
- 奖励设计问题
- 算法实现错误

**解决方案**：
- 检查网络初始化
- 检查奖励函数
- 检查算法实现

## 性能优化

### 1. 批量处理

```python
# 采集多个 episode
episodes = [self.collect_episode(env) for _ in range(batch_size)]

# 合并数据
all_returns = torch.cat([self.compute_returns(ep.rewards) for ep in episodes])
```

### 2. 并行环境

```python
import multiprocessing as mp

def worker(env, policy, queue):
    episode = collect_episode(env, policy)
    queue.put(episode)

# 创建多个环境
envs = [make_env() for _ in range(num_workers)]

# 并行采集
with mp.Pool(num_workers) as pool:
    episodes = pool.starmap(collect_episode, [(env, policy) for env in envs])
```

### 3. GPU 加速

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

policy = policy.to(device)
states = states.to(device)
returns = returns.to(device)
```

## 扩展开发

### 1. 添加新的基线

```python
class NewBaseline(Baseline):
    def get_baseline(self, returns):
        # 实现新的基线逻辑
        return baseline_values
```

### 2. 添加新的策略网络

```python
class NewPolicyNetwork(PolicyNetwork):
    def __init__(self):
        # 实现新的网络结构
        super().__init__(...)

    def forward(self, state):
        # 实现新的前向传播
        return log_probs
```

### 3. 添加新的算法

```python
class NewAlgorithm(REINFORCE):
    def update(self, episode):
        # 实现新的更新逻辑
        return metrics
```

## 版本管理

### 版本号

- 主版本号：不兼容的 API 修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 更新日志

```markdown
## [1.0.0] - 2024-01-01

### Added
- 实现 REINFORCE 算法
- 实现策略网络
- 实现基线减法

### Changed
- 无

### Fixed
- 无
```

## 部署

### 打包

```bash
# 创建 setup.py
# 打包
python setup.py sdist bdist_wheel
```

### 发布

```bash
# 上传到 PyPI
twine upload dist/*
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
