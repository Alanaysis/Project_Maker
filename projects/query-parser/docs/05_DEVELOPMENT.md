# 查询解析器开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip (Python 包管理器)
- pytest (测试框架)

### 1.2 环境配置

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

### 1.3 IDE 配置

推荐使用 VS Code 或 PyCharm，配置 Python 解释器指向虚拟环境。

## 2. 项目结构

```
query-parser/
├── src/                        # 源代码
│   ├── __init__.py            # 包初始化
│   ├── lexer.py               # 词法分析器
│   ├── parser.py              # 语法分析器
│   ├── ast_nodes.py           # AST 节点定义
│   ├── optimizer.py           # 查询优化器
│   └── executor.py            # 查询执行器
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_lexer.py          # 词法分析器测试
│   ├── test_parser.py         # 语法分析器测试
│   └── test_executor.py       # 执行器测试
├── examples/                   # 示例代码
│   └── queries.py             # 查询示例
├── docs/                       # 文档
│   ├── 01_RESEARCH.md         # 研究文档
│   ├── 02_REQUIREMENTS.md     # 需求文档
│   ├── 03_DESIGN.md           # 设计文档
│   ├── 04_PRODUCT.md          # 产品文档
│   └── 05_DEVELOPMENT.md      # 开发文档
├── requirements.txt            # 依赖
└── README.md                   # 项目说明
```

## 3. 开发流程

### 3.1 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解
- 编写文档字符串
- 保持函数简短（< 50 行）

### 3.2 命名规范

- 类名：PascalCase
- 函数名：snake_case
- 常量：UPPER_SNAKE_CASE
- 私有成员：_leading_underscore

### 3.3 注释规范

```python
def function_name(param1: str, param2: int) -> bool:
    """
    函数功能描述

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ValueError: 异常描述
    """
    pass
```

## 4. 模块开发指南

### 4.1 词法分析器开发

#### 添加新 Token 类型

1. 在 `TokenType` 枚举中添加新类型
2. 在 `KEYWORDS` 字典中添加关键字映射（如果是关键字）
3. 在 `tokenize` 方法中添加识别逻辑

```python
# 1. 添加 Token 类型
class TokenType(Enum):
    NEW_TOKEN = auto()

# 2. 添加关键字映射
KEYWORDS = {
    'NEW_KEYWORD': TokenType.NEW_TOKEN,
}

# 3. 添加识别逻辑
def read_word(self):
    # ...
    upper = word.upper()
    if upper in KEYWORDS:
        return Token(KEYWORDS[upper], word)
```

### 4.2 语法分析器开发

#### 添加新语句类型

1. 在 `NodeType` 枚举中添加新节点类型
2. 在 `ast_nodes.py` 中定义新节点类
3. 在 `Parser` 中添加解析方法
4. 在 `parse` 方法中添加调用

```python
# 1. 添加节点类型
class NodeType(Enum):
    NEW_STMT = auto()

# 2. 定义节点类
@dataclass
class NewStatement(ASTNode):
    node_type: NodeType = NodeType.NEW_STMT
    # ...

# 3. 添加解析方法
def parse_new_statement(self) -> NewStatement:
    # ...
    pass

# 4. 在 parse 中调用
def parse(self) -> ASTNode:
    if self.match(TokenType.NEW_KEYWORD):
        return self.parse_new_statement()
```

### 4.3 执行器开发

#### 添加新语句执行

1. 在 `Executor` 中添加新方法
2. 在 `execute` 方法中添加调用

```python
# 1. 添加执行方法
def execute_new_statement(self, stmt: NewStatement) -> QueryResult:
    # ...
    pass

# 2. 在 execute 中调用
def execute(self, node: ASTNode) -> QueryResult:
    if isinstance(node, NewStatement):
        return self.execute_new_statement(node)
```

### 4.4 优化器开发

#### 添加新优化规则

1. 在 `QueryOptimizer` 中添加新方法
2. 在 `optimize` 方法中调用

```python
# 1. 添加优化方法
def new_optimization(self, node: ASTNode) -> ASTNode:
    # ...
    pass

# 2. 在 optimize 中调用
def optimize(self, node: ASTNode) -> ASTNode:
    node = self.new_optimization(node)
    return node
```

