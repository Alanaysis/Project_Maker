# 05 - 开发指南

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip 或 conda

### 1.2 依赖安装

```bash
cd projects/mpc-controller
pip install -r requirements.txt
```

### 1.3 开发依赖

```bash
pip install pytest pytest-cov black flake8 mypy
```

## 2. 项目结构

```
mpc-controller/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── plant_model.py     # 被控对象模型
│   ├── mpc_controller.py  # MPC 控制器
│   ├── optimizer.py       # 优化求解器
│   └── simulation.py      # 仿真环境
├── tests/                  # 测试代码
├── examples/               # 示例代码
├── docs/                   # 文档
├── requirements.txt        # 依赖
└── README.md               # 项目说明
```

## 3. 编码规范

### 3.1 代码风格

遵循 PEP 8 规范:

```python
# 好的写法
def compute_control(
    self,
    state: np.ndarray,
    reference: np.ndarray
) -> MPCResult:
    """计算控制输入"""
    pass

# 不好的写法
def computeControl(self, state, reference):
    pass
```

### 3.2 命名规范

```python
# 类名: PascalCase
class MPCController:
    pass

# 函数名: snake_case
def compute_control():
    pass

# 常量: UPPER_SNAKE_CASE
MAX_ITERATIONS = 100

# 私有方法: _前缀
def _internal_method():
    pass
```

### 3.3 类型注解

```python
from typing import Optional, List, Tuple, Dict

def method(
    self,
    x: np.ndarray,
    u: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """带类型注解的方法"""
    pass
```

### 3.4 文档规范

```python
def compute_control(
    self,
    state: np.ndarray,
    reference: np.ndarray,
    u_prev: Optional[np.ndarray] = None
) -> MPCResult:
    """
    计算 MPC 控制输入

    Args:
        state: 当前状态向量，维度为 (n_states,)
        reference: 参考轨迹，维度为 (n_outputs,) 或 (Np, n_outputs)
        u_prev: 上一时刻控制输入，维度为 (n_inputs,)

    Returns:
        MPCResult 对象，包含:
        - u_optimal: 最优控制输入
        - u_sequence: 控制序列
        - x_predicted: 预测状态序列
        - y_predicted: 预测输出序列
        - cost: 代价值
        - info: 优化信息

    Raises:
        ValueError: 当输入维度不正确时

    Example:
        >>> controller = MPCController(plant, config)
        >>> result = controller.compute_control(
        ...     state=np.array([0.0, 0.0]),
        ...     reference=np.array([1.0, 0.0])
        ... )
        >>> print(result.u_optimal)
        [0.5]
    """
    pass
```

## 4. 开发流程

### 4.1 功能开发

1. **需求分析**: 明确功能需求
2. **设计**: 设计接口和数据结构
3. **实现**: 编写代码
4. **测试**: 编写和运行测试
5. **文档**: 更新文档
6. **审查**: 代码审查
7. **合并**: 合并到主分支

### 4.2 分支管理

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发和提交
git add .
git commit -m "feat: add new feature"

# 合并到主分支
git checkout master
git merge feature/new-feature
```

### 4.3 提交规范

使用 Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型:
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例:
```
feat(controller): add adaptive MPC
fix(optimizer): fix constraint handling
docs(readme): update installation guide
```

## 5. 新增功能

### 5.1 新增被控对象

```python
# 1. 继承基类
class NewSystem(NonlinearPlantModel):
    def __init__(self, param1, param2):
        # 2. 定义动力学函数
        def dynamics(x, u):
            # 系统动力学
            return dx_dt

        # 3. 定义输出函数（可选）
        def output(x):
            return x

        # 4. 调用父类初始化
        super().__init__(
            n_states=n,
            n_inputs=m,
            n_outputs=p,
            dynamics_fn=dynamics,
            output_fn=output
        )

# 5. 编写测试
class TestNewSystem:
    def test_initialization(self):
        system = NewSystem(1.0, 2.0)
        assert system.n_states == n

    def test_dynamics(self):
        # 测试动力学
        pass
```

### 5.2 新增控制模式

```python
# 1. 定义新模式
class MPCMode(Enum):
    LINEAR = "linear"
    NONLINEAR = "nonlinear"
    NEW_MODE = "new_mode"  # 新增

# 2. 在控制器中实现
class MPCController:
    def _get_linearized_model(self, state, u):
        if self.config.mode == MPCMode.NEW_MODE:
            # 新模式的实现
            pass
