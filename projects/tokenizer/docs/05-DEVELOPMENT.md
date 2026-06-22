# 开发文档

## 开发环境

### 依赖

- Python 3.8+
- pytest (测试)
- pytest-cov (覆盖率)

### 安装依赖

```bash
pip install pytest pytest-cov
```

## 项目结构

```
tokenizer/
├── src/
│   ├── __init__.py
│   ├── dictionary.py
│   ├── fmm.py
│   ├── bmm.py
│   ├── hmm.py
│   └── tokenizer.py
├── tests/
│   ├── __init__.py
│   ├── test_dictionary.py
│   ├── test_fmm.py
│   ├── test_bmm.py
│   ├── test_hmm.py
│   └── test_tokenizer.py
├── data/
│   └── dict.txt
├── docs/
└── README.md
```

## 开发流程

### 1. 词典管理模块

**实现步骤**：
1. 创建 Dictionary 类
2. 实现 load 方法
3. 实现 add/remove 方法
4. 实现 contains 方法
5. 编写测试

**关键代码**：
```python
class Dictionary:
    def __init__(self):
        self.words = {}
        self.max_length = 0

    def load(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    word, freq = parts[0], int(parts[1])
                    self.add(word, freq)
```

### 2. 正向最大匹配

**实现步骤**：
1. 创建 FMM 类
2. 实现 segment 方法
3. 处理边界情况
4. 编写测试

**关键代码**：
```python
class FMM:
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.max_len = dictionary.get_max_word_length()

    def segment(self, text):
        result = []
        i = 0
        while i < len(text):
            matched = False
            for length in range(self.max_len, 0, -1):
                if i + length > len(text):
                    continue
                word = text[i:i+length]
                if self.dictionary.contains(word):
                    result.append(word)
                    i += length
                    matched = True
                    break
            if not matched:
                result.append(text[i])
                i += 1
        return result
```

### 3. 逆向最大匹配

**实现步骤**：
1. 创建 BMM 类
2. 实现 segment 方法
3. 从右向左扫描
4. 编写测试

**关键代码**：
```python
class BMM:
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.max_len = dictionary.get_max_word_length()

    def segment(self, text):
        result = []
        i = len(text)
        while i > 0:
            matched = False
            for length in range(self.max_len, 0, -1):
                if i - length < 0:
                    continue
                word = text[i-length:i]
                if self.dictionary.contains(word):
                    result.append(word)
                    i -= length
                    matched = True
                    break
            if not matched:
                result.append(text[i-1])
                i -= 1
        return list(reversed(result))
```

### 4. HMM 分词

**实现步骤**：
1. 定义状态集合 {B, M, E, S}
2. 实现训练方法
3. 实现维特比算法
4. 实现状态转分词
5. 编写测试

**关键代码**：
```python
class HMM:
    def __init__(self):
        self.states = {'B': 0, 'M': 1, 'E': 2, 'S': 3}
        self.start_prob = [0.0] * 4
        self.trans_prob = [[0.0] * 4 for _ in range(4)]
        self.emit_prob = [{} for _ in range(4)]

    def train(self, corpus):
        # 统计初始概率、转移概率、发射概率
        pass

    def viterbi(self, text):
        # 维特比算法求最优路径
        pass

    def segment(self, text):
        states = self.viterbi(text)
        return self.states_to_words(text, states)
```

### 5. 主分词器

**实现步骤**：
1. 创建 Tokenizer 类
2. 集成各分词算法
3. 提供统一接口
4. 编写测试

**关键代码**：
```python
class Tokenizer:
    def __init__(self):
        self.dictionary = Dictionary()
        self.fmm_seg = None
        self.bmm_seg = None
        self.hmm_seg = HMM()

    def load_dictionary(self, filepath):
        self.dictionary.load(filepath)
        self.fmm_seg = FMM(self.dictionary)
        self.bmm_seg = BMM(self.dictionary)

    def fmm(self, text):
        return self.fmm_seg.segment(text)

    def bmm(self, text):
        return self.bmm_seg.segment(text)

    def hmm(self, text):
        return self.hmm_seg.segment(text)
```

## 测试执行

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_fmm.py

# 显示详细输出
pytest -v tests/

# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/
```

### 测试覆盖率

目标：核心算法 100% 覆盖

## 代码规范

1. **命名规范**
   - 类名：PascalCase
   - 方法名：snake_case
   - 常量：UPPER_SNAKE_CASE

2. **文档规范**
   - 每个类和方法都要有文档字符串
   - 使用中文注释

3. **导入规范**
   - 标准库在前
   - 第三方库在后
   - 本地模块最后

## 部署说明

### 打包

```bash
# 创建 setup.py
# 打包
python setup.py sdist bdist_wheel
```

### 发布

```bash
# 上传到 PyPI
twine upload dist/*
```

## 后续优化

1. **性能优化**
   - 使用 Trie 树优化词典查询
   - 缓存分词结果

2. **功能扩展**
   - 支持用户词典
   - 支持词性标注
   - 支持命名实体识别

3. **算法改进**
   - 实现 CRF 分词
   - 实现深度学习分词
