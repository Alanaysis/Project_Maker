# 实现细节文档

## 1. 隶属函数实现

### 1.1 三角形隶属函数

**数学公式**：
```
μ(x) = max(0, min((x-a)/(b-a), (c-x)/(c-b)))
```

**实现要点**：
- 使用 NumPy 的向量化操作
- 处理边界情况（a=b 或 b=c）
- 支持标量和数组输入

**代码实现**：
```python
def __call__(self, x):
    x = np.asarray(x, dtype=float)
    result = np.zeros_like(x)

    # 上升段
    mask1 = (x >= self.a) & (x <= self.b)
    if self.b != self.a:
        result[mask1] = (x[mask1] - self.a) / (self.b - self.a)

    # 下降段
    mask2 = (x > self.b) & (x <= self.c)
    if self.c != self.b:
        result[mask2] = (self.c - x[mask2]) / (self.c - self.b)

    return result
```

### 1.2 梯形隶属函数

**数学公式**：
```
μ(x) = max(0, min((x-a)/(b-a), 1, (d-x)/(d-c)))
```

**实现要点**：
- 分为三段：上升段、平台段、下降段
- 使用掩码（mask）进行向量化计算

### 1.3 高斯隶属函数

**数学公式**：
```
μ(x) = exp(-(x - m)^2 / (2σ^2))
```

**实现要点**：
- 使用 NumPy 的 exp 函数
- 参数 σ 控制宽度，m 控制中心位置

## 2. 模糊化实现

### 2.1 模糊化过程

```python
def fuzzify(self, crisp_inputs):
    fuzzy_outputs = {}

    for var_name, crisp_value in crisp_inputs.items():
        fuzzy_outputs[var_name] = {}
        fuzzy_sets = self.input_variables[var_name]

        for set_name, fuzzy_set in fuzzy_sets.items():
            membership_value = fuzzy_set.membership(crisp_value)
            fuzzy_outputs[var_name][set_name] = membership_value

    return fuzzy_outputs
```

### 2.2 数据结构

输入变量以字典形式存储：
```python
{
    'variable_name': {
        'set_name': FuzzySet(...)
    }
}
```

## 3. 规则引擎实现

### 3.1 规则表示

每条规则包含：
- **前提 (antecedent)**：条件列表
- **结论 (consequent)**：输出列表
- **连接符 (operator)**：AND 或 OR
- **权重 (weight)**：0-1

### 3.2 规则评估

```python
def evaluate(self, fuzzy_inputs):
    activation_levels = []

    for var_name, set_name, operator in self.antecedent:
        membership = fuzzy_inputs[var_name][set_name]

        if operator == 'IS_NOT':
            membership = 1.0 - membership

        activation_levels.append(membership)

    # 使用连接符
    if self.operator == 'AND':
        activation = min(activation_levels)
    elif self.operator == 'OR':
        activation = max(activation_levels)

    return activation * self.weight
```

### 3.3 Mamdani 推理

**步骤**：
1. 计算每条规则的激活强度
2. 使用激活强度裁剪输出隶属函数
3. 聚合所有规则的输出（取最大值）

```python
def infer_mamdani(self, fuzzy_inputs, output_variables, x_range, num_points):
    # 计算规则激活
    rule_activations = []
    for rule in self.rules:
        activation = rule.evaluate(fuzzy_inputs)
        rule_activations.append((rule, activation))

    # 对每个输出变量
    for var_name, fuzzy_sets in output_variables.items():
        x = np.linspace(x_range[var_name][0], x_range[var_name][1], num_points)
        output_mf = np.zeros(num_points)

        # 应用每条规则
        for rule, activation in rule_activations:
            for rule_var, set_name in rule.consequent:
                if rule_var == var_name:
                    mf_values = fuzzy_sets[set_name].membership(x)
                    clipped = np.minimum(mf_values, activation)
                    output_mf = np.maximum(output_mf, clipped)

    return output_mf, x
```

### 3.4 Sugeno (TSK) 推理

**特点**：
- 结论部分是输入变量的线性函数，而非模糊集合
- 零阶 Sugeno: f = p0 (常数)
- 一阶 Sugeno: f = p0 + p1*x1 + p2*x2 + ...
- 去模糊化使用加权平均，计算更高效

