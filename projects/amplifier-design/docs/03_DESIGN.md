# 放大器设计 - 设计文档

## 1. 架构设计

### 1.1 模块划分

```
amplifier-design/
├── src/
│   ├── bjt.py           # BJT 基本放大器
│   ├── opamp.py         # 运算放大器电路
│   ├── frequency.py     # 频率响应分析
│   └── applications.py  # 实际应用
```

### 1.2 依赖关系

```
applications.py
    ├── opamp.py (InstrumentationAmp, NonInvertingAmp, InvertingAmp)
    └── numpy

frequency.py
    └── numpy

opamp.py
    └── numpy

bjt.py
    └── numpy
```

## 2. BJT 放大器设计

### 2.1 类设计

```
BJTParams (dataclass)
├── beta, V_A, V_BE, V_T
├── transconductance(I_C) -> float
├── r_pi_from_ic(I_C) -> float
└── output_resistance(I_C) -> float

CommonEmitter
├── R_B1, R_B2, R_C, R_E, V_CC
├── operating_point() -> dict
├── voltage_gain(R_L) -> float
├── input_impedance() -> float
├── output_impedance() -> float
└── summary() -> dict

CommonCollector
├── R_B1, R_B2, R_E, V_CC
├── operating_point() -> dict
├── voltage_gain(R_L) -> float
├── input_impedance(R_L) -> float
├── output_impedance(R_s) -> float
└── summary() -> dict

CommonBase
├── R_E, R_C, V_CC, I_C_bias
├── operating_point() -> dict
├── voltage_gain(R_L) -> float
├── input_impedance() -> float
├── output_impedance() -> float
└── summary() -> dict
```

### 2.2 计算公式

**共射放大器**:
- V_B = V_CC × R_B2 / (R_B1 + R_B2)
- V_E = V_B - V_BE
- I_C ≈ V_E / R_E
- g_m = I_C / V_T
- Av = -g_m × (R_C || r_o || R_L)
- Z_in = R_B || r_pi
- Z_out = R_C || r_o

**共集放大器**:
- Av = g_m × (R_E || R_L) / (1 + g_m × (R_E || R_L))
- Z_in = R_B || (r_pi + (β+1) × (R_E || R_L))
- Z_out = R_E || ((R_s || R_B) + r_pi) / (β+1)

**共基放大器**:
- Av = g_m × (R_C || r_o || R_L)
- Z_in = R_E || (r_pi / (β+1))
- Z_out = R_C || r_o

## 3. 运放电路设计

### 3.1 类设计

```
OpAmpParams (dataclass)
├── A_OL, GBW, SR, V_sat
├── I_bias, V_os, CMRR, PSRR
├── CMRR_linear -> float
└── PSRR_linear -> float

InvertingAmp
├── R_in, R_f, opamp
├── gain() -> float                  # -Rf/Rin
├── gain_with_loading() -> float     # 考虑有限 A_OL
├── input_impedance() -> float       # Rin
├── output_impedance() -> float
├── bandwidth() -> float             # GBW / |Av|
├── max_output_swing(freq) -> float  # SR 限制
├── transfer_function(f) -> ndarray  # 频率响应
└── summary() -> dict

NonInvertingAmp
├── R_in, R_f, opamp
├── gain() -> float                  # 1 + Rf/Rin
├── gain_with_loading() -> float
├── input_impedance() -> float       # 非常高
├── bandwidth() -> float
├── transfer_function(f) -> ndarray
└── summary() -> dict

DifferentialAmp
├── R1, R_f, R2, R_g, opamp
├── differential_gain() -> float     # Rf/R1
├── common_mode_gain() -> float      # 取决于匹配
├── cmrr() -> float
├── output(V1, V2) -> float
└── summary() -> dict

InstrumentationAmp
├── R1, R_g, R2..R5, opamp
├── gain() -> float                  # 1 + 2R1/Rg
├── set_gain(gain) -> None
├── output(V1, V2) -> float
├── bandwidth() -> float
└── summary() -> dict
```

### 3.2 传递函数模型

反相放大器一阶模型：
```
H(s) = (-Rf/Rin) / (1 + s/ωp)
ωp = 2π × GBW / (1 + |Av|)
```

同相放大器一阶模型：
```
H(s) = (1 + Rf/Rin) / (1 + s/ωp)
ωp = 2π × GBW / (1 + Rf/Rin)
```

## 4. 频率响应设计

### 4.1 GainBandwidthProduct 类

核心方法：
- `bandwidth_at_gain(gain)`: BW = GBW / |Av|
- `gain_at_bandwidth(bw)`: |Av| = GBW / BW
- `gain_db_at_frequency(gain, f)`: 单极点幅频响应
- `phase_at_frequency(gain, f)`: 单极点相频响应

### 4.2 PhaseCompensation 类

静态方法：
- `dominant_pole_compensation()`: 主极点补偿参数计算
- `lead_compensation()`: 超前补偿网络参数
- `lag_compensation()`: 滞后补偿参数
- `miller_compensation()`: 密勒补偿参数

### 4.3 StabilityAnalyzer 类

静态方法：
- `loop_gain_tf()`: 创建环路增益传递函数
- `phase_margin()`: 计算相位裕度和增益裕度
- `step_response_params()`: 估算阶跃响应参数

## 5. 应用层设计

### 5.1 SignalConditioner

- `process(signal)`: 放大 + 偏移
- `level_shift(signal, shift)`: 电平移位
- `ac_coupled_amplify(signal, f_cutoff, fs)`: AC耦合放大
- `differential_to_single(v_pos, v_neg)`: 差分转单端

### 5.2 SensorAmplifier

- `thermocouple_amp(R_g)`: 热电偶放大
- `strain_gauge_amp(R_gauge, R_g)`: 应变片放大
- `photodiode_amp(R_f, C_f)`: 光电二极管 TIA
- `piezo_amp(R_f)`: 压电传感器放大

### 5.3 AudioAmplifier

- `preamp(R_in, R_f)`: 前置放大
- `tone_control()`: Baxandall 音调控制
- `baxandall_response(f)`: 音调控制频率响应
- `power_amp_driver()`: 功率驱动级
- `crossover_network()`: 分频器设计

## 6. 接口规范

### 6.1 统一接口

所有放大器类提供：
- `gain()` 或等效方法: 增益计算
- `summary() -> dict`: 完整参数摘要

### 6.2 返回格式

summary() 返回 dict，包含：
- `type`: 放大器类型名称
- 增益/带宽等关键参数
- 工作点信息 (BJT)
- 频率响应参数 (运放)

### 6.3 频率参数

所有频率以 Hz 为单位 (非 rad/s)。
增益使用线性值 (非 dB)，除非明确标注 _dB。
