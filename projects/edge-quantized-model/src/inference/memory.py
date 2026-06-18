"""
内存管理模块

提供内存池管理功能，优化内存分配和释放
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryBlock:
    """
    内存块

    Attributes:
        offset: 偏移量
        size: 大小
        is_free: 是否空闲
        name: 分配的名称
    """
    offset: int
    size: int
    is_free: bool = True
    name: Optional[str] = None


class MemoryPool:
    """
    内存池

    提供高效的内存管理，支持：
    - 内存预分配
    - 内存复用
    - 碎片整理
    - 内存统计
    """

    def __init__(self, size: int, dtype: np.dtype = np.float32):
        """
        初始化内存池

        Args:
            size: 内存池大小（元素数量）
            dtype: 数据类型
        """
        self.size = size
        self.dtype = dtype
        self.buffer = np.zeros(size, dtype=dtype)
        self.blocks: List[MemoryBlock] = [MemoryBlock(offset=0, size=size)]
        self.allocated: Dict[str, MemoryBlock] = {}

        logger.info(f"初始化内存池: size={size}, dtype={dtype}")

    def allocate(self, name: str, size: int) -> np.ndarray:
        """
        分配内存

        Args:
            name: 分配名称
            size: 需要的元素数量

        Returns:
            分配的内存数组

        Raises:
            MemoryError: 如果内存不足
        """
        # 查找合适的空闲块
        block = self._find_free_block(size)

        if block is None:
            raise MemoryError(f"内存不足: 需要 {size} 元素，可用 {self._available_size()} 元素")

        # 分割块（如果需要）
        if block.size > size:
            new_block = MemoryBlock(
                offset=block.offset + size,
                size=block.size - size,
                is_free=True,
            )
            self.blocks.insert(self.blocks.index(block) + 1, new_block)
            block.size = size

        # 标记为已分配
        block.is_free = False
        block.name = name
        self.allocated[name] = block

        logger.debug(f"分配内存: name={name}, size={size}, offset={block.offset}")

        # 返回数组视图
        return self.buffer[block.offset:block.offset + size]

    def free(self, name: str):
        """
        释放内存

        Args:
            name: 分配名称
        """
        if name not in self.allocated:
            logger.warning(f"尝试释放未分配的内存: {name}")
            return

        block = self.allocated.pop(name)
        block.is_free = True
        block.name = None

        logger.debug(f"释放内存: name={name}, offset={block.offset}, size={block.size}")

        # 合并相邻空闲块
        self._merge_free_blocks()

    def _find_free_block(self, size: int) -> Optional[MemoryBlock]:
        """
        查找合适的空闲块

        使用首次适应算法

        Args:
            size: 需要的大小

        Returns:
            合适的空闲块，如果不存在返回 None
        """
        for block in self.blocks:
            if block.is_free and block.size >= size:
                return block
        return None

    def _merge_free_blocks(self):
        """合并相邻的空闲块"""
        merged = True
        while merged:
            merged = False
            i = 0
            while i < len(self.blocks) - 1:
                current = self.blocks[i]
                next_block = self.blocks[i + 1]

                if current.is_free and next_block.is_free:
                    # 合并块
                    current.size += next_block.size
                    self.blocks.pop(i + 1)
                    merged = True
                else:
                    i += 1

    def _available_size(self) -> int:
        """获取可用内存大小"""
        return sum(block.size for block in self.blocks if block.is_free)

    def get_usage(self) -> Dict[str, int]:
        """
        获取内存使用情况

        Returns:
            使用情况字典
        """
        allocated_size = sum(block.size for block in self.blocks if not block.is_free)
        free_size = sum(block.size for block in self.blocks if block.is_free)

        return {
            "total": self.size,
            "allocated": allocated_size,
            "free": free_size,
            "fragmentation": len([b for b in self.blocks if b.is_free]),
        }

    def reset(self):
        """重置内存池"""
        self.blocks = [MemoryBlock(offset=0, size=self.size)]
        self.allocated.clear()
        self.buffer[:] = 0
        logger.info("内存池已重置")

    def resize(self, new_size: int):
        """
        调整内存池大小

        Args:
            new_size: 新的大小
        """
        if self.allocated:
            raise RuntimeError("无法调整有分配的内存池大小")

        self.size = new_size
        self.buffer = np.zeros(new_size, dtype=self.dtype)
        self.blocks = [MemoryBlock(offset=0, size=new_size)]
        logger.info(f"内存池大小调整为: {new_size}")


class TensorAllocator:
    """
    张量分配器

    管理张量的内存分配，支持生命周期管理
    """

    def __init__(self, memory_pool: MemoryPool):
        """
        初始化张量分配器

        Args:
            memory_pool: 内存池
        """
        self.memory_pool = memory_pool
        self.tensor_refs: Dict[str, int] = {}  # name -> ref_count

    def allocate_tensor(
        self,
        name: str,
        shape: Tuple[int, ...],
        dtype: np.dtype = np.float32,
    ) -> np.ndarray:
        """
        分配张量

        Args:
            name: 张量名称
            shape: 形状
            dtype: 数据类型

        Returns:
            分配的张量
        """
        size = int(np.prod(shape))

        # 分配内存
        data = self.memory_pool.allocate(name, size)

        # 重塑为指定形状
        tensor = data.reshape(shape)

        # 增加引用计数
        self.tensor_refs[name] = self.tensor_refs.get(name, 0) + 1

        return tensor

    def release_tensor(self, name: str):
        """
        释放张量

        Args:
            name: 张量名称
        """
        if name not in self.tensor_refs:
            return

        self.tensor_refs[name] -= 1

        if self.tensor_refs[name] <= 0:
            self.memory_pool.free(name)
            del self.tensor_refs[name]

    def get_tensor(self, name: str) -> Optional[np.ndarray]:
        """
        获取已分配的张量

        Args:
            name: 张量名称

        Returns:
            张量数据，如果不存在返回 None
        """
        if name in self.memory_pool.allocated:
            block = self.memory_pool.allocated[name]
            return self.memory_pool.buffer[block.offset:block.offset + block.size]
        return None

    def reset(self):
        """重置分配器"""
        self.tensor_refs.clear()
        self.memory_pool.reset()
