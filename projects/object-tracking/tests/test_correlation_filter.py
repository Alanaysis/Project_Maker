"""
相关滤波跟踪器测试

测试内容:
- MOSSE跟踪器初始化和更新
- KCF跟踪器初始化和更新
- 跟踪结果验证
- 合成序列跟踪
"""

import pytest
import numpy as np
import cv2
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.correlation_filter import MOSSETracker, KCFTracker, TrackingResult


def create_test_frame(
    width: int = 300,
    height: int = 300,
    target_pos: tuple = (150, 150),
    target_size: tuple = (40, 40),
    noise_level: int = 10
) -> tuple:
    """创建测试帧

    Args:
        width: 帧宽度
        height: 帧高度
        target_pos: 目标中心位置
        target_size: 目标大小
        noise_level: 噪声级别

    Returns:
        (frame, bbox) 帧和边界框
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # 绘制目标
    w, h = target_size
    x = int(target_pos[0] - w / 2)
    y = int(target_pos[1] - h / 2)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), -1)

    # 添加噪声
    noise = np.random.randint(0, noise_level, frame.shape, dtype=np.uint8)
    frame = cv2.add(frame, noise)

    bbox = (x, y, w, h)
    return frame, bbox


class TestMOSSETracker:
    """MOSSE跟踪器测试类"""

    def test_initialization(self):
        """测试初始化"""
        tracker = MOSSETracker(learning_rate=0.2)
        assert tracker is not None
        assert tracker.learning_rate == 0.2
        assert not tracker.initialized

    def test_init_with_frame(self):
        """测试用帧初始化"""
        tracker = MOSSETracker()
        frame, bbox = create_test_frame()

        success = tracker.init(frame, bbox)
        assert success
        assert tracker.initialized
        assert tracker.bbox == bbox

    def test_update_after_init(self):
        """测试初始化后的更新"""
        tracker = MOSSETracker()
        frame, bbox = create_test_frame()

        tracker.init(frame, bbox)

        # 创建新帧，目标稍微移动
        new_frame, _ = create_test_frame(target_pos=(155, 155))

        result = tracker.update(new_frame)
        assert isinstance(result, TrackingResult)
        assert result.bbox is not None
        assert result.confidence >= 0

    def test_tracking_consistency(self):
        """测试跟踪一致性"""
        tracker = MOSSETracker(learning_rate=0.3)

        # 初始化
        init_pos = (150, 150)
        frame, bbox = create_test_frame(target_pos=init_pos)
        tracker.init(frame, bbox)

        # 跟踪几帧
        positions = []
        for i in range(10):
            new_pos = (init_pos[0] + 2*i, init_pos[1] + 2*i)
            frame, _ = create_test_frame(target_pos=new_pos)
            result = tracker.update(frame)
            positions.append(result.center)

        # 位置应该变化
        assert positions[-1][0] > positions[0][0]
        assert positions[-1][1] > positions[0][1]

    def test_update_without_init(self):
        """测试未初始化时更新"""
        tracker = MOSSETracker()
        frame, _ = create_test_frame()

        with pytest.raises(RuntimeError):
            tracker.update(frame)

    def test_psr_calculation(self):
        """测试PSR计算"""
        tracker = MOSSETracker()

        # 创建一个简单的响应图
        response = np.random.randn(10, 10)
        response[5, 5] = 10  # 设置峰值

        psr = tracker._compute_psr(response, (5, 5))
        assert psr > 0

    def test_preprocess(self):
        """测试预处理"""
        tracker = MOSSETracker()

        # 创建测试图像
        patch = np.random.randint(0, 255, (50, 50), dtype=np.uint8)

        processed = tracker._preprocess(patch)

        # 应该归一化
        assert abs(np.mean(processed)) < 0.1
        assert abs(np.std(processed) - 1.0) < 0.1

    def test_gaussian_response(self):
        """测试高斯响应创建"""
        tracker = MOSSETracker()

        response = tracker._create_gaussian_response((10, 10), (5, 5))

        # 峰值应该在中心
        assert response[5, 5] == np.max(response)
        # 应该是高斯分布
        assert response[0, 0] < response[5, 5]


class TestKCFTracker:
    """KCF跟踪器测试类"""

    def test_initialization(self):
        """测试初始化"""
        tracker = KCFTracker()
        assert tracker is not None
        assert not tracker.initialized

    def test_init_with_frame(self):
        """测试用帧初始化"""
        tracker = KCFTracker()
        frame, bbox = create_test_frame()

        success = tracker.init(frame, bbox)
        assert success
        assert tracker.initialized

    def test_update_after_init(self):
        """测试初始化后的更新"""
        tracker = KCFTracker()
        frame, bbox = create_test_frame()

        tracker.init(frame, bbox)

        # 创建新帧
        new_frame, _ = create_test_frame(target_pos=(155, 155))

        result = tracker.update(new_frame)
        assert isinstance(result, TrackingResult)
        assert result.bbox is not None

    def test_gaussian_kernel(self):
        """测试高斯核计算"""
        tracker = KCFTracker()

        # 使用相同的向量测试 (对角线应该是最大的)
        x1 = np.random.randn(10, 5)

        k = tracker._gaussian_kernel(x1, x1)
        assert k.shape == (10, 10)

        # 对角线应该最大 (因为d[i,i]=0时k=1)
        for i in range(10):
            assert k[i, i] >= k[i, 0] - 1e-10

    def test_hog_features(self):
        """测试HOG特征提取"""
        tracker = KCFTracker(cell_size=4)

        patch = np.random.randint(0, 255, (32, 32), dtype=np.uint8)
        features = tracker._extract_hog(patch)

        assert features is not None
        assert len(features) > 0


class TestTrackingResult:
    """跟踪结果测试类"""

    def test_creation(self):
        """测试创建"""
        result = TrackingResult(
            bbox=(10, 20, 30, 40),
            confidence=0.95,
            center=(25.0, 40.0)
        )

        assert result.bbox == (10, 20, 30, 40)
        assert result.confidence == 0.95
        assert result.center == (25.0, 40.0)


class TestSyntheticSequence:
    """合成序列跟踪测试"""

    def test_mosse_linear_motion(self):
        """测试MOSSE线性运动跟踪"""
        tracker = MOSSETracker(learning_rate=0.25)

        # 初始位置
        init_pos = (100, 100)
        frame, bbox = create_test_frame(
            width=400,
            height=400,
            target_pos=init_pos
        )
        tracker.init(frame, bbox)

        # 线性运动
        positions = []
        for i in range(20):
            new_pos = (init_pos[0] + 3*i, init_pos[1] + 2*i)
            frame, _ = create_test_frame(
                width=400,
                height=400,
                target_pos=new_pos
            )
            result = tracker.update(frame)
            positions.append(result.center)

        # 验证跟踪方向正确
        last_pos = positions[-1]
        assert last_pos[0] > init_pos[0], "X方向应该增加"
        assert last_pos[1] > init_pos[1], "Y方向应该增加"

    def test_kcf_stationary_target(self):
        """测试KCF静止目标跟踪"""
        tracker = KCFTracker()

        # 固定位置
        fixed_pos = (150, 150)
        frame, bbox = create_test_frame(target_pos=fixed_pos)
        tracker.init(frame, bbox)

        # 跟踪静止目标
        for i in range(10):
            frame, _ = create_test_frame(target_pos=fixed_pos, noise_level=20)
            result = tracker.update(frame)

            # 位置应该保持接近
            error = np.sqrt(
                (result.center[0] - fixed_pos[0])**2 +
                (result.center[1] - fixed_pos[1])**2
            )
            assert error < 30, f"静止目标误差 {error} 太大"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
