"""
文字识别模块

识别单元格中的文字内容。
"""

import logging
from typing import List, Dict, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class TextRecognizer:
    """
    文字识别器

    使用 OCR 技术识别单元格中的文字。
    """

    def __init__(self, engine: str = "easyocr", language: str = "ch_sim+en"):
        """
        初始化文字识别器

        Args:
            engine: OCR 引擎 (easyocr/tesseract)
            language: 识别语言
        """
        self.engine = engine
        self.language = language
        self.reader = None

        # 初始化 OCR 引擎
        self._init_engine()

    def _init_engine(self):
        """初始化 OCR 引擎"""
        if self.engine == "easyocr":
            try:
                import easyocr
                self.reader = easyocr.Reader([self.language])
                logger.info("EasyOCR 初始化成功")
            except ImportError:
                logger.warning("EasyOCR 未安装，使用简单识别")
                self.reader = None
        elif self.engine == "tesseract":
            try:
                import pytesseract
                self.reader = pytesseract
                logger.info("Tesseract 初始化成功")
            except ImportError:
                logger.warning("Tesseract 未安装，使用简单识别")
                self.reader = None

    def recognize(self, cell_image: np.ndarray) -> str:
        """
        识别单元格文字

        Args:
            cell_image: 单元格图像

        Returns:
            识别的文字
        """
        if cell_image is None or cell_image.size == 0:
            return ""

        # 预处理
        processed = self._preprocess(cell_image)

        # 使用对应引擎识别
        if self.engine == "easyocr":
            return self._recognize_easyocr(processed)
        elif self.engine == "tesseract":
            return self._recognize_tesseract(processed)
        else:
            return self._recognize_simple(processed)

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像

        Args:
            image: 输入图像

        Returns:
            预处理后的图像
        """
        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 去噪
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # 二值化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 膨胀使文字更清晰
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)

        return dilated

    def _recognize_easyocr(self, image: np.ndarray) -> str:
        """
        使用 EasyOCR 识别

        Args:
            image: 预处理后的图像

        Returns:
            识别的文字
        """
        if self.reader is None:
            return self._recognize_simple(image)

        try:
            results = self.reader.readtext(image)

            # 拼接结果
            texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.3:
                    texts.append(text)

            return " ".join(texts)
        except Exception as e:
            logger.warning(f"EasyOCR 识别失败: {e}")
            return ""

    def _recognize_tesseract(self, image: np.ndarray) -> str:
        """
        使用 Tesseract 识别

        Args:
            image: 预处理后的图像

        Returns:
            识别的文字
        """
        if self.reader is None:
            return self._recognize_simple(image)

        try:
            # 设置语言
            config = f'--oem 3 --psm 6 -l {self.language}'
            text = self.reader.image_to_string(image, config=config)
            return text.strip()
        except Exception as e:
            logger.warning(f"Tesseract 识别失败: {e}")
            return ""

    def _recognize_simple(self, image: np.ndarray) -> str:
        """
        简单识别（仅用于测试）

        Args:
            image: 预处理后的图像

        Returns:
            占位文字
        """
        # 返回占位符
        return "[文字识别需要安装 OCR 引擎]"

    def batch_recognize(self, cell_images: List[np.ndarray]) -> List[str]:
        """
        批量识别

        Args:
            cell_images: 单元格图像列表

        Returns:
            识别结果列表
        """
        results = []
        for image in cell_images:
            text = self.recognize(image)
            results.append(text)

        return results


class SimpleTextDetector:
    """
    简单文字检测器

    检测单元格中是否包含文字。
    """

    def __init__(self, threshold: float = 0.1):
        """
        初始化文字检测器

        Args:
            threshold: 文字区域比例阈值
        """
        self.threshold = threshold

    def has_text(self, cell_image: np.ndarray) -> bool:
        """
        检测单元格是否包含文字

        Args:
            cell_image: 单元格图像

        Returns:
            是否包含文字
        """
        if cell_image is None or cell_image.size == 0:
            return False

        # 转灰度
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()

        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 计算文字像素比例
        text_ratio = np.sum(binary > 0) / binary.size

        return text_ratio > self.threshold

    def detect_text_regions(self, cell_image: np.ndarray) -> List[Dict]:
        """
        检测文字区域

        Args:
            cell_image: 单元格图像

        Returns:
            文字区域列表
        """
        if cell_image is None or cell_image.size == 0:
            return []

        # 转灰度
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()

        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 膨胀连接文字
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # 查找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            # 过滤太小的区域
            if area < 50:
                continue

            regions.append({
                "bbox": [x, y, x + w, y + h],
                "area": area,
            })

        return regions


class TextLineDetector:
    """
    文字行检测器

    检测单元格中的文字行。
    """

    def __init__(self, min_line_height: int = 5, max_line_height: int = 100):
        """
        初始化文字行检测器

        Args:
            min_line_height: 最小行高
            max_line_height: 最大行高
        """
        self.min_line_height = min_line_height
        self.max_line_height = max_line_height

    def detect_lines(self, cell_image: np.ndarray) -> List[Dict]:
        """
        检测文字行

        Args:
            cell_image: 单元格图像

        Returns:
            文字行列表
        """
        if cell_image is None or cell_image.size == 0:
            return []

        # 转灰度
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()

        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 计算水平投影
        h, w = binary.shape
        projection = np.sum(binary, axis=1) / 255

        # 查找文字行
        lines = []
        in_line = False
        line_start = 0

        for i in range(h):
            if projection[i] > 0 and not in_line:
                # 行开始
                in_line = True
                line_start = i
            elif projection[i] == 0 and in_line:
                # 行结束
                in_line = False
                line_height = i - line_start

                if self.min_line_height <= line_height <= self.max_line_height:
                    lines.append({
                        "y_start": line_start,
                        "y_end": i,
                        "height": line_height,
                    })

        # 处理最后一行
        if in_line:
            line_height = h - line_start
            if self.min_line_height <= line_height <= self.max_line_height:
                lines.append({
                    "y_start": line_start,
                    "y_end": h,
                    "height": line_height,
                })

        return lines
