# 测试文档

## 测试策略

### 测试类型

1. **单元测试**：测试各个模块的核心功能
2. **集成测试**：测试模块间的协作
3. **边界测试**：测试边界条件和异常情况

### 测试覆盖率目标

- 核心算法：100%
- 辅助功能：90%+
- 整体覆盖率：85%+

## 测试用例

### 1. Dictionary 测试

#### 基本功能测试

```python
def test_load_dictionary():
    """测试加载词典"""
    dict = Dictionary()
    dict.load("data/dict.txt")
    assert len(dict.words) > 0

def test_add_word():
    """测试添加词条"""
    dict = Dictionary()
    dict.add("测试", 100)
    assert dict.contains("测试")
    assert dict.get_frequency("测试") == 100

def test_contains():
    """测试查询词条"""
    dict = Dictionary()
    dict.add("北京", 100)
    assert dict.contains("北京") == True
    assert dict.contains("上海") == False

def test_max_length():
    """测试最大词长"""
    dict = Dictionary()
    dict.add("我", 100)
    dict.add("北京", 50)
    dict.add("天安门", 20)
    assert dict.get_max_word_length() == 3
```

#### 边界测试

```python
def test_empty_dictionary():
    """测试空词典"""
    dict = Dictionary()
    assert dict.get_max_word_length() == 0

def test_load_nonexistent_file():
    """测试加载不存在的文件"""
    dict = Dictionary()
    with pytest.raises(FileNotFoundError):
        dict.load("nonexistent.txt")
```

### 2. FMM 测试

#### 基本功能测试

```python
def test_fmm_basic():
    """测试基本正向最大匹配"""
    dict = Dictionary()
    dict.add("我", 100)
    dict.add("爱", 100)
    dict.add("北京", 100)
    dict.add("天安门", 100)

    fmm = FMM(dict)
    result = fmm.segment("我爱北京天安门")
    assert result == ["我", "爱", "北京", "天安门"]

def test_fmm_ambiguity():
    """测试歧义处理"""
    dict = Dictionary()
    dict.add("研究", 100)
    dict.add("研究生", 100)
    dict.add("生命", 100)
    dict.add("命", 50)
    dict.add("的", 100)
    dict.add("起源", 100)

    fmm = FMM(dict)
    result = fmm.segment("研究生命的起源")
    # FMM 会选择最长匹配 "研究生"
    assert result == ["研究生", "命", "的", "起源"]
```

#### 边界测试

```python
def test_fmm_empty_text():
    """测试空文本"""
    dict = Dictionary()
    fmm = FMM(dict)
    result = fmm.segment("")
    assert result == []

def test_fmm_single_char():
    """测试单字"""
    dict = Dictionary()
    dict.add("我", 100)

    fmm = FMM(dict)
    result = fmm.segment("我")
    assert result == ["我"]

def test_fmm_unknown_words():
    """测试未登录词"""
    dict = Dictionary()
    dict.add("北京", 100)

    fmm = FMM(dict)
    result = fmm.segment("我爱北京")
    assert result == ["我", "爱", "北京"]
```

### 3. BMM 测试

#### 基本功能测试

```python
def test_bmm_basic():
    """测试基本逆向最大匹配"""
    dict = Dictionary()
    dict.add("我", 100)
    dict.add("爱", 100)
    dict.add("北京", 100)
    dict.add("天安门", 100)

    bmm = BMM(dict)
    result = bmm.segment("我爱北京天安门")
    assert result == ["我", "爱", "北京", "天安门"]

def test_bmm_ambiguity():
    """测试歧义处理"""
    dict = Dictionary()
    dict.add("研究", 100)
    dict.add("研究生", 100)
    dict.add("生命", 100)
    dict.add("的", 100)
    dict.add("起源", 100)

    bmm = BMM(dict)
    result = bmm.segment("研究生命的起源")
    # BMM 可能与 FMM 结果不同
    assert result == ["研究", "生命", "的", "起源"]
```

### 4. HMM 测试

#### 训练测试

```python
def test_hmm_train():
    """测试 HMM 训练"""
    hmm = HMM()
    corpus = [
        "我/S 爱/S 北京/B 天安门/E",
        "你/S 好/S"
    ]
    hmm.train(corpus)
    assert len(hmm.start_prob) == 4
    assert len(hmm.trans_prob) == 4
    assert len(hmm.emit_prob) == 4
```

#### 分词测试

```python
def test_hmm_segment():
    """测试 HMM 分词"""
    hmm = HMM()
    # 加载预训练模型或训练
    hmm.load_model("data/hmm_model.json")

    result = hmm.segment("我爱北京天安门")
    assert isinstance(result, list)
    assert len(result) > 0
```

#### 模型保存/加载测试

```python
def test_hmm_save_load():
    """测试模型保存和加载"""
    hmm = HMM()
    # 训练模型
    hmm.train(corpus)

    # 保存模型
    hmm.save_model("test_model.json")

    # 加载模型
    hmm2 = HMM()
    hmm2.load_model("test_model.json")

    # 验证模型参数一致
    assert hmm.start_prob == hmm2.start_prob
    assert hmm.trans_prob == hmm2.trans_prob
```

### 5. Tokenizer 测试

#### 集成测试

```python
def test_tokenizer_integration():
    """测试完整分词流程"""
    tokenizer = Tokenizer()
    tokenizer.load_dictionary("data/dict.txt")

    # 测试 FMM
    fmm_result = tokenizer.fmm("我爱北京天安门")
    assert isinstance(fmm_result, list)

    # 测试 BMM
    bmm_result = tokenizer.bmm("我爱北京天安门")
    assert isinstance(bmm_result, list)

    # 测试 HMM
    hmm_result = tokenizer.hmm("我爱北京天安门")
    assert isinstance(hmm_result, list)
```

## 测试数据

### 标准测试集

```python
TEST_CASES = [
    ("我爱北京天安门", ["我", "爱", "北京", "天安门"]),
    ("研究生命的起源", ["研究", "生命", "的", "起源"]),
    ("中华人民共和国", ["中华人民共和国"]),
    ("今天天气真好", ["今天", "天气", "真", "好"]),
]
```

### 边界测试数据

```python
EDGE_CASES = [
    ("", []),
    ("我", ["我"]),
    ("ab", ["a", "b"]),  # 英文字符
    ("123", ["123"]),     # 数字
]
```

## 运行测试

### 运行所有测试

```bash
pytest tests/
```

### 运行特定测试

```bash
pytest tests/test_fmm.py
pytest tests/test_bmm.py
pytest tests/test_hmm.py
```

### 查看覆盖率

```bash
pytest --cov=src tests/
```

## 测试报告

测试报告将包含：
1. 测试用例总数
2. 通过/失败/跳过数量
3. 覆盖率统计
4. 失败用例详情
