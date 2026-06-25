# 放大器设计 - 开发日志

## 2026-06-24: 项目初始化

### 完成的工作

#### 1. BJT 基本放大器 (src/bjt.py)
- 实现 BJTParams 数据类 (beta, V_A, V_BE, V_T)
- 实现 CommonEmitter 类
  - 直流工作点计算 (分压偏置)
  - 小信号电压增益 (含负载效应)
  - 输入/输出阻抗计算
- 实现 CommonCollector 类
  - 电压增益接近 1
  - 高输入阻抗、低输出阻抗
- 实现 CommonBase 类
  - 高增益同相放大
  - 低输入阻抗

#### 2. 运算放大器电路 (src/opamp.py)
- 实现 OpAmpParams 数据类
- 实现 InvertingAmp 类
  - 理想/实际增益计算
  - 带宽、最大输出摆幅
  - 频率响应传递函数
- 实现 NonInvertingAmp 类
  - 高输入阻抗
  - 频率响应
- 实现 DifferentialAmp 类
  - 差模/共模增益
  - CMRR 计算
- 实现 InstrumentationAmp 类
  - 三运放结构
  - 可编程增益设置

#### 3. 频率响应分析 (src/frequency.py)
- 实现 GainBandwidthProduct 类
  - 增益-带宽互算
  - 单极点频率响应
  - 建立时间估算
- 实现 PhaseCompensation 类
  - 主极点补偿
  - 超前补偿
  - 滞后补偿
  - 密勒补偿
- 实现 StabilityAnalyzer 类
  - 环路增益传递函数
  - 相位裕度/增益裕度
  - 阶跃响应参数估算

#### 4. 实际应用 (src/applications.py)
- 实现 SignalConditioner 类
  - 信号放大 + 偏移
  - 电平移位
  - AC 耦合放大
  - 差分转单端
- 实现 SensorAmplifier 类
  - 热电偶放大器 (仪表放大器)
  - 应变片放大器 (惠斯通电桥)
  - 光电二极管 TIA
  - 压电传感器放大器
- 实现 AudioAmplifier 类
  - 前置放大器
  - Baxandall 音调控制
  - 功率驱动级
  - 分频器设计

#### 5. 测试
- tests/test_bjt.py: BJT 放大器测试 (含对比测试)
- tests/test_opamp.py: 运放电路测试
- tests/test_frequency.py: 频率响应测试
- tests/test_applications.py: 应用测试

#### 6. 示例
- examples/basic_amplifiers.py: BJT 放大器演示
- examples/opamp_circuits.py: 运放电路演示
- examples/frequency_response.py: 频率响应演示
- examples/applications_demo.py: 应用演示

#### 7. 文档
- docs/01_RESEARCH.md: 调研报告
- docs/02_REQUIREMENTS.md: 需求文档
- docs/03_DESIGN.md: 设计文档
- docs/04_PRODUCT.md: 产品文档
- docs/05_DEVELOPMENT.md: 开发日志

### 设计决策

1. **使用 dataclass 管理参数**: 简洁、类型安全、可序列化
2. **静态方法用于频率分析**: PhaseCompensation 和 StabilityAnalyzer 不需要实例状态
3. **统一的 summary() 接口**: 所有放大器类提供一致的参数摘要
4. **频率单位统一为 Hz**: 避免 rad/s 和 Hz 的混淆
5. **增益使用线性值**: _dB 后缀表示 dB 值

### 后续计划

- 添加 matplotlib 可视化工具 (波特图、波形图)
- 实现更多运放电路 (积分器、微分器、比较器)
- 添加噪声分析 (热噪声、1/f 噪声)
- 支持多级放大器级联分析
- 添加蒙特卡洛分析 (元件容差影响)
