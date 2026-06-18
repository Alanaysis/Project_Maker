# 技术设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户接口层 (Python API)                    │
├─────────────────────────────────────────────────────────────┤
│                    量化工具链 (Python)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 模型解析 │  │ 量化校准 │  │ 量化转换 │  │ 精度评估 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    推理引擎 (C++)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 模型加载 │  │ 图优化   │  │ 算子执行 │  │ 内存管理 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    硬件抽象层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ CPU 后端 │  │ GPU 后端 │  │ NPU 后端 │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
edge-quantized-model/
├── src/
│   ├── quantization/          # 量化模块
│   │   ├── quantizer.py       # 量化器主类
│   │   ├── calibration.py     # 校准算法
│   │   ├── quant_ops.py       # 量化算子
│   │   └── utils.py           # 工具函数
│   ├── inference/             # 推理模块
│   │   ├── engine.py          # 推理引擎
│   │   ├── graph.py           # 计算图
│   │   ├── executor.py        # 执行器
│   │   └── memory.py          # 内存管理
│   ├── operators/             # 算子实现
│   │   ├── conv.py            # 卷积算子
│   │   ├── linear.py          # 全连接算子
│   │   ├── activation.py      # 激活函数
│   │   └── fusion.py          # 算子融合
│   └── utils/                 # 工具模块
│       ├── logger.py          # 日志
│       ├── profiler.py        # 性能分析
│       └── config.py          # 配置管理
├── tests/                     # 测试
├── examples/                  # 示例
└── benchmarks/                # 基准测试
```

## 2. 核心数据结构

### 2.1 量化参数

```python
@dataclass
class QuantParams:
    """量化参数"""
    scale: np.ndarray      # 缩放因子
    zero_point: np.ndarray # 零点
    num_bits: int          # 量化位数
    symmetric: bool        # 是否对称量化
    per_channel: bool      # 是否逐通道量化
    channel_axis: int      # 通道轴
```

### 2.2 量化张量

```python
@dataclass
class QuantizedTensor:
    """量化张量"""
    data: np.ndarray       # 量化后的数据
    params: QuantParams    # 量化参数
    dtype: np.dtype        # 数据类型 (int8, int4)

    def dequantize(self) -> np.ndarray:
        """反量化"""
        return self.data.astype(np.float32) * self.params.scale + self.params.zero_point
```

### 2.3 计算图节点

```python
@dataclass
class GraphNode:
    """计算图节点"""
    name: str              # 节点名称
    op_type: str           # 算子类型
    inputs: List[str]      # 输入名称列表
    outputs: List[str]     # 输出名称列表
    params: Dict           # 算子参数
    quant_params: Optional[QuantParams]  # 量化参数
```

### 2.4 计算图

```python
class ComputeGraph:
    """计算图"""
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.topo_order: List[str] = []

    def add_node(self, node: GraphNode):
        """添加节点"""
        self.nodes[node.name] = node

    def topological_sort(self) -> List[str]:
        """拓扑排序"""
        # 实现拓扑排序算法
        pass
```

## 3. 核心算法设计

### 3.1 INT8 量化算法

#### 对称量化

```
量化公式：
q = round(x / scale)

反量化公式：
x ≈ q * scale

缩放因子计算：
scale = max(|x|) / (2^(bits-1) - 1)
```

#### 非对称量化

```
量化公式：
q = round(x / scale) + zero_point

反量化公式：
x ≈ (q - zero_point) * scale

缩放因子计算：
scale = (max(x) - min(x)) / (2^bits - 1)
zero_point = round(-min(x) / scale)
```

### 3.2 校准算法

#### MinMax 校准

```python
def minmax_calibration(activations: List[np.ndarray]) -> Tuple[float, float]:
    """MinMax 校准"""
    min_val = min(act.min() for act in activations)
    max_val = max(act.max() for act in activations)
    return min_val, max_val
```

#### Percentile 校准

```python
def percentile_calibration(
    activations: List[np.ndarray],
    percentile: float = 99.99
) -> Tuple[float, float]:
    """百分位校准"""
    all_vals = np.concatenate([act.flatten() for act in activations])
    min_val = np.percentile(all_vals, 100 - percentile)
    max_val = np.percentile(all_vals, percentile)
    return min_val, max_val
