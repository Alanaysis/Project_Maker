# 设计文档：OCR 文字识别系统

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      OCR 系统架构                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  图像输入  │ → │  预处理   │ → │ 文字检测  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                          ↓                  │
│                    ┌──────────┐    ┌──────────┐            │
│                    │  文本输出  │ ← │ 文字识别  │            │
│                    └──────────┘    └──────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
ocr/
├── detector.py      # 文字检测模块
├── recognizer.py    # 文字识别模块
├── ocr_engine.py    # OCR 引擎（整合检测和识别）
└── utils.py         # 工具函数
```

## 2. 文字检测模块设计

### 2.1 检测器接口

```python
class TextDetector:
    """文字检测器基类"""
    
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        检测图像中的文字区域
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            List[np.ndarray]: 检测到的文字区域坐标列表
                              每个元素为 (4, 2) 的数组，表示四边形的4个顶点
        """
        pass
```

### 2.2 EAST 检测器设计

```python
class EASTDetector(TextDetector):
    """基于 EAST 的文字检测器"""
    
    def __init__(self, model_path: str, input_size: int = 512):
        self.model = self._load_model(model_path)
        self.input_size = input_size
    
    def _load_model(self, model_path: str) -> nn.Module:
        """加载 EAST 模型"""
        pass
    
    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """图像预处理"""
        pass
    
    def _postprocess(self, score_map, geo_map, threshold) -> List[np.ndarray]:
        """后处理：NMS 过滤"""
        pass
    
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """执行检测"""
        pass
```

### 2.3 简化检测器设计

为了学习目的，实现一个简化的文字检测器：

```python
class SimpleTextDetector(TextDetector):
    """基于传统方法的简单文字检测器"""
    
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        # 1. 灰度化
        # 2. 二值化
        # 3. 形态学操作
        # 4. 轮廓检测
        # 5. 矩形框提取
        pass
```

## 3. 文字识别模块设计

### 3.1 CRNN 模型架构

```python
class CRNN(nn.Module):
    """CRNN 文字识别模型"""
    
    def __init__(self, num_classes, hidden_size=256):
        super().__init__()
        
        # CNN 特征提取
        self.cnn = self._build_cnn()
        
        # RNN 序列建模
        self.rnn = nn.LSTM(512, hidden_size, 
                          num_layers=2, 
                          bidirectional=True)
        
        # 全连接层
        self.fc = nn.Linear(hidden_size * 2, num_classes)
    
    def _build_cnn(self) -> nn.Module:
        """构建 CNN 部分"""
        pass
    
    def forward(self, x):
        # CNN 提取特征
        conv = self.cnn(x)
        
        # 转换为序列
        b, c, h, w = conv.size()
        conv = conv.squeeze(2)  # 移除高度维度
        conv = conv.permute(2, 0, 1)  # (W, B, C)
        
        # RNN 处理
        rnn_out, _ = self.rnn(conv)
        
        # 全连接
        output = self.fc(rnn_out)
        
        return output
```

### 3.2 识别器接口

```python
class TextRecognizer:
    """文字识别器"""
    
    def __init__(self, model_path: str, charset: str):
        self.model = self._load_model(model_path)
        self.charset = charset
    
    def recognize(self, image: np.ndarray) -> Tuple[str, float]:
        """
        识别单张文字图像
        
        Args:
            image: 文字图像 (H, W, C)
            
        Returns:
            Tuple[str, float]: (识别结果, 置信度)
        """
        pass
    
    def recognize_batch(self, images: List[np.ndarray]) -> List[Tuple[str, float]]:
        """批量识别"""
        pass
```

### 3.3 CTC 解码器

```python
class CTCDecoder:
    """CTC 解码器"""
    
    def __init__(self, charset: str, blank_idx: int = 0):
        self.charset = charset
        self.blank_idx = blank_idx
    
    def decode(self, logits: torch.Tensor) -> str:
        """
        贪心解码
        
        Args:
            logits: 模型输出 (T, C)
            
        Returns:
            str: 解码后的文本
        """
        pass
    
    def decode_beam(self, logits: torch.Tensor, beam_size: int = 10) -> str:
        """Beam Search 解码"""
        pass
```

## 4. OCR 引擎设计

### 4.1 引擎接口

```python
class OCREngine:
    """OCR 引擎"""
    
    def __init__(self, detector: TextDetector, recognizer: TextRecognizer):
        self.detector = detector
        self.recognizer = recognizer
    
    def process(self, image: np.ndarray) -> List[Dict]:
        """
        处理单张图像
        
        Args:
            image: 输入图像
            
        Returns:
            List[Dict]: 识别结果列表
            [
                {
                    "bbox": np.ndarray,  # 文字区域坐标
                    "text": str,         # 识别文本
                    "confidence": float  # 置信度
                },
                ...
            ]
        """
        pass
```

### 4.2 处理流程

```python
def process(self, image: np.ndarray) -> List[Dict]:
    # 1. 文字检测
    bboxes = self.detector.detect(image)
    
    results = []
    for bbox in bboxes:
        # 2. 裁剪文字区域
        cropped = self._crop_text_region(image, bbox)
        
        # 3. 文字识别
        text, confidence = self.recognizer.recognize(cropped)
        
        results.append({
            "bbox": bbox,
            "text": text,
            "confidence": confidence
        })
    
    return results
```

## 5. 工具函数设计

### 5.1 图像处理工具

```python
def resize_image(image: np.ndarray, max_size: int = 1024) -> np.ndarray:
    """保持宽高比缩放图像"""
    pass

def crop_region(image: np.ndarray, bbox: np.ndarray) -> np.ndarray:
    """根据四边形坐标裁剪区域"""
    pass

def order_points(pts: np.ndarray) -> np.ndarray:
    """排序四边形顶点：左上、右上、右下、左下"""
    pass
```

### 5.2 可视化工具

```python
def draw_bboxes(image: np.ndarray, bboxes: List[np.ndarray], 
                color=(0, 255, 0), thickness=2) -> np.ndarray:
    """绘制检测框"""
    pass

def draw_text(image: np.ndarray, bboxes: List[np.ndarray], 
              texts: List[str]) -> np.ndarray:
    """绘制识别结果"""
    pass
```

## 6. 数据流设计

### 6.1 输入格式

```python
# 图像输入
image: np.ndarray  # shape: (H, W, C), dtype: uint8, BGR格式

# 批量输入
images: List[np.ndarray]
```

### 6.2 输出格式

```python
# 单图结果
result = {
    "image_path": str,
    "results": [
        {
            "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
            "text": "Hello World",
            "confidence": 0.95
        }
    ]
}

# 批量结果
results: List[Dict]
```

## 7. 错误处理设计

### 7.1 异常类型

```python
class OCRError(Exception):
    """OCR 基础异常"""
    pass

class DetectionError(OCRError):
    """检测错误"""
    pass

class RecognitionError(OCRError):
    """识别错误"""
    pass

class ModelLoadError(OCRError):
    """模型加载错误"""
    pass
```

### 7.2 错误处理策略

```python
def process_safe(self, image: np.ndarray) -> List[Dict]:
    """安全处理，捕获异常"""
    try:
        return self.process(image)
    except DetectionError as e:
        logger.error(f"Detection failed: {e}")
        return []
    except RecognitionError as e:
        logger.error(f"Recognition failed: {e}")
        return []
```

## 8. 性能优化设计

### 8.1 批处理

```python
def process_batch(self, images: List[np.ndarray]) -> List[List[Dict]]:
    """批量处理，提高 GPU 利用率"""
    pass
```

### 8.2 模型优化

```python
# 模型量化
model = torch.quantization.quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8)

# 模型导出
torch.onnx.export(model, dummy_input, "model.onnx")
```

### 8.3 缓存机制

```python
class OCRPipeline:
    def __init__(self):
        self._model_cache = {}
    
    def get_model(self, model_name: str):
        if model_name not in self._model_cache:
            self._model_cache[model_name] = self._load_model(model_name)
        return self._model_cache[model_name]
```

## 9. 配置管理设计

### 9.1 配置类

```python
@dataclass
class OCRConfig:
    # 检测配置
    detector_type: str = "simple"
    detector_model_path: str = ""
    detection_threshold: float = 0.5
    
    # 识别配置
    recognizer_model_path: str = ""
    charset: str = "0123456789abcdefghijklmnopqrstuvwxyz"
    recognizer_height: int = 32
    
    # 通用配置
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    max_batch_size: int = 32
```

## 10. 扩展性设计

### 10.1 插件式检测器

```python
# 检测器注册
DETECTORS = {
    "simple": SimpleTextDetector,
    "east": EASTDetector,
    "ctpn": CTPNDetector,
}

def create_detector(config: OCRConfig) -> TextDetector:
    detector_class = DETECTORS[config.detector_type]
    return detector_class(**config.detector_params)
```

### 10.2 自定义字符集

```python
class Charset:
    """字符集管理"""
    
    def __init__(self, chars: str):
        self.chars = chars
        self.char_to_idx = {c: i for i, c in enumerate(chars)}
        self.idx_to_char = {i: c for i, c in enumerate(chars)}
    
    @classmethod
    def from_file(cls, path: str):
        """从文件加载字符集"""
        pass
```