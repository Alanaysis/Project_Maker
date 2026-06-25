# 开发指南

## 1. 开发环境搭建

### 1.1 系统要求

- **操作系统**: Linux / macOS / Windows
- **Python**: 3.8 或更高版本
- **内存**: 建议 8GB+
- **存储**: 至少 1GB 可用空间

### 1.2 环境配置

#### 使用 venv

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 使用 conda

```bash
# 创建环境
conda create -n table-recognition python=3.9

# 激活环境
conda activate table-recognition

# 安装依赖
pip install -r requirements.txt
```

### 1.3 IDE 配置

#### VS Code

推荐插件：
- Python
- Pylance
- Python Test Explorer
- GitLens

设置文件 (.vscode/settings.json):

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

#### PyCharm

1. 打开项目目录
2. 配置 Python 解释器
3. 启用 pytest 作为测试框架

## 2. 项目结构

```
table-recognition/
├── src/                    # 源代码
│   ├── __init__.py        # 模块初始化
│   ├── detector.py        # 表格检测
│   ├── structure.py       # 结构识别
│   ├── extractor.py       # 单元格提取
│   ├── recognizer.py      # 文字识别
│   ├── pipeline.py        # 处理管道
│   └── utils.py           # 工具函数
├── tests/                 # 测试代码
│   ├── __init__.py
│   ├── test_detector.py
│   ├── test_structure.py
│   ├── test_extractor.py
│   └── test_pipeline.py
├── examples/              # 示例代码
│   └── demo.py
├── docs/                  # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── models/                # 模型文件
├── requirements.txt       # 依赖列表
├── README.md              # 项目说明
└── LEARNING_NOTES.md      # 学习笔记
```

## 3. 开发流程

### 3.1 功能开发流程

```
1. 创建功能分支
   git checkout -b feature/new-feature

2. 编写代码
   - 实现功能
   - 编写测试
   - 更新文档

3. 运行测试
   pytest

4. 提交代码
   git add .
   git commit -m "feat: add new feature"

5. 推送分支
   git push origin feature/new-feature

6. 创建 Pull Request

7. 代码审查

8. 合并到主分支
```

### 3.2 代码规范

#### PEP 8 规范

```python
# 好的命名
def calculate_iou(bbox1, bbox2):
    pass

class TableDetector:
    pass

MAX_AREA = 10000

# 不好的命名
def calc(b1, b2):
    pass

class td:
    pass

ma = 10000
```

#### 类型注解

```python
from typing import List, Dict, Optional

def detect_tables(
    image: np.ndarray,
    threshold: float = 0.5
) -> List[Dict]:
    """
    检测表格区域

    Args:
        image: 输入图像
        threshold: 置信度阈值

    Returns:
        检测结果列表
    """
    pass
```

#### 文档字符串

```python
def process_image(image: np.ndarray) -> Dict:
    """
    处理图像并识别表格

    Args:
        image: 输入图像，BGR 格式的 numpy 数组

    Returns:
        处理结果字典，包含:
        - tables: 检测到的表格列表
        - processing_time: 处理时间（秒）

    Raises:
        ValueError: 当输入图像无效时

    Example:
        >>> image = cv2.imread("table.jpg")
        >>> result = process_image(image)
        >>> print(len(result["tables"]))
        2
    """
    pass
```

### 3.3 Git 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型（type）：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat(detector): add deep learning based table detection

- Implement Faster R-CNN based detector
- Add model loading and inference
- Support GPU acceleration

Closes #123
```

## 4. 代码质量

### 4.1 代码格式化

使用 Black 进行代码格式化：

```bash
# 格式化单个文件
black src/detector.py

# 格式化整个项目
black src/ tests/

# 检查格式
black --check src/
```

使用 isort 整理导入：

```bash
# 整理导入
isort src/ tests/

# 检查导入顺序
isort --check-only src/
```

### 4.2 代码检查

使用 flake8 进行代码检查：

```bash
# 检查代码
flake8 src/ tests/

# 忽略特定规则
flake8 --ignore=E501,W503 src/
```

使用 mypy 进行类型检查：

```bash
# 类型检查
mypy src/
```

### 4.3 代码审查清单

- [ ] 代码符合 PEP 8 规范
- [ ] 类型注解完整
- [ ] 文档字符串清晰
- [ ] 测试覆盖充分
- [ ] 没有硬编码的魔法数字
- [ ] 错误处理完善
- [ ] 日志记录合理

## 5. 调试技巧

### 5.1 使用 print 调试

```python
def process_image(image):
    print(f"Image shape: {image.shape}")
    print(f"Image dtype: {image.dtype}")

    result = detect_tables(image)
    print(f"Detected {len(result)} tables")

    return result
