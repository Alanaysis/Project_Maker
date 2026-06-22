# 中文分词器

实现一个中文分词器，支持多种分词算法。

## 学习目标

- 理解分词算法
- 掌握词典构建
- 学会 HMM/CRF

## 技术栈

- 主语言：Python
- 框架：无
- 其他：无

## 核心循环

```
文本输入 → 分词算法 → 词序列 → 输出
```

## 最小可用版本

- 实现正向最大匹配
- 实现逆向最大匹配
- 实现 HMM 分词
- 简单的词典管理

## 项目结构

```
tokenizer/
├── src/
│   ├── __init__.py
│   ├── dictionary.py      # 词典管理
│   ├── fmm.py             # 正向最大匹配
│   ├── bmm.py             # 逆向最大匹配
│   ├── hmm.py             # HMM 分词
│   └── tokenizer.py       # 主分词器
├── tests/
│   ├── __init__.py
│   ├── test_dictionary.py
│   ├── test_fmm.py
│   ├── test_bmm.py
│   ├── test_hmm.py
│   └── test_tokenizer.py
├── data/
│   └── dict.txt           # 示例词典
├── docs/
│   ├── 01-RESEARCH.md     # 研究文档
│   ├── 02-DESIGN.md       # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md      # 测试文档
│   └── 05-DEVELOPMENT.md  # 开发文档
├── example.py             # 使用示例
├── setup.py               # 安装配置
├── requirements.txt       # 依赖列表
├── .gitignore             # Git 忽略文件
├── LEARNING_NOTES.md      # 学习笔记
└── README.md
```

## 使用方法

```python
from src.tokenizer import Tokenizer

# 创建分词器
tokenizer = Tokenizer()

# 加载词典
tokenizer.load_dictionary("data/dict.txt")

# 正向最大匹配
result = tokenizer.fmm("我爱北京天安门")

# 逆向最大匹配
result = tokenizer.bmm("我爱北京天安门")

# HMM 分词
result = tokenizer.hmm("我爱北京天安门")
```

## 安装

### 方式一：直接使用

```bash
cd projects/tokenizer
pip install -e .
```

### 方式二：安装依赖

```bash
cd projects/tokenizer
pip install -r requirements.txt
```

## 运行示例

```bash
cd projects/tokenizer
python3 example.py
```

## 运行测试

```bash
cd projects/tokenizer
pytest tests/ -v
```

## 运行覆盖率测试

```bash
cd projects/tokenizer
pytest --cov=src tests/
```

## 分词算法说明

### 正向最大匹配 (FMM)

从左到右扫描文本，每次取最长可能的词进行匹配。

**优点**：实现简单，速度快
**缺点**：无法处理歧义

### 逆向最大匹配 (BMM)

从右到左扫描文本，每次取最长可能的词进行匹配。

**优点**：对某些歧义处理比 FMM 好
**缺点**：同样依赖词典质量

### HMM 分词

使用隐马尔可夫模型进行分词，将分词问题转化为序列标注问题。

**状态定义**：
- B (Begin)：词的开始
- M (Middle)：词的中间
- E (End)：词的结束
- S (Single)：单字词

**优点**：可以处理未登录词
**缺点**：需要训练数据

## 学习资源

- [研究文档](docs/01-RESEARCH.md) - 分词算法研究
- [设计文档](docs/02-DESIGN.md) - 系统设计说明
- [实现文档](docs/03-IMPLEMENTATION.md) - 实现细节
- [测试文档](docs/04-TESTING.md) - 测试策略
- [开发文档](docs/05-DEVELOPMENT.md) - 开发指南
- [学习笔记](LEARNING_NOTES.md) - 学习总结

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
