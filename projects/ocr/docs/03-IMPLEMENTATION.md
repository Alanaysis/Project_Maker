# 实现文档：OCR 文字识别系统

## 1. 环境配置

### 1.1 依赖安装

```bash
pip install torch torchvision opencv-python numpy Pillow matplotlib pytest
```

### 1.2 验证安装

```python
import torch
import cv2
import numpy as np

print(f"PyTorch: {torch.__version__}")
print(f"OpenCV: {cv2.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
```

## 2. 工具函数实现

### 2.1 utils.py

```python
"""OCR 工具函数"""

import cv2
import numpy as np
from typing import List, Tuple


def resize_image(image: np.ndarray, max_size: int = 1024) -> np.ndarray:
    """保持宽高比缩放图像"""
    h, w = image.shape[:2]
    scale = min(max_size / max(h, w), 1.0)
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h))
    return image


def order_points(pts: np.ndarray) -> np.ndarray:
    """排序四边形顶点：左上、右上、右下、左下"""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def crop_text_region(image: np.ndarray, bbox: np.ndarray, 
                     target_height: int = 32) -> np.ndarray:
    """根据四边形坐标裁剪文字区域"""
    bbox = order_points(bbox)
    
    # 计算目标尺寸
    width_a = np.linalg.norm(bbox[1] - bbox[0])
    width_b = np.linalg.norm(bbox[2] - bbox[3])
    max_width = max(int(width_a), int(width_b))
    
    height_a = np.linalg.norm(bbox[3] - bbox[0])
    height_b = np.linalg.norm(bbox[2] - bbox[1])
    max_height = max(int(height_a), int(height_b))
    
    # 目标点
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype=np.float32)
    
    # 透视变换
    M = cv2.getPerspectiveTransform(bbox, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    
    # 调整到目标高度
    if warped.shape[0] != target_height:
        scale = target_height / warped.shape[0]
        new_width = int(warped.shape[1] * scale)
        warped = cv2.resize(warped, (new_width, target_height))
    
    return warped


def draw_bboxes(image: np.ndarray, bboxes: List[np.ndarray],
                color=(0, 255, 0), thickness: int = 2) -> np.ndarray:
    """绘制检测框"""
    vis = image.copy()
    for bbox in bboxes:
        pts = bbox.astype(np.int32)
        cv2.polylines(vis, [pts], True, color, thickness)
    return vis


def draw_results(image: np.ndarray, results: List[dict]) -> np.ndarray:
    """绘制识别结果"""
    vis = image.copy()
    for result in results:
        bbox = result["bbox"].astype(np.int32)
        text = result["text"]
        conf = result["confidence"]
        
        # 绘制框
        cv2.polylines(vis, [bbox], True, (0, 255, 0), 2)
        
        # 绘制文本
        x, y = bbox[0]
        label = f"{text} ({conf:.2f})"
        cv2.putText(vis, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return vis


def normalize_image(image: np.ndarray, 
                    mean: Tuple[float, ...] = (0.485, 0.456, 0.406),
                    std: Tuple[float, ...] = (0.229, 0.224, 0.225)) -> np.ndarray:
    """图像归一化"""
    image = image.astype(np.float32) / 255.0
    image = (image - mean) / std
    return image


def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """计算两个矩形框的 IoU"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0


def nms(boxes: np.ndarray, scores: np.ndarray, 
        threshold: float = 0.5) -> List[int]:
    """非极大值抑制"""
    if len(boxes) == 0:
        return []
    
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        intersection = w * h
        
        iou = intersection / (areas[i] + areas[order[1:]] - intersection)
        
        inds = np.where(iou <= threshold)[0]
        order = order[inds + 1]
    
    return keep
```

## 3. 文字检测模块实现

### 3.1 detector.py

