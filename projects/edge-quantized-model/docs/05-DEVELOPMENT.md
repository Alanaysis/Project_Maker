# 开发手册

## 1. 环境搭建

### 1.1 系统要求

- **操作系统**：Ubuntu 20.04+ / macOS 12+ / Windows 10+
- **Python**：3.8+
- **C++编译器**：GCC 9+ / Clang 12+ / MSVC 2019+
- **CMake**：3.16+

### 1.2 Python 环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

**requirements.txt 内容**：

```txt
numpy>=1.21.0
torch>=2.0.0
onnx>=1.14.0
onnxruntime>=1.15.0
matplotlib>=3.5.0
tqdm>=4.62.0
pyyaml>=6.0
```

### 1.3 C++ 环境（可选）

```bash
# 安装依赖
sudo apt-get install build-essential cmake

# 编译
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 1.4 IDE 配置

#### VS Code

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "C_Cpp.default.cppStandard": "c++17"
}
```

#### PyCharm

1. 打开项目目录
2. 配置 Python 解释器：`venv/bin/python`
3. 配置代码风格：PEP 8

## 2. 项目结构详解

```
edge-quantized-model/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记模板
├── requirements.txt             # Python 依赖
├── setup.py                     # 安装配置
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-REQUIREMENTS.md      # 需求分析
│   ├── 03-DESIGN.md            # 技术设计
│   ├── 04-PRODUCT.md           # 产品思维
│   └── 05-DEVELOPMENT.md       # 开发手册
├── src/                         # 源代码
│   ├── __init__.py
│   ├── quantization/           # 量化模块
│   │   ├── __init__.py
│   │   ├── quantizer.py        # 量化器主类
│   │   ├── calibration.py      # 校准算法
│   │   ├── quant_ops.py        # 量化算子
│   │   └── utils.py            # 工具函数
│   ├── inference/              # 推理模块
│   │   ├── __init__.py
│   │   ├── engine.py           # 推理引擎
│   │   ├── graph.py            # 计算图
│   │   ├── executor.py         # 执行器
│   │   └── memory.py           # 内存管理
│   ├── operators/              # 算子实现
│   │   ├── __init__.py
│   │   ├── conv.py             # 卷积算子
│   │   ├── linear.py           # 全连接算子
│   │   ├── activation.py       # 激活函数
│   │   └── fusion.py           # 算子融合
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── logger.py           # 日志
│       ├── profiler.py         # 性能分析
│       └── config.py           # 配置管理
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_quantization.py    # 量化测试
│   ├── test_inference.py       # 推理测试
│   ├── test_operators.py       # 算子测试
│   └── test_fusion.py          # 融合测试
├── examples/                    # 示例目录
│   ├── automotive/             # 车载场景
│   │   ├── object_detection_demo.py
│   │   └── benchmark_demo.py
│   └── basic/                  # 基础示例
│       ├── simple_quantize.py
│       └── simple_inference.py
├── configs/                     # 配置文件
│   ├── quant_config.yaml       # 量化配置
│   └── inference_config.yaml   # 推理配置
├── scripts/                     # 脚本工具
│   ├── run_tests.sh            # 运行测试
│   └── run_benchmark.sh        # 运行基准测试
└── benchmarks/                  # 基准测试
    ├── run_benchmark.py
    └── results/
```

## 3. 核心模块解析

### 3.1 量化模块 (src/quantization/)

#### quantizer.py - 量化器主类

```python
"""
量化器主类

负责协调整个量化流程：
1. 加载模型
2. 校准激活值
3. 计算量化参数
4. 量化模型权重
5. 导出量化模型
"""

class Quantizer:
    """量化器"""

    def __init__(self, config: QuantConfig):
        self.config = config
        self.calibrator = CalibratorFactory.create(config.calibration_method)

    def quantize(self, model, calibration_data):
        """执行量化"""
        # 1. 校准
        calibration_stats = self.calibrate(model, calibration_data)

        # 2. 计算量化参数
        quant_params = self.compute_quant_params(calibration_stats)

        # 3. 量化模型
        quant_model = self.quantize_model(model, quant_params)

        return quant_model
```

**⭐ 重点**：
- 理解量化流程的各个阶段
- 掌握校准方法的选择策略
- 理解量化参数的计算方式

**💡 思考**：
- 为什么需要校准数据？
- 如何选择合适的校准方法？
- 量化参数如何影响精度？

#### calibration.py - 校准算法

```python
"""
校准算法实现

支持的校准方法：
1. MinMax：使用激活值的最小最大值
2. Percentile：使用百分位数
3. Entropy：使用 KL 散度最小化
"""

class MinMaxCalibration:
    """MinMax 校准"""

    def calibrate(self, activations):
        min_val = np.min(activations)
        max_val = np.max(activations)
        return min_val, max_val

class PercentileCalibration:
    """百分位校准"""

    def __init__(self, percentile=99.99):
        self.percentile = percentile

    def calibrate(self, activations):
        min_val = np.percentile(activations, 100 - self.percentile)
        max_val = np.percentile(activations, self.percentile)
        return min_val, max_val

class EntropyCalibration:
    """熵校准 (KL 散度)"""

    def calibrate(self, activations, num_bins=2048):
        # 计算激活值分布
        # 寻找最优阈值
        # 最小化 KL 散度
        pass
```