```

### 5.2 使用 logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def process_image(image):
    logger.info(f"Processing image: {image.shape}")

    try:
        result = detect_tables(image)
        logger.info(f"Detected {len(result)} tables")
        return result
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise
```

### 5.3 使用 debugger

```python
# 使用 pdb
import pdb

def process_image(image):
    pdb.set_trace()  # 断点
    result = detect_tables(image)
    return result

# 使用 IDE 调试器
# 在 VS Code 或 PyCharm 中设置断点
```

### 5.4 可视化调试

```python
def debug_detection(image, detections):
    """可视化检测结果"""
    import cv2

    vis_image = image.copy()
    for det in detections:
        bbox = det["bbox"]
        cv2.rectangle(vis_image,
                     (bbox[0], bbox[1]),
                     (bbox[2], bbox[3]),
                     (0, 255, 0), 2)

    cv2.imshow("Debug", vis_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

## 6. 性能优化

### 6.1 代码优化

#### 使用 NumPy 向量化

```python
# 不好的写法
result = []
for i in range(len(array)):
    result.append(array[i] * 2)

# 好的写法
result = array * 2
```

#### 避免重复计算

```python
# 不好的写法
def process(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    binary2 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# 好的写法
def process(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    # 使用 binary 而不是重复计算
```

### 6.2 内存优化

```python
# 及时释放大对象
import gc

def process_large_image(image):
    result = heavy_computation(image)
    del image  # 释放原图
    gc.collect()
    return result
```

### 6.3 并行处理

```python
from concurrent.futures import ThreadPoolExecutor

def batch_process(images, num_workers=4):
    """并行处理多张图像"""
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_image, images))
    return results
```

## 7. 文档编写

### 7.1 README 编写

README 应包含：
- 项目简介
- 安装说明
- 快速开始
- 使用示例
- API 文档
- 贡献指南

### 7.2 代码注释

```python
# 好的注释
# 计算 IoU 用于过滤重叠的检测框
iou = calculate_iou(box1, box2)

# 不好的注释
# 计算 IoU
iou = calculate_iou(box1, box2)
```

### 7.3 API 文档

使用 docstring 生成 API 文档：

```bash
# 使用 pdoc
pip install pdoc
pdoc --html src/

# 使用 sphinx
pip install sphinx
sphinx-quickstart
make html
```

## 8. 发布流程

### 8.1 版本管理

使用语义化版本（Semantic Versioning）：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 修改
MINOR: 向下兼容的功能性新增
PATCH: 向下兼容的问题修正
```

### 8.2 发布清单

- [ ] 所有测试通过
- [ ] 文档更新
- [ ] 版本号更新
- [ ] CHANGELOG 更新
- [ ] 创建 Git 标签
- [ ] 发布到 PyPI（如需要）

### 8.3 创建发布

```bash
# 更新版本号
# 编辑 setup.py 或 pyproject.toml

# 提交更改
git add .
git commit -m "chore: bump version to 1.0.0"

# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

## 9. 常见问题

### 9.1 安装问题

**问题**: pip install 失败

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 使用镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 9.2 导入问题

**问题**: ModuleNotFoundError

**解决方案**:
```bash
# 确保在项目根目录
cd table-recognition

# 确保安装了依赖
pip install -r requirements.txt

# 使用相对导入
from src.detector import TableDetector
```

### 9.3 测试问题

**问题**: pytest 找不到测试

**解决方案**:
```bash
# 确保在项目根目录运行
cd table-recognition
pytest

# 检查测试文件命名
# 应该是 test_*.py 格式
```

## 10. 学习资源

### 10.1 Python 学习

- [Python 官方文档](https://docs.python.org/3/)
- [Real Python](https://realpython.com/)
- [Python 最佳实践](https://docs.python-guide.org/)

### 10.2 OpenCV 学习

- [OpenCV 官方教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [OpenCV Python 教程](https://opencv-python-tutroals.readthedocs.io/)

### 10.3 PyTorch 学习

- [PyTorch 官方教程](https://pytorch.org/tutorials/)
- [PyTorch 文档](https://pytorch.org/docs/stable/)

### 10.4 表格识别相关

- [ICDAR 竞赛](https://icdar2021.org/)
- [Papers With Code - Table Recognition](https://paperswithcode.com/task/table-recognition)

## 11. 总结

本开发指南涵盖了：

1. **环境搭建**: 如何配置开发环境
2. **项目结构**: 代码组织方式
3. **开发流程**: 从需求到发布的完整流程
4. **代码质量**: 如何保证代码质量
5. **调试技巧**: 如何高效调试
6. **性能优化**: 如何优化代码性能
7. **文档编写**: 如何编写清晰的文档
8. **发布流程**: 如何发布新版本

遵循这些指南可以帮助你更高效地开发和维护项目。