```

#### Entropy 校准

```python
def entropy_calibration(
    activations: List[np.ndarray],
    num_bins: int = 2048
) -> Tuple[float, float]:
    """熵校准 (KL 散度)"""
    # 计算激活值分布
    # 寻找最优阈值，最小化 KL 散度
    pass
```

### 3.3 算子融合算法

#### Conv + BN 融合

```python
def fuse_conv_bn(conv_weight, conv_bias, bn_mean, bn_var, bn_weight, bn_bias, eps=1e-5):
    """融合 Conv 和 BN"""
    # BN 参数
    gamma = bn_weight
    beta = bn_bias
    mean = bn_mean
    var = bn_var

    # 融合公式
    scale = gamma / np.sqrt(var + eps)
    fused_weight = conv_weight * scale.reshape(-1, 1, 1, 1)
    fused_bias = (conv_bias - mean) * scale + beta

    return fused_weight, fused_bias
```

#### Conv + BN + ReLU 融合

```python
def fuse_conv_bn_relu(conv_weight, conv_bias, bn_params, relu=True):
    """融合 Conv + BN + ReLU"""
    fused_weight, fused_bias = fuse_conv_bn(conv_weight, conv_bias, **bn_params)

    if relu:
        # ReLU 可以直接应用，不需要额外参数
        # 在执行时处理
        pass

    return fused_weight, fused_bias
```

## 4. 推理引擎设计

### 4.1 模型加载

```python
class ModelLoader:
    """模型加载器"""

    def load_onnx(self, path: str) -> ComputeGraph:
        """加载 ONNX 模型"""
        import onnx
        model = onnx.load(path)
        return self._convert_to_graph(model)

    def _convert_to_graph(self, onnx_model) -> ComputeGraph:
        """转换为计算图"""
        graph = ComputeGraph()
        # 解析 ONNX 模型，构建计算图
        return graph
```

### 4.2 内存管理

```python
class MemoryPool:
    """内存池"""

    def __init__(self, size: int):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.uint8)
        self.allocated = {}  # name -> (offset, size)
        self.free_list = [(0, size)]

    def allocate(self, name: str, size: int, dtype: np.dtype) -> np.ndarray:
        """分配内存"""
        # 查找合适的空闲块
        offset = self._find_free_block(size)
        if offset is None:
            raise MemoryError("内存不足")

        self.allocated[name] = (offset, size)
        return self.buffer[offset:offset+size].view(dtype)

    def free(self, name: str):
        """释放内存"""
        if name in self.allocated:
            offset, size = self.allocated.pop(name)
            self.free_list.append((offset, size))
            self._merge_free_blocks()
```

### 4.3 执行器

```python
class Executor:
    """执行器"""

    def __init__(self, graph: ComputeGraph, memory_pool: MemoryPool):
        self.graph = graph
        self.memory_pool = memory_pool
        self.operators = {}

    def register_operator(self, op_type: str, op_impl):
        """注册算子"""
        self.operators[op_type] = op_impl

    def execute(self, inputs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """执行计算图"""
        # 按拓扑序执行
        for node_name in self.graph.topo_order:
            node = self.graph.nodes[node_name]
            op = self.operators[node.op_type]

            # 获取输入
            node_inputs = {
                inp: self._get_tensor(inp) for inp in node.inputs
            }

            # 执行算子
            outputs = op.execute(node_inputs, node.params)

            # 保存输出
            for out_name, out_data in outputs.items():
                self._set_tensor(out_name, out_data)

        # 返回输出
        return {
            out: self._get_tensor(out) for out in self.graph.outputs
        }
```

## 5. 算子设计

### 5.1 算子接口

```python
class Operator(ABC):
    """算子基类"""

    @abstractmethod
    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict
    ) -> Dict[str, np.ndarray]:
        """执行算子"""
        pass

    @abstractmethod
    def compute_output_shape(
        self,
        input_shapes: List[Tuple],
        params: Dict
    ) -> Tuple:
        """计算输出形状"""
        pass
