# Development: System Response Analysis

## 开发环境

### 依赖
```
Python >= 3.10
NumPy >= 1.24.0
SciPy >= 1.10.0
```

### 安装
```bash
cd projects/system-response
pip install -r requirements.txt
```

## 项目结构

```
src/
├── __init__.py              # 包入口，导出所有公共类
├── transfer_function.py     # TransferFunction 核心类
├── time_response.py         # TimeResponse + TimeResponseData
├── frequency_response.py    # FrequencyResponse + BodeData/NyquistData
├── performance.py           # PerformanceMetrics + PerformanceData
├── stability.py             # StabilityAnalyzer + RouthTable/RootLocusData
├── system_id.py             # SystemIdentifier + IdentificationResult
└── controller_design.py     # ControllerDesigner + PIDParams

tests/
├── test_transfer_function.py    # 15 个测试用例
├── test_time_response.py        # 9 个测试用例
├── test_frequency_response.py   # 12 个测试用例
├── test_performance.py          # 10 个测试用例
├── test_stability.py            # 10 个测试用例
├── test_system_id.py            # 6 个测试用例
└── test_controller_design.py    # 8 个测试用例

examples/
├── basic_analysis.py           # 基础分析示例
├── controller_design.py        # 控制器设计示例
└── system_identification.py    # 系统辨识示例
```

## 模块说明

### transfer_function.py
- `TransferFunction`: 核心数据类
  - 系数存储：降幂排列，自动归一化
  - 运算：*, +, -, feedback
  - 工厂方法：first_order, second_order, from_poles_zeros, integrator, delay
  - 属性：poles, zeros, dc_gain, order, is_proper

### time_response.py
- `TimeResponseData`: t, y, u 数据容器
- `TimeResponse`: 计算引擎
  - step/impulse/ramp: 三种标准响应
  - lsim: 任意输入响应
  - initial: 零输入响应
  - 自动时间范围估计

### frequency_response.py
- `BodeData`: omega, magnitude_db, phase_deg
- `NyquistData`: real, imag, omega
- `StabilityMargins`: gain_margin_db, phase_margin_deg
- `FrequencyResponse`: 计算引擎
  - bode/nyquist: 图数据
  - margins: 稳定裕度
  - resonance_peak/bandwidth: 特征频率

### performance.py
- `PerformanceData`: 7 个性能指标
- `PerformanceMetrics`: 计算引擎
  - step_metrics: 全部指标
  - steady_state_error: 稳态误差
  - second_order_metrics: 解析公式

### stability.py
- `RouthTable`: table, is_stable, sign_changes
- `RootLocusData`: gains, roots
- `StabilityAnalyzer`: 分析引擎
  - routh: 劳斯表
  - root_locus: 根轨迹
  - closed_loop_poles/is_stable: 闭环分析

### system_id.py
- `IdentificationResult`: tf, order, residual
- `SystemIdentifier`: 静态方法集合
  - from_step_response: 阶跃响应辨识
  - from_frequency_response: 频域辨识
  - from_impulse_response: 脉冲响应辨识

### controller_design.py
- `PIDParams`: Kp, Ki, Kd, Tf
- `ControllerDesigner`: 设计引擎
  - pid_ziegler_nichols: Z-N 整定
  - design_lead/lag: 超前/滞后补偿
  - design_from_poles: 极点配置

## 测试

```bash
cd projects/system-response
python -m pytest tests/ -v
```

## 已知限制

1. 劳斯表：零行处理使用 epsilon 近似
2. 系统辨识：仅支持 SISO 系统
3. 根轨迹：不包含渐近线和分离点计算
4. Pade 延迟：仅支持等阶近似