**实现**：
```python
def infer_sugeno(self, fuzzy_inputs, crisp_inputs, sugeno_params):
    weighted_sum = 0.0
    weight_total = 0.0

    for i, rule in enumerate(self.rules):
        activation = rule.evaluate(fuzzy_inputs)

        # 计算规则输出
        for var_name, params_list in sugeno_params.items():
            params = params_list[i]
            output_value = params[0]  # p0
            input_values = list(crisp_inputs.values())
            for j in range(1, len(params)):
                output_value += params[j] * input_values[j-1]

        weighted_sum += activation * output_value
        weight_total += activation

    # 加权平均去模糊化
    if weight_total == 0:
        return 0.0

    return weighted_sum / weight_total
```

## 4. 去模糊化实现

### 4.1 重心法 (COG)

**数学公式**：
```
x* = ∫(x * μ(x)) dx / ∫ μ(x) dx
```

**实现**：
```python
def _center_of_gravity(self, x, mf_values):
    numerator = np.sum(x * mf_values)
    denominator = np.sum(mf_values)

    if denominator == 0:
        return np.mean(x)

    return numerator / denominator
```

### 4.2 最大隶属度法 (MOM)

**实现**：
```python
def _mean_of_maximum(self, x, mf_values):
    max_mf = np.max(mf_values)

    if max_mf == 0:
        return np.mean(x)

    max_indices = np.where(mf_values == max_mf)[0]
    return np.mean(x[max_indices])
```

## 5. 控制器集成

### 5.1 完整控制流程

```python
def control(self, crisp_inputs, output_x_ranges, num_points=100):
    # 步骤1: 模糊化
    fuzzy_inputs = self.fuzzifier.fuzzify(crisp_inputs)

    # 步骤2: 规则推理
    fuzzy_outputs, x = self.rule_engine.infer_mamdani(
        fuzzy_inputs, self.output_variables, output_x_ranges, num_points
    )

    # 步骤3: 去模糊化
    crisp_outputs = {}
    for var_name, mf_values in fuzzy_outputs.items():
        crisp_outputs[var_name] = self.defuzzifier.defuzzify(x, mf_values)

    return crisp_outputs
```

### 5.2 逐步执行（调试用）

`control_step_by_step` 方法返回每一步的中间结果：
- 模糊化结果
- 规则激活强度
- 模糊输出
- 精确输出

## 6. 性能优化

### 6.1 向量化计算

使用 NumPy 的向量化操作替代循环：
```python
# 不推荐
for i in range(len(x)):
    result[i] = some_function(x[i])

# 推荐
result = some_function(x)
```

### 6.2 避免重复计算

- 缓存隶属函数的参数
- 预计算论域网格

### 6.3 内存优化

- 使用原地操作（如 `np.minimum` 的 out 参数）
- 避免创建不必要的中间数组

## 7. 错误处理

### 7.1 输入验证

- 检查输入变量是否已定义
- 检查模糊集合是否存在
- 验证论域范围的有效性

### 7.2 边界情况

- 零隶属度的处理
- 空规则集的处理
- 论域范围为零的处理

## 8. 实际应用实现

### 8.1 温度控制器 (TemperatureController)

**输入变量**：
- `error`: 温度误差 (设定值 - 实际值), 范围 [-20, 20]°C
- `change`: 误差变化率, 范围 [-10, 10]°C/s

**输出变量**：
- `power`: 加热器功率, 范围 [-100, 100]%

**模糊集合**：
- error: negative_big, negative_small, zero, positive_small, positive_big
- change: negative, zero, positive
- power: cool_strong, cool_weak, off, heat_weak, heat_strong

**规则库**: 5x3 = 15 条规则

### 8.2 速度控制器 (SpeedController)

**输入变量**：
- `error`: 速度误差 (设定值 - 实际值), 范围 [-50, 50] km/h
- `change`: 误差变化率, 范围 [-20, 20] km/h/s

**输出变量**：
- `throttle`: 油门/驱动量, 范围 [-100, 100]%

**模糊集合**：
- error: negative_big, negative_small, zero, positive_small, positive_big
- change: negative, zero, positive
- throttle: brake_strong, brake_weak, coast, accel_weak, accel_strong

**规则库**: 5x3 = 15 条规则

## 9. 测试策略

### 8.1 单元测试

- 每个隶属函数的正确性
- 模糊化的准确性
- 规则评估的正确性
- 去模糊化的精度

### 8.2 集成测试

- 完整控制流程
- 多输入多输出场景
- 边界条件测试

### 8.3 性能测试

- 大量规则的推理速度
- 高精度论域的计算时间