```python
"""文字检测模块"""

import cv2
import numpy as np
from typing import List


class TextDetector:
    """文字检测器基类"""
    
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        raise NotImplementedError


class SimpleTextDetector(TextDetector):
    """基于传统方法的简单文字检测器"""
    
    def __init__(self, min_area: int = 100, max_area: int = 100000):
        self.min_area = min_area
        self.max_area = max_area
    
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        检测图像中的文字区域
        
        实现步骤：
        1. 灰度化
        2. 高斯模糊
        3. 自适应二值化
        4. 形态学操作
        5. 轮廓检测
        6. 矩形框提取
        """
        # 灰度化
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 自适应二值化
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # 形态学操作：连接相邻文字
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # 轮廓检测
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 提取文字区域
        bboxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_area < area < self.max_area:
                # 获取最小外接矩形
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                bboxes.append(box)
        
        return bboxes


class EASTTextDetector(TextDetector):
    """基于 EAST 的文字检测器（需要预训练模型）"""
    
    def __init__(self, model_path: str, input_size: int = 512,
                 confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.4):
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        
        # 加载模型
        self.net = cv2.dnn.readNet(model_path)
    
    def detect(self, image: np.ndarray) -> List[np.ndarray]:
        """
        使用 EAST 模型检测文字
        
        注意：需要预训练的 EAST 模型文件
        """
        orig_h, orig_w = image.shape[:2]
        
        # 预处理
        blob = cv2.dnn.blobFromImage(
            image, 1.0, (self.input_size, self.input_size),
            (123.68, 116.78, 103.94), True, False
        )
        
        # 前向传播
        self.net.setInput(blob)
        scores, geometry = self.net.forward([
            "feature_fusion/Conv_7/Sigmoid",
            "feature_fusion/concat_3"
        ])
        
        # 解码检测结果
        bboxes, confidences = self._decode(scores, geometry)
        
        # NMS
        indices = cv2.dnn.NMSBoxesRotated(
            bboxes, confidences,
            self.confidence_threshold,
            self.nms_threshold
        )
        
        # 转换坐标
        results = []
        for i in indices:
            bbox = bboxes[i[0]]
            # 转换为四边形坐标
            pts = self._rotated_rect_to_points(bbox, orig_w, orig_h)
            results.append(pts)
        
        return results
    
    def _decode(self, scores, geometry):
        """解码 EAST 输出"""
        # 实现省略，需要处理 EAST 的输出格式
        pass
    
    def _rotated_rect_to_points(self, bbox, orig_w, orig_h):
        """将旋转矩形转换为四边形点"""
        # 实现省略
        pass
```

## 4. 文字识别模块实现

### 4.1 recognizer.py

