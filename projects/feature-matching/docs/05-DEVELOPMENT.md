# 特征匹配开发指南

## 1. 开发环境搭建

### 系统要求
- Python 3.8+
- pip 21.0+
- Git

### 安装步骤

```bash
# 1. 克隆项目
git clone <repo-url>
cd projects/feature-matching

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行测试
pytest tests/

# 5. 运行主程序
python src/main.py --help
```

## 2. 代码规范

### 命名规范
- 类名: PascalCase (e.g., `FeatureDetector`)
- 函数名: snake_case (e.g., `detect_keypoints`)
- 变量名: snake_case (e.g., `keypoints`)
- 常量名: UPPER_CASE (e.g., `MAX_FEATURES`)

### 文档规范
- 使用Google风格docstring
- 类和公共函数必须有文档
- 复杂算法添加注释

```python
def detect(self, image: np.ndarray) -> List[cv2.KeyPoint]:
    """
    检测图像中的特征点

    Args:
        image: 灰度图像，dtype=np.uint8

    Returns:
        关键点列表，每个关键点包含位置、尺度、方向等信息

    Raises:
        ValueError: 如果图像为空或格式不正确
    """
    pass
```

### 导入规范
```python
# 标准库
import os
import sys
from typing import List, Tuple

# 第三方库
import cv2
import numpy as np
import matplotlib.pyplot as plt

# 本地模块
from .detector import FeatureDetector
from .matcher import FeatureMatcher
```

## 3. 项目结构

```
feature-matching/
├── README.md              # 项目说明
├── LEARNING_NOTES.md      # 学习笔记
├── requirements.txt       # Python依赖
├── setup.py              # 包安装配置
├── docs/                 # 文档目录
│   ├── 01-RESEARCH.md    # 研究笔记
│   ├── 02-DESIGN.md      # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现记录
│   ├── 04-TESTING.md     # 测试文档
│   └── 05-DEVELOPMENT.md # 开发指南
├── src/                  # 源代码
│   ├── __init__.py
│   ├── detector.py       # 特征检测器
│   ├── descriptor.py     # 描述子提取
│   ├── matcher.py        # 特征匹配
│   ├── visualizer.py     # 可视化工具
│   └── main.py           # 主程序
├── tests/                # 测试代码
│   ├── __init__.py
│   ├── test_detector.py
│   ├── test_descriptor.py
│   ├── test_matcher.py
│   └── test_integration.py
└── data/                 # 数据目录
    └── examples/         # 示例图像
```

## 4. 开发工作流

### 分支策略
- main: 稳定版本
- develop: 开发分支
- feature/*: 功能分支
- bugfix/*: 修复分支

### 提交规范
```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
style: 代码格式
chore: 构建/工具
```

### 代码审查清单
- [ ] 代码符合规范
- [ ] 添加了必要的文档
- [ ] 编写了测试用例
- [ ] 测试全部通过
- [ ] 无明显性能问题

## 5. 调试技巧

### 日志记录
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect(self, image):
    logger.info(f"检测特征点，图像尺寸: {image.shape}")
    keypoints = self._detector.detect(image)
    logger.info(f"检测到 {len(keypoints)} 个特征点")
    return keypoints
```

### 可视化调试
```python
# 显示中间结果
def debug_show(image, title="Debug"):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

### 性能分析
```python
import cProfile

def profile_detection():
    pr = cProfile.Profile()
    pr.enable()

    # 要分析的代码
    detector.detect(image)

    pr.disable()
    pr.print_stats(sort='cumulative')
```

## 6. 常见问题

### 问题1: 检测不到特征点
**原因**: 图像纹理太少或阈值太高
**解决**:
- 降低对比度阈值
- 增加图像纹理
- 使用不同的检测器

### 问题2: 匹配结果差
**原因**: 描述子不具区分性或误匹配多
**解决**:
- 使用比率测试
- 增加RANSAC过滤
- 调整匹配参数

### 问题3: 处理速度慢
**原因**: 特征点太多或算法复杂度高
**解决**:
- 限制特征点数量
- 使用ORB替代SIFT
- 使用FLANN替代暴力匹配

### 问题4: 内存溢出
**原因**: 图像太大或特征点太多
**解决**:
- 限制最大特征点数
- 分批处理
- 使用图像金字塔

## 7. 扩展开发

### 添加新检测器
```python
class NewDetector:
    def __init__(self, **params):
        pass

    def detect(self, image):
        # 实现检测逻辑
        pass

# 注册到工厂
def create_detector(method):
    if method == 'new':
        return NewDetector()
    # ...
```

### 添加新匹配器
```python
class NewMatcher:
    def __init__(self, **params):
        pass

    def match(self, desc1, desc2):
        # 实现匹配逻辑
        pass
```

## 8. 部署指南

### 打包
```bash
# 创建setup.py
python setup.py sdist bdist_wheel

# 上传到PyPI
twine upload dist/*
```

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "src/main.py"]
```

## 9. 持续集成

### GitHub Actions配置
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=src tests/
```

## 10. 版本管理

### 版本号规则
- 主版本.次版本.修订号 (e.g., 1.0.0)
- 主版本: 不兼容的API变更
- 次版本: 向后兼容的功能新增
- 修订号: 向后兼容的问题修复

### 更新日志
```markdown
# Changelog

## [1.0.0] - 2026-06-22
### Added
- SIFT特征检测
- ORB特征检测
- 暴力匹配和FLANN匹配
- 可视化工具
```
