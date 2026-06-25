"""
存储引擎

整合 MemTable、WAL 和 SSTable，提供统一的存储接口。
"""

import os
import json
import time
import struct
import threading
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from .memtable import MemTable
from .wal import WAL
from .compression import compress_block, decompress_block


@dataclass
class SSTableMeta:
    """SSTable 元数据"""
    file_path: str
    metric: str
    min_timestamp: int
    max_timestamp: int
    size: int
    created_at: int
    entry_count: int


class SSTable:
    """
    Sorted String Table

    文件格式:
    ┌─────────────────────────────────────────────────────────┐
    │ Data Blocks                                             │
    │ ├── Block 1 (compressed timestamps + values)           │
    │ ├── Block 2                                            │
    │ └── ...                                                │
    ├─────────────────────────────────────────────────────────┤
    │ Index Block                                             │
    │ ├── Entry 1: min_ts, max_ts, offset, size              │
    │ └── ...                                                │
    ├─────────────────────────────────────────────────────────┤
    │ Footer (32 bytes)                                       │
    │ ├── Index Offset (8 bytes)                             │
    │ ├── Index Size (8 bytes)                               │
    │ ├── Entry Count (8 bytes)                              │
    │ └── Magic Number (8 bytes)                             │
    └─────────────────────────────────────────────────────────┘
    """

    MAGIC = 0x53535442  # 'SSTB'
    BLOCK_SIZE = 4096  # 每个块的目标大小

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.index = []  # [(min_ts, max_ts, offset, size)]
        self.entry_count = 0

    @classmethod
    def create(cls, file_path: str, data: List[Tuple[int, float]]) -> 'SSTable':
        """
        创建 SSTable 文件

        Args:
            file_path: 文件路径
            data: (timestamp, value) 列表，已按时间戳排序

        Returns:
            SSTable: 创建的 SSTable 实例
        """
        sst = cls(file_path)
        sst._write(data)
        return sst

    def _write(self, data: List[Tuple[int, float]]) -> None:
        """写入数据"""
        if not data:
            return

        self.entry_count = len(data)

        with open(self.file_path, 'wb') as f:
            # 写入数据块
            index = []
            pos = 0

            # 按块大小分组
            block_start = 0
            while block_start < len(data):
                # 计算块大小
                block_end = min(block_start + self.BLOCK_SIZE, len(data))
                block_data = data[block_start:block_end]

                # 提取时间戳和值
                timestamps = [d[0] for d in block_data]
                values = [d[1] for d in block_data]

                # 压缩块
                compressed = compress_block(timestamps, values)

                # 写入块
                f.write(compressed)

                # 更新索引
                index.append({
                    'min_ts': timestamps[0],
                    'max_ts': timestamps[-1],
                    'offset': pos,
                    'size': len(compressed)
                })

                pos += len(compressed)
                block_start = block_end

            # 写入索引
            index_offset = pos
            index_data = json.dumps(index).encode('utf-8')
            f.write(index_data)
            index_size = len(index_data)

            # 写入 Footer
            footer = struct.pack('Q', index_offset) + \
                     struct.pack('Q', index_size) + \
                     struct.pack('Q', self.entry_count) + \
                     struct.pack('Q', self.MAGIC)
            f.write(footer)

            self.index = index

    def read(self, start: int, end: int) -> List[Tuple[int, float]]:
        """
        读取时间范围内的数据

        Args:
            start: 开始时间戳
            end: 结束时间戳

        Returns:
            List[Tuple[int, float]]: (timestamp, value) 列表
        """
        if not self.index:
            self._load_index()

        results = []

        with open(self.file_path, 'rb') as f:
            for idx_entry in self.index:
                # 检查块是否与查询范围重叠
                if idx_entry['max_ts'] < start or idx_entry['min_ts'] > end:
                    continue

                # 读取块
                f.seek(idx_entry['offset'])
                block_data = f.read(idx_entry['size'])

                # 解压块
                timestamps, values = decompress_block(block_data)

                # 过滤范围
                for ts, val in zip(timestamps, values):
                    if start <= ts <= end:
                        results.append((ts, val))

        return results

    def _load_index(self) -> None:
        """加载索引"""
        file_size = os.path.getsize(self.file_path)

        # 读取 Footer
        with open(self.file_path, 'rb') as f:
            f.seek(file_size - 32)
            footer = f.read(32)

            index_offset = struct.unpack('Q', footer[:8])[0]
            index_size = struct.unpack('Q', footer[8:16])[0]
            self.entry_count = struct.unpack('Q', footer[16:24])[0]
            magic = struct.unpack('Q', footer[24:32])[0]

            if magic != self.MAGIC:
                raise ValueError("Invalid SSTable file")

            # 读取索引
            f.seek(index_offset)
            index_data = f.read(index_size)
            self.index = json.loads(index_data.decode('utf-8'))

    def get_meta(self) -> SSTableMeta:
        """获取元数据"""
        if not self.index:
            self._load_index()

        return SSTableMeta(
            file_path=str(self.file_path),
            metric='',  # 需要从外部设置
            min_timestamp=self.index[0]['min_ts'] if self.index else 0,
            max_timestamp=self.index[-1]['max_ts'] if self.index else 0,
            size=os.path.getsize(self.file_path),
            created_at=int(self.file_path.stem),
            entry_count=self.entry_count
        )


