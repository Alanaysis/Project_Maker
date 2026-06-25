"""
数据集测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dataset import SimpleDetectionDataset, create_simple_dataset, collate_fn


class TestDataset:
    """数据集测试类"""

    def test_simple_dataset_creation(self):
        """测试简单数据集创建"""
        dataset = SimpleDetectionDataset(num_samples=100, image_size=320, num_classes=5)
        assert len(dataset) == 100

    def test_dataset_getitem(self):
        """测试数据集获取元素"""
        dataset = SimpleDetectionDataset(num_samples=10, image_size=320, num_classes=5)

        item = dataset[0]
        assert 'image' in item
        assert 'boxes' in item
        assert 'labels' in item

        assert item['image'].shape == (3, 320, 320)
        assert item['boxes'].ndim == 2
        assert item['boxes'].shape[1] == 4
        assert item['labels'].ndim == 1

    def test_dataset_boxes_format(self):
        """测试边界框格式"""
        dataset = SimpleDetectionDataset(num_samples=10, image_size=320, num_classes=5)

        item = dataset[0]
        boxes = item['boxes']

        # 边界框应该在[0, 1]范围内
        assert (boxes >= 0).all()
        assert (boxes <= 1).all()

    def test_create_simple_dataset(self):
        """测试创建简单数据集函数"""
        dataset = create_simple_dataset(num_samples=50, image_size=640, num_classes=10)
        assert len(dataset) == 50
        assert dataset.image_size == 640
        assert dataset.num_classes == 10

    def test_collate_fn(self):
        """测试批处理函数"""
        dataset = SimpleDetectionDataset(num_samples=4, image_size=320, num_classes=5)
        batch = [dataset[0], dataset[1], dataset[2], dataset[3]]

        images, targets = collate_fn(batch)

        assert images.shape == (4, 3, 320, 320)
        assert len(targets) == 4
        for target in targets:
            assert 'boxes' in target
            assert 'labels' in target

    def test_dataset_consistency(self):
        """测试数据集一致性"""
        dataset = SimpleDetectionDataset(num_samples=100, image_size=320, num_classes=5)

        # 多次访问同一索引应该返回相同结果
        item1 = dataset[0]
        item2 = dataset[0]
        assert torch.equal(item1['image'], item2['image'])
        assert torch.equal(item1['boxes'], item2['boxes'])
        assert torch.equal(item1['labels'], item2['labels'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
