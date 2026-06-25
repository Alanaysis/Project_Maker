# 05 - 开发指南

## 开发环境设置

### 5.1 环境要求

- Python 3.9+
- pip 或 poetry
- Git

### 5.2 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd decentralized-voting/python

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install -e ".[dev]"
```

### 5.3 项目结构

```
python/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── blockchain.py      # 区块链模块
│   ├── voting.py          # 投票模块
│   ├── identity.py        # 身份模块
│   ├── consensus.py       # 规则模块
│   └── transparency.py    # 透明性模块
├── tests/                 # 测试代码
│   ├── __init__.py
│   ├── test_blockchain.py
│   ├── test_voting.py
│   ├── test_identity.py
│   ├── test_consensus.py
│   └── test_transparency.py
├── examples/              # 示例代码
│   ├── basic_voting.py
│   ├── dao_voting.py
│   └── community_governance.py
├── docs/                  # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_IMPLEMENTATION.md
│   ├── 04_TESTING.md
│   └── 05_DEVELOPMENT.md
├── requirements.txt       # 依赖
├── setup.py              # 安装脚本
└── README.md             # 项目说明
```

## 开发流程

### 5.4 Git 工作流

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发功能
# 编写代码和测试

# 3. 运行测试
pytest

# 4. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 5. 推送分支
git push origin feature/new-feature

# 6. 创建 Pull Request
# 在 GitHub 上创建 PR

# 7. 代码审查
# 等待审查和合并
```

### 5.5 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例:**
```
feat(voting): 添加投票权重功能

- 支持加权投票
- 添加权重验证
- 更新测试用例

Closes #123
```

## 代码规范

### 5.6 Python 代码风格

遵循 PEP 8 规范：

```python
# 1. 导入顺序
import os
import sys
from typing import List, Dict

import pytest

from src.blockchain import Blockchain
from src.voting import VotingContract

# 2. 命名规范
# 模块名: 小写 + 下划线
# 类名: 驼峰命名
# 函数名: 小写 + 下划线
# 常量: 大写 + 下划线

# 3. 行长度: 最大 88 字符（Black 默认）

# 4. 注释
def vote(session_id: int, proposal_id: int, voter: str) -> None:
    """
    执行投票

    Args:
        session_id: 投票活动ID
        proposal_id: 提案ID
        voter: 投票者地址

    Raises:
        ValueError: 投票活动不存在
        PermissionError: 无投票权限
    """
    pass
```

### 5.7 类型注解

```python
from typing import List, Dict, Optional, Any

# 函数签名
def create_vote_session(
    title: str,
    description: str,
    start_time: float,
    end_time: float,
    creator: str,
) -> int:
    pass

# 变量注解
voters: Dict[str, Voter] = {}
proposals: List[Proposal] = []
result: Optional[VoteResult] = None
```

### 5.8 数据类使用

```python
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Voter:
    """选民数据结构"""
    address: str
    name: str
    email: str
    voting_power: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "address": self.address,
            "name": self.name,
            "email": self.email,
            "voting_power": self.voting_power,
        }
```

## 测试指南

### 5.9 编写测试

```python
import pytest
from src.voting import VotingContract

class TestVotingContract:
    """投票合约测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.contract = VotingContract()

    def test_create_vote_session(self):
        """测试创建投票活动"""
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator="0xCreator",
        )
        assert session_id == 0

    def test_vote_twice_raises_error(self):
        """测试重复投票抛出异常"""
        # 准备
        session_id = self._create_session_with_proposal()
        self.contract.start_voting(session_id, "0xCreator")

        # 第一次投票
        self.contract.vote(session_id, 0, "0xVoter1")

        # 第二次投票应该失败
        with pytest.raises(ValueError, match="您已经投过票了"):
            self.contract.vote(session_id, 0, "0xVoter1")
```

### 5.10 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看未覆盖的行
pytest --cov=src --cov-report=term-missing
```

## 文档编写

### 5.11 文档规范

1. **README.md**: 项目概述和快速开始
2. **API 文档**: 使用 docstring
3. **架构文档**: 系统设计说明
4. **开发指南**: 开发流程和规范

### 5.12 Docstring 格式

使用 Google 风格：

```python
def vote(
    session_id: int,
    proposal_id: int,
    voter_address: str,
) -> None:
    """
    执行投票

    Args:
        session_id: 投票活动ID
        proposal_id: 提案ID
        voter_address: 投票者地址

    Raises:
        ValueError: 投票活动不存在或提案无效
        PermissionError: 选民无投票资格
        DuplicateVoteError: 选民已投票

    Example:
        >>> contract = VotingContract()
        >>> contract.vote(1, 0, "0xVoter1")
    """
    pass
```

## 部署指南

### 5.13 打包发布

```bash
# 1. 更新版本号
# 在 setup.py 和 __init__.py 中更新版本号

# 2. 构建包
python -m build

# 3. 检查包
twine check dist/*

# 4. 上传到 PyPI
twine upload dist/*
```

### 5.14 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "examples/basic_voting.py"]
```

## 调试技巧

### 5.15 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def vote(session_id, proposal_id, voter):
    logger.info(f"Voter {voter} voting for proposal {proposal_id}")
    # ...
    logger.info(f"Vote recorded successfully")
```

### 5.16 断点调试

```python
# 使用 pdb
import pdb; pdb.set_trace()

# 使用 ipdb（更好用）
import ipdb; ipdb.set_trace()

# 使用 VS Code 调试器
# 在 .vscode/launch.json 中配置
```

## 性能优化

### 5.17 优化建议

1. **缓存**: 使用 `lru_cache` 缓存频繁访问的数据
2. **批量处理**: 合并多个操作减少开销
3. **异步处理**: 使用 `asyncio` 处理 I/O 密集型任务
4. **数据结构**: 选择合适的数据结构

### 5.18 性能测试

```python
import time

def benchmark_vote():
    """性能测试"""
    contract = VotingContract()
    # 创建投票活动
    session_id = contract.create_vote_session(...)

    start = time.time()
    for i in range(1000):
        contract.vote(session_id, 0, f"0xVoter{i}")
    end = time.time()

    print(f"1000 次投票耗时: {end - start:.2f} 秒")
```

## 常见问题

### 5.19 FAQ

**Q: 如何扩展新的投票方式？**

A: 在 `consensus.py` 中添加新的投票方法枚举，并在 `VotingEngine` 中实现对应的逻辑。

**Q: 如何连接真实的区块链？**

A: 使用 `web3.py` 库连接以太坊网络，替换本地的区块链实现。

**Q: 如何添加 REST API？**

A: 使用 `FastAPI` 或 `Flask` 创建 API 接口，封装核心功能。

**Q: 如何提高安全性？**

A: 添加数字签名、加密存储、访问控制等安全机制。

## 贡献指南

### 5.20 如何贡献

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 确保测试通过
5. 提交 Pull Request

### 5.21 代码审查清单

- [ ] 代码符合 PEP 8 规范
- [ ] 有完整的类型注解
- [ ] 有充分的测试覆盖
- [ ] 文档已更新
- [ ] 没有引入新的依赖（或已说明原因）
- [ ] 性能没有明显下降
