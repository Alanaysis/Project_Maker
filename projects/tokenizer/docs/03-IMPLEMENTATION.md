# 实现文档

## 实现概述

本文档记录中文分词器的具体实现细节。

## 1. 词典管理 (dictionary.py)

### 核心实现

```python
class Dictionary:
    def __init__(self):
        self.words = {}  # {word: freq}
        self.max_length = 0

    def load(self, filepath):
        """加载词典文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    word, freq = parts[0], int(parts[1])
                    self.add(word, freq)

    def add(self, word, freq=1):
        """添加词条"""
        self.words[word] = freq
        self.max_length = max(self.max_length, len(word))

    def contains(self, word):
        """检查词是否在词典中"""
        return word in self.words
```

### 文件格式

词典文件每行格式：
```
词语 频率
```

示例：
```
北京 100
天安门 50
我 200
```

## 2. 正向最大匹配 (fmm.py)

### 核心算法

```python
def segment(self, text):
    result = []
    i = 0
    while i < len(text):
        matched = False
        # 从最长词开始匹配
        for length in range(self.max_len, 0, -1):
            if i + length > len(text):
                continue
            word = text[i:i+length]
            if self.dict.contains(word):
                result.append(word)
                i += length
                matched = True
                break
        # 未匹配则取单字
        if not matched:
            result.append(text[i])
            i += 1
    return result
```

### 时间复杂度

- 最好情况：O(n / max_len)
- 最坏情况：O(n * max_len)

## 3. 逆向最大匹配 (bmm.py)

### 核心算法

```python
def segment(self, text):
    result = []
    i = len(text)
    while i > 0:
        matched = False
        # 从最长词开始匹配
        for length in range(self.max_len, 0, -1):
            if i - length < 0:
                continue
            word = text[i-length:i]
            if self.dict.contains(word):
                result.append(word)
                i -= length
                matched = True
                break
        # 未匹配则取单字
        if not matched:
            result.append(text[i-1])
            i -= 1
    return list(reversed(result))
```

### 与 FMM 的区别

- 扫描方向相反
- 对某些歧义处理不同
- 例如："研究生命的起源"
  - FMM: 研究/生命/的/起源
  - BMM: 研究/生命/的/起源

## 4. HMM 分词 (hmm.py)

### 状态定义

```python
STATES = {'B': 0, 'M': 1, 'E': 2, 'S': 3}
```

### 训练过程

1. **构建观测序列和状态序列**
   - 从标注语料中提取
   - "我爱北京" -> 观测: [我,爱,北,京]
   - 对应状态: [S, S, B, E]

2. **统计概率**
   - 初始概率：π[i] = 以状态 i 开头的句子数 / 总句子数
   - 转移概率：A[i][j] = 从状态 i 转移到状态 j 的次数 / 从状态 i 转移的总次数
   - 发射概率：B[i][o] = 状态 i 观测到 o 的次数 / 状态 i 的总次数

### 维特比算法

```python
def viterbi(self, text):
    T = len(text)
    N = len(STATES)

    # 初始化
    dp = [[0.0] * N for _ in range(T)]
    path = [[0] * N for _ in range(T)]

    # 初始状态
    for s in range(N):
        dp[0][s] = self.start_prob[s] * self.emit_prob[s].get(text[0], 1e-8)

    # 递推
    for t in range(1, T):
        for s in range(N):
            max_prob = 0
            max_state = 0
            for ps in range(N):
                prob = dp[t-1][ps] * self.trans_prob[ps][s]
                if prob > max_prob:
                    max_prob = prob
                    max_state = ps
            dp[t][s] = max_prob * self.emit_prob[s].get(text[t], 1e-8)
            path[t][s] = max_state

    # 回溯
    states = [0] * T
    states[T-1] = dp[T-1].index(max(dp[T-1]))
    for t in range(T-2, -1, -1):
        states[t] = path[t+1][states[t+1]]

    return states
```

### 状态转分词

```python
def states_to_words(text, states):
    words = []
    word = ""
    for char, state in zip(text, states):
        if state == 'B':
            word = char
        elif state == 'M':
            word += char
        elif state == 'E':
            word += char
            words.append(word)
            word = ""
        elif state == 'S':
            words.append(char)
    return words
```

## 5. 主分词器 (tokenizer.py)

### 统一接口

```python
class Tokenizer:
    def __init__(self):
        self.dictionary = Dictionary()
        self.fmm = None
        self.bmm = None
        self.hmm = HMM()

    def load_dictionary(self, filepath):
        self.dictionary.load(filepath)
        self.fmm = FMM(self.dictionary)
        self.bmm = BMM(self.dictionary)

    def fmm(self, text):
        return self.fmm.segment(text)

    def bmm(self, text):
        return self.bmm.segment(text)

    def hmm(self, text):
        return self.hmm.segment(text)
```

## 测试策略

### 单元测试

1. **词典测试**
   - 加载词典
   - 添加词条
   - 查询词条

2. **FMM 测试**
   - 正常切分
   - 未登录词处理
   - 空文本处理

3. **BMM 测试**
   - 正常切分
   - 与 FMM 结果对比

4. **HMM 测试**
   - 模型训练
   - 模型保存/加载
   - 分词结果

### 集成测试

1. **完整流程测试**
   - 加载词典
   - 使用不同算法分词
   - 验证结果

## 已知限制

1. **词典依赖**：FMM 和 BMM 需要高质量词典
2. **HMM 训练数据**：需要大量标注语料
3. **未登录词**：无法识别词典外的词
4. **歧义处理**：简单算法无法处理所有歧义
