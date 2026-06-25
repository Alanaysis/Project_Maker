# 状态空间模型 - 项目设计

## 1. 架构设计

### 1.1 整体架构

```
state-space/
├── src/                      # 源代码
│   ├── __init__.py          # 包初始化
│   ├── state_space_model.py # 核心模型
│   ├── kalman_filter.py     # 卡尔曼滤波
│   ├── analysis.py          # 系统分析
│   ├── controller.py        # 控制器设计
│   └── observer.py          # 观测器设计
├── tests/                    # 测试
├── examples/                 # 示例
└── docs/                     # 文档
```

### 1.2 模块依赖关系

```
┌─────────────────┐
│   examples/      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   controller.py  │ ← LQR需要Riccati方程求解
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   observer.py    │ ← 使用极点配置
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ kalman_filter.py │ ← 核心滤波算法
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   analysis.py    │ ← 矩阵分析工具
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│state_space_model │ ← 基础模型
└─────────────────┘
```

## 2. 类设计

### 2.1 StateSpaceModel

**职责:** 封装离散时间状态空间模型，提供仿真和分析接口。

```python
class StateSpaceModel:
    """离散时间状态空间模型"""

    def __init__(self, A, B, C, D=None, dt=1.0):
        """初始化模型矩阵"""

    def simulate(self, x0, u, n_steps=None):
        """仿真系统响应"""

    def step(self, x, u):
        """单步仿真"""

    def get_eigenvalues(self):
        """获取系统特征值"""

    def is_stable(self):
        """判断系统稳定性"""

    def get_transfer_function_coeffs(self):
        """获取传递函数系数"""
```

**设计决策:**
- 使用numpy数组存储矩阵
- 支持SISO和MIMO系统
- 提供维度验证

### 2.2 KalmanFilter

**职责:** 实现离散卡尔曼滤波算法，进行状态估计。

```python
class KalmanFilter:
    """离散卡尔曼滤波器"""

    def __init__(self, A, B, C, Q, R, P0=None, x0=None):
        """初始化滤波器参数"""

    def predict(self, u=None):
        """预测步骤"""

    def update(self, y):
        """更新步骤"""

    def filter_step(self, y, u=None):
        """完整滤波步骤"""

    def smooth(self, measurements, inputs=None):
        """RTS平滑"""

    def get_estimation_error(self, true_states):
        """计算估计误差"""
```

**设计决策:**
- 分离预测和更新步骤
- 保存历史记录用于分析
- 支持RTS平滑

### 2.3 分析函数

**职责:** 提供可控性、可观性分析工具。

```python
def controllability_matrix(A, B):
    """计算可控性矩阵"""

def observability_matrix(A, C):
    """计算可观性矩阵"""

def is_controllable(A, B):
    """判断可控性"""

def is_observable(A, C):
    """判断可观性"""

def gramian_controllability(A, B, N=100):
    """计算可控性格拉姆矩阵"""

def gramian_observability(A, C, N=100):
    """计算可观性格拉姆矩阵"""
```

**设计决策:**
- 使用函数而非类，简化接口
- 支持容差参数
- 提供格拉姆矩阵计算

### 2.4 StateFeedbackController

**职责:** 实现状态反馈控制律。

```python
class StateFeedbackController:
    """状态反馈控制器"""

    def __init__(self, A, B, K=None):
        """初始化控制器"""

    def compute_control(self, x, r=None):
        """计算控制输入"""

    def place_poles(self, desired_poles):
        """极点配置"""

    def get_closed_loop_system(self):
        """获取闭环系统"""

    def get_closed_loop_poles(self):
        """获取闭环极点"""
```

**设计决策:**
- 支持极点配置
- 支持自定义增益
- 提供闭环系统分析

### 2.5 LQRController

**职责:** 实现LQR最优控制器。

```python
class LQRController:
    """LQR控制器"""

    def __init__(self, A, B, Q, R, N=None):
        """初始化LQR控制器"""

    def compute_control(self, x, r=None):
        """计算LQR控制输入"""

    def get_cost(self, x0, N=100):
        """计算控制成本"""

    def simulate(self, x0, n_steps, r=None):
        """仿真LQR控制"""
```

