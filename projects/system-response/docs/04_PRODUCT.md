# Product: System Response Analysis

## 产品定位

控制工程师和学生的系统分析工具箱，提供完整的 LTI 系统分析和控制器设计能力。

## 用户画像

### 主要用户：控制工程师
- 需要快速分析系统响应特性
- 需要设计 PID 或补偿器
- 需要从实验数据辨识系统模型

### 次要用户：学生
- 学习控制理论
- 完成课程作业
- 验证手工计算结果

## 核心场景

### 场景 1：系统响应分析
```
输入：传递函数 G(s)
输出：阶跃响应、性能指标、波特图
价值：一站式获取系统全部动态特性
```

### 场景 2：控制器设计
```
输入：被控对象 G(s) + 性能要求
输出：PID 参数或补偿器传递函数
价值：自动化经典设计方法
```

### 场景 3：系统辨识
```
输入：实验数据 (时域或频域)
输出：传递函数模型
价值：从数据建立数学模型
```

### 场景 4：稳定性评估
```
输入：开环传递函数
输出：稳定裕度、劳斯表、根轨迹
价值：全面评估闭环稳定性
```

## 功能清单

| 优先级 | 功能 | 状态 |
|--------|------|------|
| P0 | 传递函数基本运算 | 完成 |
| P0 | 阶跃/脉冲/斜坡响应 | 完成 |
| P0 | 波特图数据 | 完成 |
| P0 | 性能指标计算 | 完成 |
| P1 | 奈奎斯特图 | 完成 |
| P1 | 增益/相位裕度 | 完成 |
| P1 | 劳斯判据 | 完成 |
| P1 | 根轨迹 | 完成 |
| P2 | PID 整定 | 完成 |
| P2 | 超前/滞后补偿 | 完成 |
| P2 | 系统辨识 | 完成 |

## 使用示例

### 典型工作流

```python
# 1. 定义系统
plant = TransferFunction([1], [1, 1, 0])

# 2. 分析性能
pm = PerformanceMetrics(plant)
metrics = pm.step_metrics()
print(f"超调: {metrics.overshoot_pct:.1f}%")

# 3. 设计控制器
cd = ControllerDesigner(plant)
pid = cd.pid_ziegler_nichols()
pid_tf = ControllerDesigner.pid_transfer_function(pid)

# 4. 验证闭环性能
cl = (pid_tf * plant).feedback()
cl_pm = PerformanceMetrics(cl)
cl_metrics = cl_pm.step_metrics()
print(f"闭环超调: {cl_metrics.overshoot_pct:.1f}%")
```

## 质量指标

- 测试覆盖率：7 个测试模块，覆盖所有核心功能
- 文档完整性：README + 5 份设计文档
- 示例数量：3 个完整示例
