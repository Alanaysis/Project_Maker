# 分词器

实现一个完整的分词器系统，支持中文分词、英文分词、子词分词和词性标注。

## 学习目标

- 理解分词算法（正向/逆向/双向最大匹配）
- 掌握词典构建和 HMM 模型
- 学会子词分词（BPE、WordPiece、Unigram）
- 掌握词性标注方法
- 了解实际应用场景

## 技术栈

- 主语言：Python
- 框架：无
- 其他：无

## 核心循环

```
文本输入 → 分词算法 → 词序列 → 词性标注 → 输出
```

## 最小可用版本

- 实现正向最大匹配
- 实现逆向最大匹配
- 实现双向最大匹配
- 实现 HMM 分词
- 实现英文分词
- 实现子词分词（BPE、WordPiece、Unigram）
- 实现词性标注（HMM、规则）
- 实现实际应用（文本预处理、搜索引擎、机器翻译）

## 项目结构

```
tokenizer/
├── src/
│   ├── __init__.py          # 模块初始化
│   ├── dictionary.py        # 词典管理
│   ├── fmm.py              # 正向最大匹配
│   ├── bmm.py              # 逆向最大匹配
│   ├── bidirectional.py     # 双向最大匹配
│   ├── hmm.py              # HMM 分词
│   ├── english.py           # 英文分词
│   ├── subword.py           # 子词分词（BPE、WordPiece、Unigram）
│   ├── pos_tagger.py        # 词性标注（HMM、规则）
│   ├── preprocessor.py      # 文本预处理和应用
│   └── tokenizer.py         # 主分词器
├── tests/
│   ├── __init__.py
│   ├── test_dictionary.py
│   ├── test_fmm.py
│   ├── test_bmm.py
│   ├── test_bidirectional.py
│   ├── test_hmm.py
│   ├── test_english.py
│   ├── test_subword.py
│   ├── test_pos_tagger.py
│   ├── test_preprocessor.py
│   └── test_tokenizer.py
├── data/
│   └── dict.txt            # 示例词典
├── docs/
│   ├── 01-RESEARCH.md      # 研究文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
├── example.py              # 使用示例
├── setup.py                # 安装配置
├── requirements.txt        # 依赖列表
├── .gitignore              # Git 忽略文件
├── LEARNING_NOTES.md       # 学习笔记
└── README.md
```

## 功能特性

### 1. 中文分词

- **正向最大匹配 (FMM)**：从左到右扫描，取最长词匹配
- **逆向最大匹配 (BMM)**：从右到左扫描，取最长词匹配
- **双向最大匹配 (BiMM)**：结合 FMM 和 BMM，选择更优结果
- **HMM 分词**：基于隐马尔可夫模型，处理未登录词

### 2. 英文分词

- **空格分词**：按空格分割
- **标点处理**：自动分离标点符号
- **缩写处理**：展开或保留缩写（如 don't → do not）
- **数字处理**：识别整数、小数、百分比
- **URL 处理**：识别 URL 和邮箱

### 3. 子词分词

- **BPE (字节对编码)**：通过统计字符对合并学习子词
- **WordPiece**：通过最大似然估计学习子词
- **Unigram**：基于 Unigram 语言模型的分词

### 4. 词性标注

- **HMM 词性标注**：基于隐马尔可夫模型的序列标注
- **规则词性标注**：基于词典和词缀规则的标注

### 5. 实际应用

- **文本预处理**：清洗、标准化、特征提取
- **搜索引擎分词**：倒排索引构建、查询处理
- **机器翻译分词**：平行语料处理、词对齐

## 使用方法

### 中文分词

```python
from src.tokenizer import Tokenizer

# 创建分词器
tokenizer = Tokenizer()

# 加载词典
tokenizer.load_dictionary("data/dict.txt")

# 正向最大匹配
result = tokenizer.fmm("我爱北京天安门")
# 输出: ['我', '爱', '北京', '天安门']

# 逆向最大匹配
result = tokenizer.bmm("我爱北京天安门")
# 输出: ['我', '爱', '北京', '天安门']

# 双向最大匹配
result = tokenizer.bimm("我爱北京天安门")
# 输出: ['我', '爱', '北京', '天安门']

# HMM 分词
corpus = ["我/S 爱/S 北京/B 天安门/E"]
tokenizer.train_hmm(corpus)
result = tokenizer.hmm("我爱北京天安门")
# 输出: ['我', '爱', '北京', '天安门']
```

### 英文分词