**设计决策:**
- 使用scipy求解Riccati方程
- 支持交叉权重项
- 提供成本计算

### 2.6 FullOrderObserver

**职责:** 实现全阶状态观测器。

```python
class FullOrderObserver:
    """全阶状态观测器"""

    def __init__(self, A, B, C, L=None):
        """初始化观测器"""

    def design_by_poles(self, desired_poles):
        """通过极点配置设计观测器"""

    def update(self, y, u=None):
        """更新观测器"""

    def get_observer_poles(self):
        """获取观测器极点"""
```

**设计决策:**
- 利用对偶性进行设计
- 支持极点配置
- 提供状态估计

## 3. 数据结构

### 3.1 矩阵表示

所有矩阵使用numpy二维数组表示：
```python
A = np.array([[a11, a12],
              [a21, a22]])  # 2x2矩阵
```

### 3.2 向量表示

状态、输入、输出使用numpy一维数组表示：
```python
x = np.array([x1, x2])  # 2维状态
u = np.array([u1])       # 1维输入
```

### 3.3 历史记录

使用列表存储历史数据：
```python
self._state_history: List[np.ndarray] = []
self._output_history: List[np.ndarray] = []
```

## 4. 接口设计

### 4.1 一致性原则

- 所有矩阵参数接受array-like输入
- 自动转换为numpy数组
- 统一的维度验证

### 4.2 默认值

- D矩阵默认为零矩阵
- 初始状态默认为零向量
- 初始协方差默认为单位矩阵

### 4.3 返回值

- 仿真返回元组 (states, outputs)
- 分析返回numpy数组
- 布尔判断返回bool

## 5. 错误处理

### 5.1 输入验证

```python
def _validate_dimensions(self):
    """验证矩阵维度一致性"""
    assert self.A.shape == (n, n)
    assert self.B.shape == (n, m)
    # ...
```

### 5.2 异常类型

- ValueError: 参数值错误
- AssertionError: 维度不匹配
- RuntimeError: 计算错误

### 5.3 错误消息

提供清晰的错误信息：
```python
raise ValueError(f"期望极点数量({len(poles)})与状态维度({n})不匹配")
```

## 6. 性能设计

### 6.1 向量化计算

使用numpy向量化操作避免循环：
```python
# 不推荐
for i in range(n):
    y[i] = sum(C[i,j] * x[j] for j in range(n))

# 推荐
y = C @ x
```

### 6.2 内存管理

- 预分配数组
- 避免频繁内存分配
- 使用视图而非复制

### 6.3 计算优化

- 利用矩阵稀疏性
- 缓存中间结果
- 使用BLAS/LAPACK后端

## 7. 测试策略

### 7.1 单元测试

- 测试每个公共方法
- 验证数学正确性
- 检查边界条件

### 7.2 集成测试

- 测试模块间交互
- 验证完整工作流
- 检查端到端功能

### 7.3 性能测试

- 测量计算时间
- 检查内存使用
- 识别瓶颈

## 8. 可扩展性

### 8.1 扩展点

- 非线性滤波器
- 自适应控制
- 鲁棒控制
- 分布式系统

### 8.2 插件机制

```python
# 基类
class FilterBase:
    def predict(self): ...
    def update(self, y): ...

# 具体实现
class KalmanFilter(FilterBase): ...
class ExtendedKalmanFilter(FilterBase): ...
```

## 9. 配置管理

### 9.1 系统参数

```python
config = {
    'dt': 0.01,           # 采样时间
    'noise': {
        'process': 0.01,  # 过程噪声
        'measurement': 0.1  # 测量噪声
    }
}
```

### 9.2 运行时配置

支持运行时修改参数：
```python
kf.R = new_R  # 更新测量噪声协方差
```

## 10. 未来规划

### 10.1 短期目标

- 完成核心功能实现
- 编写完整测试
- 创建详细文档

### 10.2 中期目标

- 添加非线性滤波器
- 支持连续时间系统
- 优化性能

### 10.3 长期目标

- 支持分布式系统
- 实现自适应算法
- 创建GUI界面