```python
"""文字识别模块 - CRNN 实现"""

import torch
import torch.nn as nn
from typing import List, Tuple
import numpy as np


class CRNN(nn.Module):
    """CRNN 文字识别模型"""
    
    def __init__(self, num_classes: int, hidden_size: int = 256):
        super().__init__()
        
        # CNN 特征提取
        self.cnn = nn.Sequential(
            # conv1
            nn.Conv2d(1, 64, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),
            
            # conv2
            nn.Conv2d(64, 128, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),
            
            # conv3
            nn.Conv2d(128, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            
            # conv4
            nn.Conv2d(256, 256, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),
            
            # conv5
            nn.Conv2d(256, 512, 3, 1, 1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            
            # conv6
            nn.Conv2d(512, 512, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),
            
            # conv7
            nn.Conv2d(512, 512, 2, 1, 0),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
        )
        
        # RNN 序列建模
        self.rnn = nn.LSTM(
            input_size=512,
            hidden_size=hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False
        )
        
        # 全连接层
        self.fc = nn.Linear(hidden_size * 2, num_classes)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入图像 (B, 1, H, W)
            
        Returns:
            输出序列 (T, B, num_classes)
        """
        # CNN 特征提取
        conv = self.cnn(x)
        
        # 转换为序列格式
        b, c, h, w = conv.size()
        assert h == 1, "高度应为1"
        conv = conv.squeeze(2)  # (B, C, W)
        conv = conv.permute(2, 0, 1)  # (W, B, C) = (T, B, C)
        
        # RNN 处理
        rnn_out, _ = self.rnn(conv)
        
        # 全连接
        output = self.fc(rnn_out)
        
        return output


class CTCDecoder:
    """CTC 解码器"""
    
    def __init__(self, charset: str, blank_idx: int = 0):
        """
        Args:
            charset: 字符集
            blank_idx: blank 标签索引
        """
        self.charset = charset
        self.blank_idx = blank_idx
    
    def greedy_decode(self, logits: torch.Tensor) -> str:
        """
        贪心解码
        
        Args:
            logits: 模型输出 (T, C)
            
        Returns:
            解码后的文本
        """
        # 获取最大概率的字符
        _, indices = torch.max(logits, dim=1)
        indices = indices.cpu().numpy()
        
        # 去重和去 blank
        chars = []
        prev_idx = -1
        for idx in indices:
            if idx != self.blank_idx and idx != prev_idx:
                chars.append(self.charset[idx])
            prev_idx = idx
        
        return ''.join(chars)
    
    def beam_search_decode(self, logits: torch.Tensor, 
                          beam_size: int = 10) -> str:
        """Beam Search 解码"""
        # 简化实现，实际应使用更复杂的 beam search
        return self.greedy_decode(logits)


class TextRecognizer:
    """文字识别器"""
    
    def __init__(self, model_path: str = None, charset: str = None,
                 input_height: int = 32, device: str = "cpu"):
        """
        Args:
            model_path: 模型路径
            charset: 字符集
            input_height: 输入图像高度
            device: 设备
        """
        self.input_height = input_height
        self.device = device
        
        # 默认字符集
        if charset is None:
            charset = "0123456789abcdefghijklmnopqrstuvwxyz"
        self.charset = charset
        
        # 创建模型
        num_classes = len(charset) + 1  # +1 for blank
        self.model = CRNN(num_classes)
        
        # 加载模型权重
        if model_path is not None:
            self.model.load_state_dict(torch.load(model_path, map_location=device))
        
        self.model.to(device)
        self.model.eval()
        
        # 创建解码器
        self.decoder = CTCDecoder(charset)
    
    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        预处理图像
        
        Args:
            image: 输入图像 (H, W, C) 或 (H, W)
            
        Returns:
            预处理后的张量 (1, 1, H, W)
        """
        # 灰度化
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 调整大小
        h, w = gray.shape
        new_w = int(w * self.input_height / h)
        resized = cv2.resize(gray, (new_w, self.input_height))
        
        # 归一化
        normalized = resized.astype(np.float32) / 255.0
        normalized = (normalized - 0.5) / 0.5
        
        # 转换为张量
        tensor = torch.from_numpy(normalized).unsqueeze(0).unsqueeze(0)
        return tensor.to(self.device)
    
    def recognize(self, image: np.ndarray) -> Tuple[str, float]:
        """
        识别文字
        
        Args:
            image: 输入图像
            
        Returns:
            (识别文本, 置信度)
        """
        # 预处理
        input_tensor = self.preprocess(image)
        
        # 前向传播
        with torch.no_grad():
            output = self.model(input_tensor)
        
        # 解码
        text = self.decoder.greedy_decode(output.squeeze(1))
        
        # 计算置信度
        probs = torch.softmax(output, dim=2)
        confidence = probs.max().item()
        
        return text, confidence
    
    def recognize_batch(self, images: List[np.ndarray]) -> List[Tuple[str, float]]:
        """批量识别"""
        results = []
        for image in images:
            text, conf = self.recognize(image)
            results.append((text, conf))
        return results
```

## 5. OCR 引擎实现

### 5.1 ocr_engine.py

```python
"""OCR 引擎"""

import numpy as np
from typing import List, Dict
from .detector import TextDetector, SimpleTextDetector
from .recognizer import TextRecognizer
from .utils import crop_text_region


class OCREngine:
    """OCR 引擎"""
    
    def __init__(self, detector: TextDetector = None, 
                 recognizer: TextRecognizer = None):
        """
        Args:
            detector: 文字检测器
            recognizer: 文字识别器
        """
        self.detector = detector or SimpleTextDetector()
        self.recognizer = recognizer or TextRecognizer()
    
    def process(self, image: np.ndarray) -> List[Dict]:
        """
        处理单张图像
        
        Args:
            image: 输入图像 (H, W, C)
            
        Returns:
            识别结果列表
        """
        # 文字检测
        bboxes = self.detector.detect(image)
        
        results = []
        for bbox in bboxes:
            # 裁剪文字区域
            cropped = crop_text_region(image, bbox)
            
            # 文字识别
            text, confidence = self.recognizer.recognize(cropped)
            
            if text:  # 过滤空结果
                results.append({
                    "bbox": bbox,
                    "text": text,
                    "confidence": confidence
                })
        
        return results
    
    def process_batch(self, images: List[np.ndarray]) -> List[List[Dict]]:
        """批量处理"""
        all_results = []
        for image in images:
            results = self.process(image)
            all_results.append(results)
        return all_results
    
    def visualize(self, image: np.ndarray, results: List[Dict]) -> np.ndarray:
        """可视化结果"""
        from .utils import draw_results
        return draw_results(image, results)
```