class StorageEngine:
    """
    存储引擎

    整合 MemTable、WAL 和 SSTable，提供:
    - 写入：先写 WAL，再写 MemTable
    - 查询：合并 MemTable 和 SSTable 的结果
    - 刷盘：MemTable 满后写入 SSTable
    - 恢复：从 WAL 恢复数据
    """

    def __init__(self, data_dir: str, config: Optional[Dict] = None):
        """
        初始化存储引擎

        Args:
            data_dir: 数据目录
            config: 配置字典
        """
        self.data_dir = Path(data_dir)
        self.config = config or {}

        # 创建目录
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / 'wal').mkdir(exist_ok=True)
        (self.data_dir / 'sst').mkdir(exist_ok=True)
        (self.data_dir / 'meta').mkdir(exist_ok=True)

        # 初始化组件
        memtable_max_size = self.config.get('memtable_max_size', 64 * 1024 * 1024)
        self.memtable = MemTable(max_size=memtable_max_size)
        self.immutable_memtable = None

        wal_max_size = self.config.get('wal_max_file_size', 64 * 1024 * 1024)
        self.wal = WAL(str(self.data_dir / 'wal'), max_file_size=wal_max_size)

        # SSTable 列表
        self.sstables: Dict[str, List[SSTableMeta]] = {}  # {metric: [SSTableMeta]}
        self._load_sstable_meta()

        # 锁
        self.write_lock = threading.Lock()
        self.read_lock = threading.RLock()
        self.flush_lock = threading.Lock()

        # 刷盘线程
        self.flush_thread = None
        self.flush_interval = self.config.get('flush_interval', 60)
        self._start_flush_thread()

    def write(self, metric: str, tags: Dict[str, str], timestamp: int, value: float) -> bool:
        """
        写入单个数据点

        Args:
            metric: 指标名称
            tags: 标签字典
            timestamp: 时间戳
            value: 数据值

        Returns:
            bool: 是否写入成功
        """
        with self.write_lock:
            # 写入 WAL
            self.wal.write(metric, tags, timestamp, value)

            # 写入 MemTable
            self.memtable.put(metric, tags, timestamp, value)

            # 检查是否需要刷盘
            if self.memtable.is_full():
                self._flush_memtable()

            return True

    def write_batch(self, points: List[Dict[str, Any]]) -> int:
        """
        批量写入数据点

        Args:
            points: 数据点列表

        Returns:
            int: 成功写入的点数
        """
        with self.write_lock:
            # 写入 WAL
            self.wal.write_batch(points)

            # 写入 MemTable
            count = self.memtable.put_batch(points)

            # 检查是否需要刷盘
            if self.memtable.is_full():
                self._flush_memtable()

            return count

    def query(
        self,
        metric: str,
        start: int,
        end: int,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Tuple[int, float]]:
        """
        查询数据

        Args:
            metric: 指标名称
            start: 开始时间戳
            end: 结束时间戳
            tags: 标签过滤（可选）

        Returns:
            List[Tuple[int, float]]: (timestamp, value) 列表
        """
        with self.read_lock:
            results = []

            # 查询 MemTable
            memtable_results = self.memtable.range_query(metric, start, end, tags)
            results.extend(memtable_results)

            # 查询 Immutable MemTable
            if self.immutable_memtable:
                immutable_results = self.immutable_memtable.range_query(metric, start, end, tags)
                results.extend(immutable_results)

            # 查询 SSTable
            sstable_results = self._query_sstables(metric, start, end)
            results.extend(sstable_results)

            # 去重和排序
            results = self._deduplicate_and_sort(results)

            return results

    def latest(self, metric: str, tags: Optional[Dict[str, str]] = None) -> Optional[Tuple[int, float]]:
        """
        获取最新数据点

        Args:
            metric: 指标名称
            tags: 标签过滤（可选）

        Returns:
            Optional[Tuple[int, float]]: (timestamp, value)
        """
        with self.read_lock:
            # 查询 MemTable
            result = self.memtable.latest(metric, tags)
            if result:
                return result

            # 查询 SSTable（最新的在前）
            if metric in self.sstables:
                for meta in reversed(self.sstables[metric]):
                    sst = SSTable(meta.file_path)
                    results = sst.read(meta.min_timestamp, meta.max_timestamp)
                    if results:
                        return results[-1]

            return None

    def delete_before(self, metric: str, before_timestamp: int) -> int:
        """
        删除指定时间之前的数据

        Args:
            metric: 指标名称
            before_timestamp: 时间戳阈值

        Returns:
            int: 删除的数据点数量
        """
        count = 0

        # 从 MemTable 删除
        count += self.memtable.delete_before(metric, before_timestamp)

        # 删除 SSTable
        if metric in self.sstables:
            sstables_to_keep = []
            for meta in self.sstables[metric]:
                if meta.max_timestamp < before_timestamp:
                    # 整个 SSTable 都在阈值之前，删除
                    os.remove(meta.file_path)
                    count += meta.entry_count
                else:
                    sstables_to_keep.append(meta)
            self.sstables[metric] = sstables_to_keep

        return count

    def flush(self) -> None:
        """手动触发刷盘"""
        with self.flush_lock:
            self._flush_memtable()

    def close(self) -> None:
        """关闭存储引擎"""
        # 停止刷盘线程
        self.flush_interval = 0
        if self.flush_thread:
            self.flush_thread.join(timeout=5)

        # 刷盘
        self.flush()

        # 关闭 WAL
        self.wal.close()

    def recover(self) -> None:
        """从 WAL 恢复数据"""
        entries = self.wal.recover()
        for entry in entries:
            self.memtable.put(entry.metric, entry.tags, entry.timestamp, entry.value)

    def get_stats(self) -> Dict[str, Any]:
        """获取存储引擎统计信息"""
        return {
            'memtable_size': self.memtable.get_size(),
            'memtable_count': self.memtable.get_count(),
            'immutable_memtable_size': self.immutable_memtable.get_size() if self.immutable_memtable else 0,
            'sstable_count': sum(len(v) for v in self.sstables.values()),
            'wal_stats': self.wal.get_stats(),
        }

    def _flush_memtable(self) -> None:
        """将 MemTable 刷盘为 SSTable"""
        if self.memtable.get_count() == 0:
            return

        # 将当前 MemTable 设为不可变
        self.immutable_memtable = self.memtable
        self.memtable = MemTable(max_size=self.config.get('memtable_max_size', 64 * 1024 * 1024))

        # 获取不可变 MemTable 的数据
        data = self.immutable_memtable.get_all()

        # 按 metric 分组
        metric_data = {}
        for metric, tags, timestamp, value in data:
            if metric not in metric_data:
                metric_data[metric] = []
            metric_data[metric].append((tags, timestamp, value))

        # 为每个 metric 创建 SSTable
        for metric, points in metric_data.items():
            # 按时间戳排序
            points.sort(key=lambda x: x[1])

            # 创建 SSTable
            timestamp = int(time.time() * 1000)
            sst_dir = self.data_dir / 'sst' / metric
            sst_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(sst_dir / f"{timestamp}.sst")

            # 提取 (timestamp, value) 对
            sst_data = [(p[1], p[2]) for p in points]

            SSTable.create(file_path, sst_data)

            # 更新元数据
            meta = SSTableMeta(
                file_path=file_path,
                metric=metric,
                min_timestamp=points[0][1],
                max_timestamp=points[-1][1],
                size=os.path.getsize(file_path),
                created_at=timestamp,
                entry_count=len(points)
            )

            if metric not in self.sstables:
                self.sstables[metric] = []
            self.sstables[metric].append(meta)

            # 保存元数据
            self._save_sstable_meta()

        # 清空不可变 MemTable
        self.immutable_memtable = None

    def _query_sstables(self, metric: str, start: int, end: int) -> List[Tuple[int, float]]:
        """查询 SSTable"""
        results = []

        if metric not in self.sstables:
            return results

        for meta in self.sstables[metric]:
            # 检查 SSTable 是否与查询范围重叠
            if meta.max_timestamp < start or meta.min_timestamp > end:
                continue

            sst = SSTable(meta.file_path)
            block_results = sst.read(start, end)
            results.extend(block_results)

        return results

    def _deduplicate_and_sort(self, results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """去重和排序"""
        # 使用字典去重（保留最新的值）
        seen = {}
        for ts, val in results:
            seen[ts] = val

        # 按时间戳排序
        sorted_results = sorted(seen.items(), key=lambda x: x[0])
        return sorted_results

    def _load_sstable_meta(self) -> None:
        """加载 SSTable 元数据"""
        meta_file = self.data_dir / 'meta' / 'sstables.json'
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                data = json.load(f)
                for metric, metas in data.items():
                    self.sstables[metric] = [SSTableMeta(**m) for m in metas]

    def _save_sstable_meta(self) -> None:
        """保存 SSTable 元数据"""
        meta_file = self.data_dir / 'meta' / 'sstables.json'
        data = {}
        for metric, metas in self.sstables.items():
            data[metric] = [asdict(m) for m in metas]

        with open(meta_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _start_flush_thread(self) -> None:
        """启动刷盘线程"""
        def flush_worker():
            while self.flush_interval > 0:
                time.sleep(self.flush_interval)
                if self.memtable.get_count() > 0:
                    self.flush()

        self.flush_thread = threading.Thread(target=flush_worker, daemon=True)
        self.flush_thread.start()
