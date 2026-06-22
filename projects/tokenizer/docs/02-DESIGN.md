# 设计文档

## 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    Tokenizer                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │   FMM   │  │   BMM   │  │   HMM   │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
│       │            │            │                   │
│       └────────────┼────────────┘                   │
│                    │                                │
│             ┌──────┴──────┐                         │
│             │  Dictionary │                         │
│             └─────────────┘                         │
└─────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Dictionary (词典管理)

**职责**：
- 加载词典文件
- 管理词条
- 提供查询接口

**接口设计**：
```python
class Dictionary:
    def load(filepath: str) -> None
    def add(word: str, freq: int) -> None
    def remove(word: str) -> None
    def contains(word: str) -> bool
    def get_max_word_length() -> int
    def get_words() -> List[str]
```

### 2. FMM (正向最大匹配)

**职责**：
- 实现正向最大匹配算法
- 使用词典进行切分

**接口设计**：
```python
class FMM:
    def __init__(self, dictionary: Dictionary)
    def segment(text: str) -> List[str]
```

**算法流程**：
```
输入: text, dict
输出: words[]

while text 不为空:
    for len = max_len to 1:
        word = text[0:len]
        if word in dict:
            words.append(word)
            text = text[len:]
            break
    else:
        words.append(text[0])
        text = text[1:]
```

### 3. BMM (逆向最大匹配)

**职责**：
- 实现逆向最大匹配算法
- 使用词典进行切分

**接口设计**：
```python
class BMM:
    def __init__(self, dictionary: Dictionary)
    def segment(text: str) -> List[str]
```

### 4. HMM (隐马尔可夫模型)

**职责**：
- 实现 HMM 分词模型
- 训练模型参数
- 使用维特比算法进行解码

**接口设计**：
```python
class HMM:
    def __init__(self)
    def train(corpus: List[str]) -> None
    def segment(text: str) -> List[str]
    def save_model(filepath: str) -> None
    def load_model(filepath: str) -> None
```

**状态定义**：
- B: 词的开始 (Begin)
- M: 词的中间 (Middle)
- E: 词的结束 (End)
- S: 单字词 (Single)

### 5. Tokenizer (主分词器)

**职责**：
- 提供统一的分词接口
- 管理不同的分词算法
- 提供结果格式化

**接口设计**：
```python
class Tokenizer:
    def __init__(self)
    def load_dictionary(filepath: str) -> None
    def fmm(text: str) -> List[str]
    def bmm(text: str) -> List[str]
    def hmm(text: str) -> List[str]
```

## 数据结构设计

### 词典数据结构

使用 Trie 树或 Python 字典实现：
```python
# Python 字典实现
{
    "北京": 100,
    "天安门": 50,
    "我": 200,
    ...
}
```

### HMM 模型参数

```python
{
    "start_prob": {"B": 0.5, "M": 0.0, "E": 0.0, "S": 0.5},
    "trans_prob": {
        "B": {"B": 0.0, "M": 0.7, "E": 0.3, "S": 0.0},
        "M": {"B": 0.0, "M": 0.7, "E": 0.3, "S": 0.0},
        "E": {"B": 0.5, "M": 0.0, "E": 0.0, "S": 0.5},
        "S": {"B": 0.5, "M": 0.0, "E": 0.0, "S": 0.5}
    },
    "emit_prob": {
        "B": {"我": 0.1, "爱": 0.05, ...},
        "M": {...},
        "E": {...},
        "S": {...}
    }
}
```

## 错误处理

1. **文件不存在**：抛出 FileNotFoundError
2. **词典为空**：抛出 ValueError
3. **文本为空**：返回空列表
4. **编码错误**：抛出 UnicodeDecodeError

## 性能考虑

1. **词典加载**：一次性加载到内存
2. **字符串操作**：使用切片而非循环
3. **HMM 计算**：使用对数概率避免下溢