**⭐ 重点**：
- 理解不同校准方法的原理
- 掌握 KL 散度的计算方式
- 理解校准对精度的影响

**💡 思考**：
- MinMax 和 Percentile 的区别？
- 为什么 Entropy 校准通常更好？
- 如何选择合适的百分位数？

### 3.2 推理模块 (src/inference/)

#### engine.py - 推理引擎

```python
"""
推理引擎

负责：
1. 加载量化模型
2. 构建计算图
3. 执行推理
4. 返回结果
"""

class InferenceEngine:
    """推理引擎"""

    def __init__(self, model_path, config=None):
        self.config = config or InferenceConfig()
        self.graph = self.load_model(model_path)
        self.executor = Executor(self.graph)

    def inference(self, input_data):
        """执行推理"""
        # 预处理
        processed_input = self.preprocess(input_data)

        # 执行
        output = self.executor.execute(processed_input)

        # 后处理
        result = self.postprocess(output)

        return result
```

**⭐ 重点**：
- 理解推理引擎的架构
- 掌握计算图的构建方式
- 理解执行器的工作原理

**💡 思考**：
- 推理引擎如何优化性能？
- 如何管理内存使用？
- 如何支持多种硬件后端？

#### graph.py - 计算图

```python
"""
计算图实现

负责：
1. 表示模型结构
2. 管理节点依赖
3. 提供拓扑排序
4. 支持图优化
"""

class ComputeGraph:
    """计算图"""

    def __init__(self):
        self.nodes = {}
        self.inputs = []
        self.outputs = []

    def add_node(self, node):
        """添加节点"""
        self.nodes[node.name] = node

    def topological_sort(self):
        """拓扑排序"""
        # 使用 Kahn 算法或 DFS
        pass

    def optimize(self):
        """图优化"""
        # 应用优化 Pass
        pass
```

**⭐ 重点**：
- 理解计算图的表示方式
- 掌握拓扑排序算法
- 理解图优化的作用

### 3.3 算子模块 (src/operators/)

#### conv.py - 卷积算子

```python
"""
卷积算子实现

支持：
- 普通卷积
- 量化卷积
- 深度可分离卷积
"""

class Conv2dOperator:
    """卷积算子"""

    def execute(self, inputs, params):
        # 获取输入
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias')

        # 执行卷积
        output = self.conv2d(x, weight, bias, params)

        return {'output': output}

    def conv2d(self, x, weight, bias, params):
        """卷积计算"""
        # 使用 im2col + GEMM 实现
        pass
```

**⭐ 重点**：
- 理解卷积的计算过程
- 掌握 im2col 优化技术
- 理解量化卷积的实现

**💡 思考**：
- im2col 如何优化卷积计算？
- 量化卷积如何保持精度？
- 如何实现高效卷积？

#### fusion.py - 算子融合

```python
"""
算子融合实现

支持的融合模式：
- Conv + BN
- Conv + BN + ReLU
- Linear + ReLU
"""

class OperatorFusion:
    """算子融合"""

    def fuse_conv_bn(self, conv_params, bn_params):
        """融合 Conv 和 BN"""
        # 融合公式
        scale = bn_params['gamma'] / np.sqrt(bn_params['var'] + 1e-5)
        fused_weight = conv_params['weight'] * scale.reshape(-1, 1, 1, 1)
        fused_bias = (conv_params['bias'] - bn_params['mean']) * scale + bn_params['beta']

        return fused_weight, fused_bias

    def fuse_conv_bn_relu(self, conv_params, bn_params, relu=True):
        """融合 Conv + BN + ReLU"""
        fused_weight, fused_bias = self.fuse_conv_bn(conv_params, bn_params)

        if relu:
            # ReLU 可以直接应用
            pass

        return fused_weight, fused_bias
```

**⭐ 重点**：
- 理解算子融合的原理
- 掌握 Conv+BN 融合公式
- 理解融合对性能的提升

**💡 思考**：
- 为什么 Conv+BN 可以融合？
- 融合如何减少计算量？
- 还有哪些算子可以融合？

## 4. 开发流程

### 4.1 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/quantization

# 开发功能
# ...

# 提交代码
git add .
git commit -m "feat: 实现 INT8 量化功能"

# 推送分支
git push origin feature/quantization

# 创建 Pull Request
# ...

# 合并到主分支
git checkout main
git merge feature/quantization
```

### 4.2 代码规范

#### Python 代码规范

```python
# 遵循 PEP 8
# 使用类型注解
# 编写文档字符串