```

### 5.2 量化卷积算子

```python
class QuantizedConv2d(Operator):
    """量化卷积算子"""

    def execute(self, inputs, params):
        # 获取输入
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias', None)

        # 量化参数
        x_scale = params['x_scale']
        x_zero_point = params['x_zero_point']
        w_scale = params['w_scale']
        w_zero_point = params['w_zero_point']

        # 量化输入
        x_q = np.clip(np.round(x / x_scale) + x_zero_point, -128, 127).astype(np.int8)

        # 量化权重
        w_q = np.clip(np.round(weight / w_scale) + w_zero_point, -128, 127).astype(np.int8)

        # 整数卷积
        # 使用 im2col + GEMM 实现
        output_q = self._int8_conv2d(x_q, w_q, params)

        # 反量化
        output = (output_q.astype(np.float32) - x_zero_point * w_zero_point) * x_scale * w_scale

        if bias is not None:
            output += bias

        return {'output': output}
```

## 6. 性能优化设计

### 6.1 算子融合策略

```python
class FusionPass:
    """融合优化 Pass"""

    def __init__(self):
        self.patterns = [
            (['Conv', 'BatchNormalization'], self.fuse_conv_bn),
            (['Conv', 'BatchNormalization', 'Relu'], self.fuse_conv_bn_relu),
            (['Linear', 'Relu'], self.fuse_linear_relu),
        ]

    def run(self, graph: ComputeGraph) -> ComputeGraph:
        """执行融合优化"""
        for pattern, fusion_func in self.patterns:
            graph = self._apply_pattern(graph, pattern, fusion_func)
        return graph
```

### 6.2 内存优化

```python
class MemoryOptimizer:
    """内存优化器"""

    def optimize(self, graph: ComputeGraph) -> ComputeGraph:
        """优化内存使用"""
        # 1. 计算张量生命周期
        lifetimes = self._compute_lifetimes(graph)

        # 2. 内存复用
        self._reuse_memory(graph, lifetimes)

        # 3. 内存布局优化
        self._optimize_layout(graph)

        return graph
```

## 7. 配置系统设计

### 7.1 配置结构

```python
@dataclass
class QuantConfig:
    """量化配置"""
    quant_type: str = "int8"           # 量化类型
    calibration_method: str = "percentile"  # 校准方法
    calibration_percentile: float = 99.99   # 百分位数
    per_channel: bool = True           # 逐通道量化
    symmetric: bool = True             # 对称量化
    num_calibration_samples: int = 100 # 校准样本数

@dataclass
class InferenceConfig:
    """推理配置"""
    backend: str = "cpu"               # 推理后端
    num_threads: int = 4               # 线程数
    memory_pool_size: str = "512MB"    # 内存池大小
    enable_profiling: bool = False     # 性能分析
```

## 8. 错误处理设计

### 8.1 异常类型

```python
class QuantizationError(Exception):
    """量化错误"""
    pass

class InferenceError(Exception):
    """推理错误"""
    pass

class UnsupportedOperatorError(QuantizationError):
    """不支持的算子"""
    pass

class CalibrationError(QuantizationError):
    """校准错误"""
    pass
```

### 8.2 错误处理策略

```python
def safe_quantize(model, config):
    """安全量化"""
    try:
        return quantize(model, config)
    except UnsupportedOperatorError as e:
        logger.warning(f"算子 {e.op_type} 不支持量化，跳过")
        return quantize(model, config, skip_ops=[e.op_type])
    except CalibrationError as e:
        logger.error(f"校准失败: {e}")
        raise
```

## 9. 扩展性设计

### 9.1 后端扩展

```python
class Backend(ABC):
    """后端基类"""

    @abstractmethod
    def create_context(self) -> Any:
        """创建执行上下文"""
        pass

    @abstractmethod
    def execute_op(self, op, inputs, params) -> Any:
        """执行算子"""
        pass

class CPUBackend(Backend):
    """CPU 后端"""
    pass

class CUDABackend(Backend):
    """CUDA 后端"""
    pass
```

### 9.2 算子扩展

```python
class OperatorRegistry:
    """算子注册表"""

    _registry = {}

    @classmethod
    def register(cls, op_type: str):
        """注册算子"""
        def decorator(op_class):
            cls._registry[op_type] = op_class
            return op_class
        return decorator

    @classmethod
    def get(cls, op_type: str) -> Type[Operator]:
        """获取算子"""
        return cls._registry.get(op_type)
```

## 10. 测试策略

### 10.1 单元测试

- 量化算子测试
- 校准算法测试
- 算子融合测试
- 内存管理测试

### 10.2 集成测试

- 端到端量化流程测试
- 推理引擎测试
- 性能基准测试

### 10.3 精度测试

- 量化精度对比测试
- 不同校准方法对比
- 边界条件测试