```

### 5.3 新增优化器

```python
# 1. 继承优化器基类
class NewOptimizer(MPCOptimizer):
    def solve(self, x0, A_list, B_list, C_list, x_ref, u_prev):
        # 自定义优化算法
        pass
```

## 6. 性能优化

### 6.1 代码优化

```python
# 向量化运算
# 不好
cost = 0
for k in range(Np):
    cost += (y[k] - r[k])**2

# 好
cost = np.sum((Y - R)**2)
```

### 6.2 内存优化

```python
# 预分配数组
states = np.zeros((N+1, n_states))

# 使用视图而非复制
x_view = states[k:k+1]
```

### 6.3 计算优化

```python
# 缓存常数矩阵
self._H = H  # 只计算一次

# 热启动
u_init = self._u_sequence
```

## 7. 调试技巧

### 7.1 日志记录

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"状态: {state}")
logger.info(f"优化成功: {result.info['success']}")
logger.error(f"优化失败: {result.info['message']}")
```

### 7.2 可视化调试

```python
import matplotlib.pyplot as plt

# 绘制预测轨迹
plt.plot(result.x_predicted)
plt.plot(result.y_predicted)
plt.show()

# 绘制控制输入
plt.step(result.u_sequence)
plt.show()
```

### 7.3 单元测试调试

```bash
# 运行单个测试
python -m pytest tests/test_file.py::TestClass::test_method -v

# 显示详细输出
python -m pytest tests/ -v -s

# 停在第一个失败
python -m pytest tests/ -x
```

## 8. 文档编写

### 8.1 代码文档

- 所有公共方法必须有 docstring
- 包含参数、返回值、异常说明
- 提供使用示例

### 8.2 项目文档

- README.md: 项目概述
- docs/: 详细文档
- examples/: 使用示例

### 8.3 文档更新

代码变更时同步更新文档:

```bash
# 更新文档
vim docs/03-IMPLEMENTATION.md

# 验证文档
python -m doctest src/module.py
```

## 9. 发布流程

### 9.1 版本号

使用语义化版本:

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 变更
MINOR: 向后兼容的功能新增
PATCH: 向后兼容的问题修复
```

### 9.2 发布检查

```bash
# 运行测试
python -m pytest tests/ -v

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/

# 生成文档
cd docs && make html
```

### 9.3 发布步骤

```bash
# 1. 更新版本号
vim src/__init__.py

# 2. 更新 CHANGELOG
vim CHANGELOG.md

# 3. 提交
git add .
git commit -m "release: v1.0.0"

# 4. 打标签
git tag v1.0.0

# 5. 推送
git push origin master --tags
```

## 10. 常见问题

### 10.1 优化不收敛

**原因**: 权重设置不当、约束过紧

**解决**:
```python
# 调整权重
weights = MPCWeights(
    Q=np.diag([10.0, 1.0]),  # 增加状态权重
    R=np.array([[0.01]])     # 减少输入权重
)

# 放松约束
constraints = MPCConstraints(
    u_min=np.array([-10.0]),
    u_max=np.array([10.0])
)
```

### 10.2 跟踪误差大

**原因**: 模型不准确、预测时域太短

**解决**:
```python
# 增加预测时域
config = MPCConfig(
    prediction_horizon=20,  # 增加
    control_horizon=10
)

# 改进模型
# 使用更精确的模型参数
```

### 10.3 数值不稳定

**原因**: 条件数过大、浮点误差

**解决**:
```python
# 添加正则化
H_reg = H + 1e-6 * np.eye(H.shape[0])

# 使用更稳定的求解器
result = minimize(objective, U0, method='L-BFGS-B')
```

### 10.4 计算太慢

**原因**: 问题规模大、迭代次数多

**解决**:
```python
# 减少时域
config = MPCConfig(
    prediction_horizon=5,  # 减少
    control_horizon=3
)

# 限制迭代次数
result = minimize(objective, U0, options={'maxiter': 50})

# 使用热启动
u_init = self._u_sequence
```

## 11. 最佳实践

### 11.1 代码组织

- 单一职责原则
- 依赖注入
- 接口分离

### 11.2 测试驱动开发

- 先写测试
- 再写实现
- 重构代码

### 11.3 持续集成

- 自动化测试
- 代码覆盖率
- 静态分析

### 11.4 代码审查

- 功能正确性
- 代码风格
- 性能影响
- 文档完整性