## 6. 评估模块实现

### 6.1 evaluator.py

```python
"""评估模块"""

import numpy as np
from typing import List, Dict, Tuple


class OCREvaluator:
    """OCR 评估器"""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, pred: str, gt: str):
        """添加预测结果"""
        self.results.append((pred, gt))
    
    def compute_char_accuracy(self) -> float:
        """计算字符准确率"""
        correct = 0
        total = 0
        for pred, gt in self.results:
            for p, g in zip(pred, gt):
                if p == g:
                    correct += 1
            total += max(len(pred), len(gt))
        return correct / total if total > 0 else 0
    
    def compute_word_accuracy(self) -> float:
        """计算词准确率"""
        correct = sum(1 for pred, gt in self.results if pred == gt)
        return correct / len(self.results) if self.results else 0
    
    def compute_edit_distance(self, pred: str, gt: str) -> int:
        """计算编辑距离"""
        m, n = len(pred), len(gt)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if pred[i-1] == gt[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
        
        return dp[m][n]
    
    def compute_normalized_edit_distance(self) -> float:
        """计算归一化编辑距离"""
        total_distance = 0
        total_length = 0
        for pred, gt in self.results:
            total_distance += self.compute_edit_distance(pred, gt)
            total_length += len(gt)
        return total_distance / total_length if total_length > 0 else 0
    
    def compute_detection_metrics(self, pred_boxes: List[np.ndarray],
                                   gt_boxes: List[np.ndarray],
                                   iou_threshold: float = 0.5) -> Dict:
        """计算检测指标"""
        tp = 0
        fp = 0
        fn = len(gt_boxes)
        
        for pred_box in pred_boxes:
            matched = False
            for gt_box in gt_boxes:
                iou = self._compute_iou(pred_box, gt_box)
                if iou >= iou_threshold:
                    matched = True
                    break
            if matched:
                tp += 1
                fn -= 1
            else:
                fp += 1
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    
    def _compute_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """计算 IoU"""
        # 简化为矩形框 IoU
        x1 = max(box1[:, 0].min(), box2[:, 0].min())
        y1 = max(box1[:, 1].min(), box2[:, 1].min())
        x2 = min(box1[:, 0].max(), box2[:, 0].max())
        y2 = min(box1[:, 1].max(), box2[:, 1].max())
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = self._polygon_area(box1)
        area2 = self._polygon_area(box2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _polygon_area(self, pts: np.ndarray) -> float:
        """计算多边形面积"""
        n = len(pts)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        return abs(area) / 2
    
    def summary(self) -> Dict:
        """生成评估报告"""
        return {
            "char_accuracy": self.compute_char_accuracy(),
            "word_accuracy": self.compute_word_accuracy(),
            "normalized_edit_distance": self.compute_normalized_edit_distance(),
            "num_samples": len(self.results)
        }
```

## 7. 训练脚本实现

### 7.1 train.py

```python
"""CRNN 训练脚本"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from .recognizer import CRNN


def train(model: CRNN, train_loader: DataLoader, 
          val_loader: DataLoader, epochs: int = 100,
          lr: float = 0.001, device: str = "cpu"):
    """训练 CRNN 模型"""
    
    model = model.to(device)
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        # 训练
        model.train()
        train_loss = 0
        for images, targets, input_lengths, target_lengths in train_loader:
            images = images.to(device)
            
            # 前向传播
            outputs = model(images)
            log_probs = torch.nn.functional.log_softmax(outputs, dim=2)
            
            # 计算损失
            loss = criterion(log_probs, targets, input_lengths, target_lengths)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        # 验证
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, targets, input_lengths, target_lengths in val_loader:
                images = images.to(device)
                outputs = model(images)
                log_probs = torch.nn.functional.log_softmax(outputs, dim=2)
                loss = criterion(log_probs, targets, input_lengths, target_lengths)
                val_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{epochs}, "
              f"Train Loss: {train_loss/len(train_loader):.4f}, "
              f"Val Loss: {val_loss/len(val_loader):.4f}")


if __name__ == "__main__":
    # 示例训练代码
    model = CRNN(num_classes=63)  # 62字符 + blank
    train_loader = None  # 需要准备数据集
    val_loader = None
    
    if train_loader:
        train(model, train_loader, val_loader)
```