def quantize_tensor(
    tensor: np.ndarray,
    scale: float,
    zero_point: int,
    num_bits: int = 8
) -> np.ndarray:
    """
    量化张量

    Args:
        tensor: 输入张量
        scale: 缩放因子
        zero_point: 零点
        num_bits: 量化位数

    Returns:
        量化后的张量
    """
    # 实现
    pass
```

#### C++ 代码规范

```cpp
// 使用 Google C++ 风格
// 使用命名空间
// 编写注释

namespace edge_quant {

class Quantizer {
public:
    /**
     * @brief 量化张量
     * @param tensor 输入张量
     * @param scale 缩放因子
     * @param zero_point 零点
     * @return 量化后的张量
     */
    Tensor Quantize(const Tensor& tensor, float scale, int zero_point);

private:
    // 成员变量
};

}  // namespace edge_quant
```

### 4.3 测试规范

```python
# tests/test_quantization.py

import pytest
from src.quantization import Quantizer, QuantConfig

class TestQuantizer:
    """量化器测试"""

    def test_symmetric_quantization(self):
        """测试对称量化"""
        config = QuantConfig(symmetric=True)
        quantizer = Quantizer(config)

        # 测试数据
        tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # 执行量化
        quant_tensor, scale, zero_point = quantizer.quantize_tensor(tensor)

        # 验证
        assert scale > 0
        assert zero_point == 0  # 对称量化零点为0

    def test_asymmetric_quantization(self):
        """测试非对称量化"""
        config = QuantConfig(symmetric=False)
        quantizer = Quantizer(config)

        # 测试数据
        tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # 执行量化
        quant_tensor, scale, zero_point = quantizer.quantize_tensor(tensor)

        # 验证
        assert scale > 0

    def test_quantization_accuracy(self):
        """测试量化精度"""
        config = QuantConfig(quant_type="int8")
        quantizer = Quantizer(config)

        # 测试数据
        tensor = np.random.randn(100, 100)

        # 量化再反量化
        quant_tensor, scale, zero_point = quantizer.quantize_tensor(tensor)
        dequant_tensor = quantizer.dequantize_tensor(quant_tensor, scale, zero_point)

        # 计算误差
        error = np.mean(np.abs(tensor - dequant_tensor))

        # 验证误差在可接受范围内
        assert error < 0.1  # 误差小于 0.1
```

## 5. 调试技巧

### 5.1 日志调试

```python
# 配置日志
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 使用日志
logger.debug("调试信息")
logger.info("运行信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 5.2 性能分析

```python
# 使用 cProfile
import cProfile

def function_to_profile():
    # 要分析的函数
    pass

cProfile.run('function_to_profile()')

# 使用 line_profiler
# pip install line_profiler
# kernprof -l -v script.py
```

### 5.3 内存分析

```python
# 使用 memory_profiler
# pip install memory_profiler

from memory_profiler import profile

@profile
def function_to_profile():
    # 要分析的函数
    pass

# 运行
# python -m memory_profiler script.py
```

## 6. 部署流程

### 6.1 打包发布

```bash
# 安装打包工具
pip install build twine

# 构建包
python -m build

# 上传到 PyPI
twine upload dist/*
```

### 6.2 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "examples/automotive/object_detection_demo.py"]
```

## 7. 常见问题

### 7.1 量化精度下降严重

**可能原因**：
- 校准数据不具代表性
- 量化参数计算错误
- 存在异常值

**解决方案**：
- 增加校准数据量和多样性
- 检查量化参数计算逻辑
- 使用 Percentile 校准排除异常值

### 7.2 推理速度慢

**可能原因**：
- 未进行算子融合
- 内存分配频繁
- 未使用并行计算

**解决方案**：
- 启用算子融合优化
- 使用内存池减少分配开销
- 使用多线程并行执行

### 7.3 内存占用高

**可能原因**：
- 未释放中间结果
- 内存碎片化
- 缓存策略不合理

**解决方案**：
- 及时释放不需要的张量
- 使用内存池管理
- 优化缓存策略

## 8. 参考资源

### 8.1 官方文档

- [PyTorch 量化文档](https://pytorch.org/docs/stable/quantization.html)
- [ONNX 文档](https://onnx.ai/onnx/)
- [NumPy 文档](https://numpy.org/doc/)

### 8.2 学习资源

- [量化感知训练教程](https://pytorch.org/tutorials/advanced/static_quantization_tutorial.html)
- [ONNX 量化工具](https://github.com/microsoft/onnxruntime/tree/main/onnxruntime/python/tools/quantization)
- [模型优化最佳实践](https://pytorch.org/tutorials/recipes/recipes/quantization.html)

### 8.3 工具推荐

- **VS Code**：代码编辑器
- **PyCharm**：Python IDE
- **Git**：版本控制
- **Docker**：容器化部署