```python
from src.english import EnglishTokenizer

# 创建英文分词器
tokenizer = EnglishTokenizer(expand_contractions=True)

# 基本分词
result = tokenizer.tokenize("Hello, world!")
# 输出: ['Hello', ',', 'world', '!']

# 缩写处理
result = tokenizer.tokenize("I can't believe it")
# 输出: ['I', 'can', 'not', 'believe', 'it']

# 分句
result = tokenizer.sentence_split("Hello world. How are you?")
# 输出: ['Hello world.', 'How are you?']
```

### 子词分词

```python
from src.subword import BPETokenizer, WordPieceTokenizer, UnigramTokenizer

# BPE 分词
bpe = BPETokenizer(vocab_size=100)
bpe.train(["low lower newest wide"])
result = bpe.tokenize("lower")
# 输出: ['low', 'er']

# WordPiece 分词
wp = WordPieceTokenizer(vocab_size=100)
wp.train(["unaffable", "unlikely"])
result = wp.tokenize("unaffable")
# 输出: ['un', '##aff', '##able']

# Unigram 分词
uni = UnigramTokenizer(vocab_size=100)
uni.train(["low lower newest wide"])
result = uni.tokenize("lower")
# 输出: ['low', 'er']
```

### 词性标注

```python
from src.pos_tagger import POSTagger

# 规则标注
tagger = POSTagger(method='rule')
result = tagger.tag(["我", "爱", "北京"])
# 输出: [('我', 'r'), ('爱', 'v'), ('北京', 'n')]

# HMM 标注
tagger = POSTagger(method='hmm')
corpus = [[("我", "r"), ("爱", "v"), ("北京", "n")]]
tagger.train(corpus)
result = tagger.tag(["我", "爱", "北京"])
# 输出: [('我', 'r'), ('爱', 'v'), ('北京', 'n')]
```

### 实际应用

```python
from src.preprocessor import TextPreprocessor, SearchTokenizer

# 文本预处理
preprocessor = TextPreprocessor()
result = preprocessor.preprocess("  Hello, World!  ")
# 输出: 'Hello World!'

# 搜索引擎分词
tokenizer = Tokenizer()
tokenizer.load_dictionary("data/dict.txt")
search = SearchTokenizer(tokenizer, remove_stopwords=True)

# 构建索引
documents = [(1, "北京天安门"), (2, "上海外滩")]
index = search.build_index(documents)

# 搜索
results = search.search("北京", index)
# 输出: [(1, 1)]
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

### 双向最大匹配 (BiMM)

结合 FMM 和 BMM 的结果，选择更优的分词方案。

**策略**：
1. 如果结果相同，返回该结果
2. 如果词数不同，选择词数较少的
3. 如果词数相同，选择单字较少的
4. 如果都相同，选择 BMM 结果

**优点**：综合两种方法的优势
**缺点**：计算量是单向的两倍

### HMM 分词

使用隐马尔可夫模型进行分词，将分词问题转化为序列标注问题。

**状态定义**：
- B (Begin)：词的开始
- M (Middle)：词的中间
- E (End)：词的结束
- S (Single)：单字词

**优点**：可以处理未登录词
**缺点**：需要训练数据

### BPE (字节对编码)

通过统计字符对的频率，迭代合并最频繁的字符对。

**步骤**：
1. 初始化词表为所有字符
2. 统计相邻字符对的频率
3. 合并最频繁的字符对
4. 重复直到达到目标词表大小

**优点**：无需预分词，可处理任意文本
**缺点**：可能产生不合理的子词

### WordPiece

类似 BPE，但使用最大似然估计选择合并的子串。

**特点**：
- 使用 `##` 前缀标记子词
- 优先选择高频子串
- 用于 BERT 等模型

**优点**：产生的子词更有意义
**缺点**：计算复杂度较高

### Unigram

基于 Unigram 语言模型，通过 EM 算法学习最优分词。

**步骤**：
1. 初始化候选词表
2. E 步：计算每个词的最优分割
3. M 步：更新词的概率
4. 修剪低概率词

**优点**：全局最优分词
**缺点**：需要大量训练数据

## 学习资源

- [研究文档](docs/01-RESEARCH.md) - 分词算法研究
- [设计文档](docs/02-DESIGN.md) - 系统设计说明
- [实现文档](docs/03-IMPLEMENTATION.md) - 实现细节
- [测试文档](docs/04-TESTING.md) - 测试策略
- [开发文档](docs/05-DEVELOPMENT.md) - 开发指南
- [学习笔记](LEARNING_NOTES.md) - 学习总结

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
