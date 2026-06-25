# 示例图像目录

此目录用于存放 OCR 测试的示例图像。

## 使用方法

将测试图像放在此目录下，然后在代码中引用：

```python
import cv2
image = cv2.imread("examples/sample_images/test.jpg")
```

## 图像要求

- 支持格式：JPG, PNG, BMP
- 建议分辨率：至少 100x100 像素
- 文字清晰可读