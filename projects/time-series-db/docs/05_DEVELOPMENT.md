# 开发文档: 时间序列数据库

## 1. 开发环境

### 1.1 环境要求
- Python 3.10+
- pip
- 虚拟环境 (推荐)

### 1.2 环境搭建

```bash
# 克隆项目
cd /home/siok/project_copyninja/projects/time-series-db

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 1.3 依赖说明

#### 核心依赖
```
aiohttp>=3.9.0      # HTTP 服务
lz4>=4.3.0          # 数据压缩
sortedcontainers>=2.4.0  # 有序数据结构
```

#### 开发依赖
```
pytest>=7.4.0       # 测试框架
pytest-asyncio>=0.21.0  # 异步测试
pytest-cov>=4.1.0   # 覆盖率
black>=23.0.0       # 代码格式化
flake8>=6.0.0       # 代码检查
mypy>=1.0.0         # 类型检查
```

## 2. 项目结构

```
time-series-db/
├── src/
│   ├── __init__.py
│   ├── db.py                # 主入口
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── memtable.py      # 内存表
│   │   ├── wal.py           # WAL
│   │   ├── storage.py       # 存储引擎
│   │   └── compression.py   # 数据压缩
│   ├── query/
│   │   ├── __init__.py
│   │   ├── executor.py      # 查询执行器
│   │   ├── aggregation.py   # 聚合函数
│   │   └── downsampling.py  # 降采样
│   ├── retention/
│   │   ├── __init__.py
│   │   └── ttl.py           # TTL 管理
│   └── api/
│       ├── __init__.py
│       └── server.py        # HTTP 服务
├── tests/
│   ├── __init__.py
│   ├── test_memtable.py
│   ├── test_wal.py
│   ├── test_storage.py
│   ├── test_query.py
│   └── test_retention.py
├── examples/
│   ├── monitoring.py
│   └── iot.py
├── docs/
├── requirements.txt
└── README.md
```

## 3. 编码规范

### 3.1 代码风格
- 遵循 PEP 8
- 使用 Black 格式化
- 使用 Flake8 检查

### 3.2 命名规范
- 类名: PascalCase
- 函数名: snake_case
- 变量名: snake_case
- 常量名: UPPER_SNAKE_CASE

### 3.3 类型注解
```python
from typing import List, Dict, Optional, Tuple

def query(
    metric: str,
    start: int,
    end: int,
    aggregation: Optional[str] = None
) -> List[Tuple[int, float]]:
    pass
```

### 3.4 文档字符串
```python
def write_batch(
    self,
    points: List[Dict]
) -> int:
    """
    批量写入数据点。

    Args:
        points: 数据点列表，每个点包含:
            - metric (str): 指标名称
            - tags (Dict[str, str]): 标签
            - timestamp (int): 时间戳
            - value (float): 值

    Returns:
        int: 成功写入的点数

    Raises:
        WriteError: 写入失败
    """
    pass
```

## 4. 核心模块实现

### 4.1 内存表 (memtable.py)

```python
from sortedcontainers import SortedDict
import threading

class MemTable:
    def __init__(self, max_size: int = 64 * 1024 * 1024):
        self.data = SortedDict()
        self.size = 0
        self.max_size = max_size
        self.lock = threading.RLock()

    def put(self, metric: str, tags: Dict, timestamp: int, value: float):
        key = (metric, frozenset(tags.items()), timestamp)
        with self.lock:
            self.data[key] = value
            self.size += self._estimate_size(key, value)

    def range_query(self, metric: str, start: int, end: int) -> List:
        results = []
        with self.lock:
            for key, value in self.data.items():
                m, _, ts = key
                if m == metric and start <= ts <= end:
                    results.append((ts, value))
        return results

    def is_full(self) -> bool:
        return self.size >= self.max_size
```

### 4.2 WAL (wal.py)

```python
import struct
import crcmod

