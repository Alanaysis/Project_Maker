"""
Correlation Filter for Object Tracking

相关滤波跟踪器实现，基于MOSSE (Minimum Output Sum of Squared Error) 算法。

核心原理:
- 在频域中学习滤波模板
- 使用循环移位生成训练样本
- 通过FFT快速计算相关响应
- 在响应峰值处定位目标

优势:
- 计算效率高 (FFT加速)
- 实时性能好
- 对光照变化有一定鲁棒性
"""

import numpy as np
import cv2
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class TrackingResult:
    """跟踪结果"""
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float
    center: Tuple[float, float]


class MOSSETracker:
    """MOSSE相关滤波跟踪器

    使用最小输出平方误差和准则训练滤波模板。
    """

    def __init__(
        self,
        learning_rate: float = 0.125,
        sigma: float = 2.0,
        padding: float = 2.0,
        psr_threshold: float = 8.0
    ):
        """初始化MOSSE跟踪器

        Args:
            learning_rate: 模型更新学习率
            sigma: 高斯响应的标准差
            padding: 搜索区域的填充比例
            psr_threshold: PSR阈值，低于此值认为跟踪失败
        """
        self.learning_rate = learning_rate
        self.sigma = sigma
        self.padding = padding
        self.psr_threshold = psr_threshold

        # 滤波模板 (频域)
        self.H: Optional[np.ndarray] = None
        self.H_num: Optional[np.ndarray] = None  # 分子
        self.H_den: Optional[np.ndarray] = None  # 分母

        # 目标区域
        self.bbox: Optional[Tuple[int, int, int, int]] = None
        self.center: Optional[Tuple[float, float]] = None
        self.size: Optional[Tuple[int, int]] = None

        # 搜索区域大小
        self.search_size: Optional[Tuple[int, int]] = None

        self.initialized = False

    def _get_search_region(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """获取搜索区域

        Args:
            frame: 输入帧
            bbox: 目标边界框 (x, y, w, h)

        Returns:
            搜索区域图像 (灰度)
        """
        # 转换为灰度图
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        x, y, w, h = bbox
        cx, cy = x + w // 2, y + h // 2

        # 计算搜索区域大小 (带填充)
        search_w = int(w * (1 + self.padding))
        search_h = int(h * (1 + self.padding))

        # 确保为偶数 (FFT要求)
        search_w = search_w if search_w % 2 == 0 else search_w + 1
        search_h = search_h if search_h % 2 == 0 else search_h + 1

        self.search_size = (search_w, search_h)

        # 提取区域 (带边界处理)
        x1 = max(0, cx - search_w // 2)
        y1 = max(0, cy - search_h // 2)
        x2 = min(gray.shape[1], cx + search_w // 2)
        y2 = min(gray.shape[0], cy + search_h // 2)

        region = gray[y1:y2, x1:x2]

        # 如果区域小于搜索大小，进行填充
        if region.shape[0] < search_h or region.shape[1] < search_w:
            padded = np.zeros((search_h, search_w), dtype=gray.dtype)
            dy = (search_h - region.shape[0]) // 2
            dx = (search_w - region.shape[1]) // 2
            padded[dy:dy+region.shape[0], dx:dx+region.shape[1]] = region
            region = padded

        return region

    def _preprocess(self, patch: np.ndarray) -> np.ndarray:
        """预处理图像块

        - 转换为浮点数
        - 对数变换增强对比度
        - 归一化

        Args:
            patch: 输入图像块

        Returns:
            预处理后的图像块
        """
        # 转换为灰度图
        if len(patch.shape) == 3:
            patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

        patch = patch.astype(np.float64)

        # 对数变换
        patch = np.log(patch + 1.0)

        # 归一化 (零均值单位方差)
        mean = np.mean(patch)
        std = np.std(patch)
        if std > 0:
            patch = (patch - mean) / std

        return patch

    def _create_gaussian_response(
        self,
        size: Tuple[int, int],
        center: Tuple[float, float]
    ) -> np.ndarray:
        """创建高斯响应图

        Args:
            size: 响应图大小 (h, w)
            center: 峰值中心位置

        Returns:
            高斯响应图
        """
        w, h = size
        cx, cy = center

        x = np.arange(w) - cx
        y = np.arange(h) - cy
        xx, yy = np.meshgrid(x, y)

        response = np.exp(-(xx**2 + yy**2) / (2 * self.sigma**2))
        return response

    def init(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> bool:
        """初始化跟踪器

        Args:
            frame: 初始帧
            bbox: 初始目标边界框 (x, y, w, h)

        Returns:
            初始化是否成功
        """
        self.bbox = bbox
        x, y, w, h = bbox
        self.center = (x + w / 2, y + h / 2)
        self.size = (w, h)

        # 获取搜索区域
        search_region = self._get_search_region(frame, bbox)
        patch = self._preprocess(search_region)

        # 创建目标响应 (高斯峰在目标中心)
        search_w, search_h = self.search_size
        target_cx = search_w // 2 + (self.center[0] - (x + w // 2))
        target_cy = search_h // 2 + (self.center[1] - (y + h // 2))

        response = self._create_gaussian_response(
            (search_w, search_h),
            (target_cx, target_cy)
        )

        # FFT
        F = np.fft.fft2(patch)
        G = np.fft.fft2(response)

        # 计算初始滤波模板
        self.H_num = G * np.conj(F)
        self.H_den = F * np.conj(F)
        self.H = self.H_num / (self.H_den + 1e-5)

        self.initialized = True
        return True

    def update(self, frame: np.ndarray) -> TrackingResult:
        """更新跟踪

        Args:
            frame: 当前帧

        Returns:
            跟踪结果
        """
        if not self.initialized:
            raise RuntimeError("Tracker not initialized. Call init() first.")

        # 获取搜索区域
        search_region = self._get_search_region(frame, self.bbox)
        patch = self._preprocess(search_region)

        # FFT
        F = np.fft.fft2(patch)

        # 相关响应 (频域相乘)
        response_fft = self.H * F
        response = np.real(np.fft.ifft2(response_fft))

        # 找到峰值位置
        max_val = np.max(response)
        max_pos = np.unravel_index(np.argmax(response), response.shape)

        # 计算PSR (Peak-to-Sidelobe Ratio)
        psr = self._compute_psr(response, max_pos)

        # 计算位移
        search_w, search_h = self.search_size

        # 处理环绕 (FFT的周期性)
        dy = max_pos[0]
        dx = max_pos[1]
        if dy > search_h // 2:
            dy -= search_h
        if dx > search_w // 2:
            dx -= search_w

        # 更新中心位置
        new_cx = self.center[0] + dx
        new_cy = self.center[1] + dy

        # 更新边界框
        w, h = self.size
        new_x = int(new_cx - w / 2)
        new_y = int(new_cy - h / 2)
        self.bbox = (new_x, new_y, w, h)
        self.center = (new_cx, new_cy)

        # 更新滤波模板
        if psr > self.psr_threshold:
            # 重新计算响应
            response_target = self._create_gaussian_response(
                (search_w, search_h),
                (search_w // 2, search_h // 2)
            )
            G = np.fft.fft2(response_target)

            self.H_num = self.learning_rate * (G * np.conj(F)) + \
                         (1 - self.learning_rate) * self.H_num
            self.H_den = self.learning_rate * (F * np.conj(F)) + \
                         (1 - self.learning_rate) * self.H_den
            self.H = self.H_num / (self.H_den + 1e-5)

        return TrackingResult(
            bbox=self.bbox,
            confidence=psr,
            center=self.center
        )

    def _compute_psr(
        self,
        response: np.ndarray,
        peak_pos: Tuple[int, int]
    ) -> float:
        """计算峰值旁瓣比 (PSR)

        PSR = (peak - mean_sideloeb) / std_sideloeb

        Args:
            response: 相关响应图
            peak_pos: 峰值位置

        Returns:
            PSR值
        """
        peak = response[peak_pos]

        # 创建旁瓣掩码 (排除峰值周围的区域)
        mask = np.ones_like(response, dtype=bool)
        h, w = response.shape
        y, x = peak_pos

        # 自适应半径 (响应图大小的1/4，至少为1)
        r = max(1, min(h, w) // 4)

        y1 = max(0, y - r)
        y2 = min(h, y + r + 1)
        x1 = max(0, x - r)
        x2 = min(w, x + r + 1)
        mask[y1:y2, x1:x2] = False

        # 计算旁瓣统计
        sidelobe = response[mask]
        if len(sidelobe) == 0:
            return 0.0

        mean_sidelobe = np.mean(sidelobe)
        std_sidelobe = np.std(sidelobe)

        if std_sidelobe < 1e-7:
            return 0.0

        psr = (peak - mean_sidelobe) / std_sidelobe
        return float(psr)


class KCFTracker:
    """KCF (Kernelized Correlation Filter) 跟踪器

    使用核化相关滤波进行目标跟踪。
    支持HOG特征和灰度特征。
    """

    def __init__(
        self,
        learning_rate: float = 0.0125,
        sigma: float = 0.6,
        lambda_reg: float = 1e-4,
        padding: float = 2.5,
        interp_factor: float = 0.075,
        cell_size: int = 4
    ):
        """初始化KCF跟踪器

        Args:
            learning_rate: 模型更新学习率
            sigma: 高斯核带宽
            lambda_reg: 正则化参数
            padding: 搜索区域填充比例
            interp_factor: 插值因子
            cell_size: HOG cell大小
        """
        self.learning_rate = learning_rate
        self.sigma = sigma
        self.lambda_reg = lambda_reg
        self.padding = padding
        self.interp_factor = interp_factor
        self.cell_size = cell_size

        # 模型参数
        self.alphaf: Optional[np.ndarray] = None
        self.model_x: Optional[np.ndarray] = None

        # 目标信息
        self.bbox: Optional[Tuple[int, int, int, int]] = None
        self.center: Optional[Tuple[float, float]] = None
        self.size: Optional[Tuple[int, int]] = None
        self.search_size: Optional[Tuple[int, int]] = None

        self.initialized = False

    def _get_features(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """提取特征

        Args:
            frame: 输入帧
            bbox: 目标边界框

        Returns:
            特征图
        """
        x, y, w, h = bbox
        cx, cy = x + w // 2, y + h // 2

        # 搜索区域
        search_w = int(w * (1 + self.padding))
        search_h = int(h * (1 + self.padding))

        # 确保大小合适
        search_w = max(search_w, 2 * self.cell_size)
        search_h = max(search_h, 2 * self.cell_size)

        self.search_size = (search_w, search_h)

        # 提取区域
        x1 = max(0, cx - search_w // 2)
        y1 = max(0, cy - search_h // 2)
        x2 = min(frame.shape[1], cx + search_w // 2)
        y2 = min(frame.shape[0], cy + search_h // 2)

        # 创建搜索窗口
        search_window = np.zeros((search_h, search_w), dtype=np.uint8)
        src = frame[y1:y2, x1:x2]
        if len(src.shape) == 3:
            src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

        dy = (search_h - src.shape[0]) // 2
        dx = (search_w - src.shape[1]) // 2
        search_window[dy:dy+src.shape[0], dx:dx+src.shape[1]] = src

        # 提取HOG特征
        features = self._extract_hog(search_window)
        return features

    def _extract_hog(self, patch: np.ndarray) -> np.ndarray:
        """提取HOG特征

        简化版本：使用梯度直方图

        Args:
            patch: 灰度图像块

        Returns:
            HOG特征图
        """
        patch = patch.astype(np.float64)

        # 计算梯度
        gx = cv2.Sobel(patch, cv2.CV_64F, 1, 0, ksize=1)
        gy = cv2.Sobel(patch, cv2.CV_64F, 0, 1, ksize=1)

        # 梯度幅值和方向
        magnitude = np.sqrt(gx**2 + gy**2)
        orientation = np.arctan2(gy, gx) * 180 / np.pi
        orientation[orientation < 0] += 180

        # 分块计算直方图
        h, w = patch.shape
        cell_h, cell_w = self.cell_size, self.cell_size
        n_cells_y = h // cell_h
        n_cells_x = w // cell_w
        n_bins = 9

        features = np.zeros((n_cells_y, n_cells_x, n_bins))

        for i in range(n_cells_y):
            for j in range(n_cells_x):
                cell_mag = magnitude[i*cell_h:(i+1)*cell_h,
                                     j*cell_w:(j+1)*cell_w]
                cell_ori = orientation[i*cell_h:(i+1)*cell_h,
                                       j*cell_w:(j+1)*cell_w]

                for m in range(cell_h):
                    for n in range(cell_w):
                        bin_idx = int(cell_ori[m, n] * n_bins / 180)
                        bin_idx = min(bin_idx, n_bins - 1)
                        features[i, j, bin_idx] += cell_mag[m, n]

        # L2归一化
        features = features.reshape(-1)
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm

        return features

    def _gaussian_kernel(
        self,
        x1: np.ndarray,
        x2: np.ndarray
    ) -> np.ndarray:
        """计算高斯核

        K(x1, x2) = exp(-1/sigma^2 * (||x1||^2 + ||x2||^2 - 2*x1*x2))

        Args:
            x1: 特征向量1
            x2: 特征向量2

        Returns:
            核矩阵
        """
        if x1.ndim == 1:
            x1 = x1.reshape(1, -1)
        if x2.ndim == 1:
            x2 = x2.reshape(1, -1)

        n1 = x1.shape[0]
        n2 = x2.shape[0]

        xx = np.sum(x1**2, axis=1).reshape(-1, 1)
        yy = np.sum(x2**2, axis=1).reshape(1, -1)
        xy = x1 @ x2.T

        d = xx + yy - 2 * xy
        k = np.exp(-1 / (self.sigma**2) * np.abs(d) / d.size)

        return k

    def init(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> bool:
        """初始化跟踪器

        Args:
            frame: 初始帧
            bbox: 初始目标边界框 (x, y, w, h)

        Returns:
            初始化是否成功
        """
        self.bbox = bbox
        x, y, w, h = bbox
        self.center = (x + w / 2, y + h / 2)
        self.size = (w, h)

        # 提取特征
        features = self._get_features(frame, bbox)

        # 创建训练标签 (高斯响应)
        search_w, search_h = self.search_size
        n_cells_y = search_h // self.cell_size
        n_cells_x = search_w // self.cell_size

        # 高斯标签
        y_label = self._create_gaussian_label(n_cells_x, n_cells_y)

        # 训练初始模型
        k = self._gaussian_kernel(features, features)
        alphaf = np.fft.fft2(y_label) / (np.fft.fft2(k) + self.lambda_reg)

        self.alphaf = alphaf
        self.model_x = features

        self.initialized = True
        return True

    def _create_gaussian_label(
        self,
        width: int,
        height: int
    ) -> np.ndarray:
        """创建高斯标签

        Args:
            width: 宽度
            height: 高度

        Returns:
            高斯标签
        """
        x = np.arange(width) - width // 2
        y = np.arange(height) - height // 2
        xx, yy = np.meshgrid(x, y)

        sigma = max(width, height) / 10.0
        label = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        return label

    def update(self, frame: np.ndarray) -> TrackingResult:
        """更新跟踪

        Args:
            frame: 当前帧

        Returns:
            跟踪结果
        """
        if not self.initialized:
            raise RuntimeError("Tracker not initialized. Call init() first.")

        # 提取特征
        features = self._get_features(frame, self.bbox)

        # 检测
        k = self._gaussian_kernel(features, self.model_x)
        response = np.real(np.fft.ifft2(self.alphaf * np.fft.fft2(k)))

        # 找到峰值
        max_pos = np.unravel_index(np.argmax(response), response.shape)
        max_val = np.max(response)

        # 计算位移
        n_cells_y, n_cells_x = response.shape
        dy = max_pos[0] - n_cells_y // 2
        dx = max_pos[1] - n_cells_x // 2

        # 转换为像素位移
        pixel_dy = dy * self.cell_size
        pixel_dx = dx * self.cell_size

        # 更新位置
        new_cx = self.center[0] + pixel_dx
        new_cy = self.center[1] + pixel_dy

        w, h = self.size
        new_x = int(new_cx - w / 2)
        new_y = int(new_cy - h / 2)
        self.bbox = (new_x, new_y, w, h)
        self.center = (new_cx, new_cy)

        # 更新模型
        new_features = self._get_features(frame, self.bbox)
        k_new = self._gaussian_kernel(new_features, new_features)
        y_label = self._create_gaussian_label(n_cells_x, n_cells_y)
        new_alphaf = np.fft.fft2(y_label) / (np.fft.fft2(k_new) + self.lambda_reg)

        self.alphaf = (1 - self.interp_factor) * self.alphaf + \
                      self.interp_factor * new_alphaf
        self.model_x = (1 - self.interp_factor) * self.model_x + \
                       self.interp_factor * new_features

        return TrackingResult(
            bbox=self.bbox,
            confidence=float(max_val),
            center=self.center
        )


if __name__ == "__main__":
    # 简单测试
    print("相关滤波跟踪器测试")
    print("=" * 50)

    # 创建合成测试序列
    frame_size = (300, 400)
    target_size = (40, 40)

    # 目标轨迹
    positions = [(100 + 3*i, 150 + 2*i) for i in range(30)]

    # 创建MOSSE跟踪器
    tracker = MOSSETracker(learning_rate=0.2)

    # 模拟跟踪
    for i, (cx, cy) in enumerate(positions):
        # 创建帧
        frame = np.zeros((*frame_size, 3), dtype=np.uint8)
        w, h = target_size

        # 绘制目标 (白色矩形)
        x1, y1 = int(cx - w/2), int(cy - h/2)
        cv2.rectangle(frame, (x1, y1), (x1+w, y1+h), (255, 255, 255), -1)

        # 添加噪声
        noise = np.random.randint(0, 20, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)

        if i == 0:
            # 初始化
            bbox = (x1, y1, w, h)
            tracker.init(frame, bbox)
            print(f"初始化: bbox={bbox}")
        else:
            # 更新
            result = tracker.update(frame)
            print(f"帧{i}: 位置={result.center}, 置信度={result.confidence:.2f}")

    print("\nMOSSE跟踪器测试完成!")
