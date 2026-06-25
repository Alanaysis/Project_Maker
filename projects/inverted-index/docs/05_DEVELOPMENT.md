# 05 - 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip

### 1.2 依赖安装

```bash
# 基础依赖（无额外依赖）
pip install -r requirements.txt

# 或直接使用标准库（本项目核心功能不依赖外部库）
```

### 1.3 项目结构

```
inverted-index/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── tokenizer.py        # 分词器
│   ├── stopwords.py        # 停用词过滤
│   ├── stemmer.py          # 词干提取
│   ├── lemmatizer.py       # 词形还原
│   ├── index.py            # 索引实现
│   ├── query.py            # 查询处理
│   ├── ranking.py          # 排序算法
│   └── search_engine.py    # 搜索引擎
├── tests/                  # 测试代码
│   ├── test_tokenizer.py
│   ├── test_stopwords.py
│   ├── test_stemmer.py
│   ├── test_lemmatizer.py
│   ├── test_index.py
│   ├── test_query.py
│   └── test_ranking.py
├── examples/               # 示例代码
│   ├── basic_search.py
│   └── document_retrieval.py
├── docs/                   # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── requirements.txt        # 依赖
└── README.md              # 项目说明
```

## 2. 开发指南

### 2.1 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串
- 保持函数简洁

### 2.2 命名规范

- 类名：PascalCase
- 函数名：snake_case
- 常量：UPPER_SNAKE_CASE
- 私有成员：前缀 _

### 2.3 文档字符串

```python
def function_name(param1: str, param2: int) -> bool:
    """函数简短描述

    详细描述（可选）。

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        返回值说明

    Raises:
        ValueError: 异常说明
    """
    pass
```

## 3. 测试指南

### 3.1 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_index.py

# 运行并显示覆盖率
python -m pytest tests/ --cov=src/

# 运行并显示详细输出
python -m pytest tests/ -v
```

### 3.2 编写测试

```python
import unittest
from src.index import InvertedIndex, Document


class TestInvertedIndex(unittest.TestCase):
    """测试类简短描述"""

    def setUp(self):
        """测试前准备"""
        self.index = InvertedIndex()

    def test_add_document(self):
        """测试用例描述"""
        doc = Document(doc_id="1", title="Test", content="Hello World")
        self.index.add_document(doc)
        self.assertEqual(self.index.doc_count, 1)

    def tearDown(self):
        """测试后清理"""
        pass
```

### 3.3 测试覆盖

目标覆盖率：> 80%

需要覆盖的模块：
- [x] Tokenizer
- [x] StopWordsFilter
- [x] PorterStemmer
- [x] Lemmatizer
- [x] InvertedIndex
- [x] PositionalIndex
- [x] CompressedIndex
- [x] QueryParser
- [x] QueryExecutor
- [x] TFIDFRanker
- [x] BM25Ranker

## 4. 构建和发布

### 4.1 本地开发

```bash
# 克隆项目
git clone <repo-url>
cd inverted-index

# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 运行示例
python examples/basic_search.py
```

### 4.2 打包

```bash
# 创建 setup.py
# 构建分发包
python setup.py sdist bdist_wheel

# 安装
pip install dist/inverted_index-1.0.0.tar.gz
```

## 5. 调试技巧

### 5.1 日志输出

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
```

### 5.2 常见问题

**Q: 搜索结果为空**
A: 检查停用词过滤是否过度，尝试自定义停用词列表

**Q: 中文搜索不准确**
A: 当前使用字符分割，建议集成 jieba 分词

**Q: 内存占用过高**
A: 使用压缩索引或分批处理

## 6. 扩展开发

### 6.1 自定义分词器

```python
from src.tokenizer import Tokenizer

class CustomTokenizer(Tokenizer):
    def tokenize(self, text: str) -> List[str]:
        # 自定义分词逻辑
        return tokens
```

### 6.2 自定义排序器

```python
from src.ranking import Ranker

class CustomRanker(Ranker):
    def score(self, query_terms: List[str], doc_id: str) -> float:
        # 自定义评分逻辑
        return score
```

### 6.3 添加新功能

1. 在对应模块中添加实现
2. 编写单元测试
3. 更新文档
4. 提交代码

## 7. 性能优化

### 7.1 索引优化

- 使用压缩索引减少内存
- 批量添加文档减少开销
- 定期重建索引优化结构

### 7.2 查询优化

- 缓存热门查询结果
- 使用索引裁剪减少候选集
- 并行处理多个查询

## 8. 已知问题

1. 中文分词精度有限
2. 不支持增量更新压缩索引
3. 模糊查询性能随词汇表增大而下降

## 9. 更新日志

### v1.0.0 (2026-06-24)
- 初始版本发布
- 实现基本倒排索引
- 支持布尔查询
- 实现 TF-IDF 和 BM25 排序