class WAL:
    MAGIC = 0x57414C00
    crc32 = crcmod.predefined.mkCrcFun('crc-32')

    def __init__(self, wal_dir: str):
        self.wal_dir = wal_dir
        self.current_file = None
        self._open_new_file()

    def write(self, metric: str, tags: Dict, timestamp: int, value: float):
        data = self._encode(metric, tags, timestamp, value)
        crc = self.crc32(data)
        header = struct.pack('II', len(data), crc)
        self.current_file.write(header + data)
        self.current_file.flush()

    def _encode(self, metric, tags, timestamp, value):
        # 实现编码逻辑
        pass
```

### 4.3 存储引擎 (storage.py)

```python
class StorageEngine:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.memtable = MemTable()
        self.immutable_memtable = None
        self.wal = WAL(os.path.join(data_dir, 'wal'))
        self.sstables = []
        self.lock = threading.RLock()

    def write(self, metric: str, tags: Dict, timestamp: int, value: float):
        with self.lock:
            self.wal.write(metric, tags, timestamp, value)
            self.memtable.put(metric, tags, timestamp, value)
            if self.memtable.is_full():
                self._flush()

    def query(self, metric: str, start: int, end: int) -> List:
        with self.lock:
            results = []
            # 查询内存表
            results.extend(self.memtable.range_query(metric, start, end))
            # 查询不可变内存表
            if self.immutable_memtable:
                results.extend(self.immutable_memtable.range_query(metric, start, end))
            # 查询 SSTable
            results.extend(self._query_sstables(metric, start, end))
            return sorted(results, key=lambda x: x[0])
```

## 5. 测试

### 5.1 测试策略
- 单元测试: 测试单个模块
- 集成测试: 测试模块间交互
- 性能测试: 测试性能指标

### 5.2 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_memtable.py

# 运行并生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行性能测试
pytest tests/test_performance.py -v
```

### 5.3 测试示例

```python
# tests/test_memtable.py
import pytest
from src.engine.memtable import MemTable

class TestMemTable:
    def setup_method(self):
        self.memtable = MemTable(max_size=1024*1024)

    def test_put_and_get(self):
        self.memtable.put("cpu", {"host": "s1"}, 1000, 45.2)
        results = self.memtable.range_query("cpu", 0, 2000)
        assert len(results) == 1
        assert results[0] == (1000, 45.2)

    def test_range_query(self):
        for i in range(100):
            self.memtable.put("cpu", {"host": "s1"}, i * 100, float(i))
        results = self.memtable.range_query("cpu", 1000, 5000)
        assert len(results) == 41  # 1000, 1100, ..., 5000

    def test_is_full(self):
        small_memtable = MemTable(max_size=100)
        small_memtable.put("cpu", {}, 1000, 45.2)
        assert small_memtable.is_full()
```

## 6. 构建和部署

### 6.1 打包

```bash
# 安装打包工具
pip install build twine

# 构建
python -m build

# 上传到 PyPI (可选)
twine upload dist/*
```

### 6.2 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "-m", "src.api.server"]
```

### 6.3 配置管理

```bash
# 使用配置文件
python -m src.api.server --config config.yaml

# 使用环境变量
TSDB_DATA_DIR=./data TSDB_PORT=8080 python -m src.api.server
```

## 7. 调试

### 7.1 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 7.2 性能分析

```bash
# cProfile
python -m cProfile -o profile.stats src/api/server.py

# 分析结果
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

### 7.3 内存分析

```bash
# memory_profiler
pip install memory_profiler
python -m memory_profiler src/api/server.py
```

## 8. 贡献指南

### 8.1 开发流程
1. Fork 项目
2. 创建特性分支
3. 提交代码
4. 创建 Pull Request

### 8.2 提交规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

### 8.3 代码审查
- 所有 PR 需要至少一个审查
- 测试覆盖率不能下降
- 代码风格检查通过

## 9. 发布流程

### 9.1 版本号
- 主版本号: 不兼容的 API 变更
- 次版本号: 向后兼容的功能性新增
- 修订号: 向后兼容的问题修正

### 9.2 发布步骤
1. 更新版本号
2. 更新 CHANGELOG
3. 创建 Git Tag
4. 构建发布包
5. 发布到 PyPI
6. 创建 GitHub Release