## 5. 测试指南

### 5.1 测试结构

```
tests/
├── test_lexer.py          # 词法分析器测试
├── test_parser.py         # 语法分析器测试
└── test_executor.py       # 执行器测试
```

### 5.2 编写测试

```python
import pytest
from src.parser import parse_sql

class TestParser:
    """语法分析器测试"""

    def test_simple_select(self):
        """测试简单 SELECT"""
        ast = parse_sql("SELECT * FROM users")
        assert isinstance(ast, SelectStatement)
        assert ast.from_clause.tables[0].table_name == "users"

    def test_error_case(self):
        """测试错误情况"""
        with pytest.raises(ParseError):
            parse_sql("SELECT FROM")
```

### 5.3 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_parser.py

# 运行特定测试类
pytest tests/test_parser.py::TestParser

# 运行特定测试方法
pytest tests/test_parser.py::TestParser::test_simple_select

# 显示详细输出
pytest -v

# 显示覆盖率
pytest --cov=src
```

### 5.4 测试覆盖率

目标：> 80% 代码覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 6. 调试技巧

### 6.1 打印 Token

```python
from src.lexer import tokenize

tokens = tokenize("SELECT * FROM users")
for token in tokens:
    print(token)
```

### 6.2 打印 AST

```python
from src.parser import parse_sql

ast = parse_sql("SELECT * FROM users WHERE id = 1")
print(ast)
```

### 6.3 使用断点

```python
import pdb; pdb.set_trace()  # Python 3.7+
breakpoint()  # Python 3.7+
```

### 6.4 日志记录

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_sql(sql):
    logger.debug(f"Parsing: {sql}")
    # ...
```

## 7. 性能优化

### 7.1 词法分析优化

- 使用字符串切片而不是逐字符处理
- 预编译正则表达式
- 减少函数调用

### 7.2 语法分析优化

- 使用迭代而不是递归（对于深层嵌套）
- 缓存解析结果
- 提前返回

### 7.3 执行优化

- 使用索引加速查询
- 批量处理数据
- 延迟计算

## 8. 常见问题

### 8.1 导入错误

```bash
# 确保在项目根目录运行
cd projects/query-parser

# 确保 src 在 Python 路径中
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 8.2 测试失败

```bash
# 检查测试环境
pytest --version

# 检查依赖
pip list

# 重新安装依赖
pip install -r requirements.txt
```

### 8.3 性能问题

```python
# 使用 cProfile 分析性能
import cProfile

cProfile.run('parse_sql("SELECT * FROM users")')
```

## 9. 发布流程

### 9.1 版本号

使用语义化版本号：MAJOR.MINOR.PATCH

- MAJOR：不兼容的 API 变更
- MINOR：向后兼容的功能新增
- PATCH：向后兼容的问题修复

### 9.2 发布步骤

1. 更新版本号
2. 更新 CHANGELOG
3. 运行测试
4. 提交代码
5. 打标签
6. 发布

```bash
# 更新版本
# 编辑 src/__init__.py

# 运行测试
pytest

# 提交
git add .
git commit -m "release: v1.0.0"

# 打标签
git tag v1.0.0

# 推送
git push origin master --tags
```

## 10. 贡献指南

### 10.1 提交代码

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 PR

### 10.2 代码审查

- 代码风格检查
- 测试覆盖率检查
- 功能验证

### 10.3 文档更新

- 更新 README
- 更新 API 文档
- 更新示例代码

## 11. 学习资源

### 11.1 SQL 相关

- [SQL Tutorial](https://www.w3schools.com/sql/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MySQL Documentation](https://dev.mysql.com/doc/)

### 11.2 解析器相关

- [Let's Build a Compiler](https://compilers.iecc.com/crenshaw/)
- [Crafting Interpreters](https://craftinginterpreters.com/)
- [ANTLR](https://www.antlr.org/)

### 11.3 Python 相关

- [Python Documentation](https://docs.python.org/3/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [pytest Documentation](https://docs.pytest.org/)
