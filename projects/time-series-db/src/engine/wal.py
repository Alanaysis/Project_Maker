"""
Write-Ahead Log (WAL)

在数据写入内存表之前先写入 WAL，保证数据持久性。
支持 WAL 文件轮转和恢复。
"""

import os
import struct
import time
import zlib
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path


class WALEntry:
    """WAL 条目"""

    def __init__(self, metric: str, tags: Dict[str, str], timestamp: int, value: float):
        self.metric = metric
        self.tags = tags
        self.timestamp = timestamp
        self.value = value

    def encode(self) -> bytes:
        """编码为字节序列"""
        # 编码 metric
        metric_bytes = self.metric.encode('utf-8')
        metric_len = len(metric_bytes)

        # 编码 tags
        tags_parts = []
        for k, v in self.tags.items():
            k_bytes = k.encode('utf-8')
            v_bytes = v.encode('utf-8')
            tags_parts.append(struct.pack('I', len(k_bytes)) + k_bytes +
                             struct.pack('I', len(v_bytes)) + v_bytes)
        tags_bytes = b''.join(tags_parts)
        tags_len = len(tags_bytes)

        # 编码 timestamp 和 value
        timestamp_bytes = struct.pack('q', self.timestamp)  # int64
        value_bytes = struct.pack('d', self.value)  # double

        # 组装
        data = (
            struct.pack('I', metric_len) + metric_bytes +
            struct.pack('I', tags_len) + tags_bytes +
            timestamp_bytes +
            value_bytes
        )

        return data

    @classmethod
    def decode(cls, data: bytes, offset: int = 0) -> Tuple['WALEntry', int]:
        """从字节序列解码"""
        pos = offset

        # 解码 metric
        metric_len = struct.unpack('I', data[pos:pos+4])[0]
        pos += 4
        metric = data[pos:pos+metric_len].decode('utf-8')
        pos += metric_len

        # 解码 tags
        tags_len = struct.unpack('I', data[pos:pos+4])[0]
        pos += 4
        tags = {}
        tags_end = pos + tags_len
        while pos < tags_end:
            k_len = struct.unpack('I', data[pos:pos+4])[0]
            pos += 4
            k = data[pos:pos+k_len].decode('utf-8')
            pos += k_len
            v_len = struct.unpack('I', data[pos:pos+4])[0]
            pos += 4
            v = data[pos:pos+v_len].decode('utf-8')
            pos += v_len
            tags[k] = v

        # 解码 timestamp 和 value
        timestamp = struct.unpack('q', data[pos:pos+8])[0]
        pos += 8
        value = struct.unpack('d', data[pos:pos+8])[0]
        pos += 8

        return cls(metric, tags, timestamp, value), pos


class WAL:
    """
    Write-Ahead Log 实现

    文件格式:
    ┌─────────────────────────────────────────────┐
    │ Header (16 bytes)                           │
    │ ├── Magic Number (4 bytes): 0x57414C00     │
    │ ├── Version (4 bytes): 1                   │
    │ └── Created At (8 bytes): timestamp        │
    ├─────────────────────────────────────────────┤
    │ Entry 1                                     │
    │ ├── Length (4 bytes)                        │
    │ ├── CRC32 (4 bytes)                         │
    │ └── Data (variable)                         │
    ├─────────────────────────────────────────────┤
    │ Entry 2                                     │
    │ ...                                         │
    └─────────────────────────────────────────────┘
    """

    MAGIC = 0x57414C00
    VERSION = 1
    HEADER_SIZE = 16
    ENTRY_HEADER_SIZE = 8  # Length(4) + CRC32(4)

    def __init__(self, wal_dir: str, max_file_size: int = 64 * 1024 * 1024):
        """
        初始化 WAL

        Args:
            wal_dir: WAL 文件目录
            max_file_size: 单个 WAL 文件最大大小，默认 64MB
        """
        self.wal_dir = Path(wal_dir)
        self.max_file_size = max_file_size
        self.current_file = None
        self.current_file_path = None
        self.current_size = 0
        self.lock = None  # 不使用锁，由上层控制并发

        # 确保目录存在
        self.wal_dir.mkdir(parents=True, exist_ok=True)

        # 打开或创建 WAL 文件
        self._open_latest_file()

    def write(self, metric: str, tags: Dict[str, str], timestamp: int, value: float) -> bool:
        """
        写入一条记录

        Args:
            metric: 指标名称
            tags: 标签字典
            timestamp: 时间戳
            value: 数据值

        Returns:
            bool: 是否写入成功
        """
        entry = WALEntry(metric, tags, timestamp, value)
        data = entry.encode()

        # 计算 CRC32
        crc = zlib.crc32(data) & 0xFFFFFFFF

        # 构建条目
        entry_data = struct.pack('I', len(data)) + struct.pack('I', crc) + data
        entry_size = len(entry_data)

        # 检查是否需要轮转文件
        if self.current_size + entry_size > self.max_file_size:
            self._rotate_file()

        # 写入
        self.current_file.write(entry_data)
        self.current_file.flush()
        self.current_size += entry_size

        return True

    def write_batch(self, points: List[Dict[str, Any]]) -> int:
        """
        批量写入记录

        Args:
            points: 数据点列表

        Returns:
            int: 成功写入的点数
        """
        count = 0
        for point in points:
            if self.write(
                point['metric'],
                point['tags'],
                point['timestamp'],
                point['value']
            ):
                count += 1
        return count

    def sync(self) -> None:
        """同步到磁盘"""
        if self.current_file:
            self.current_file.flush()
            os.fsync(self.current_file.fileno())

    def close(self) -> None:
        """关闭当前 WAL 文件"""
        if self.current_file:
            self.sync()
            self.current_file.close()
            self.current_file = None

    def recover(self) -> List[WALEntry]:
        """
        从 WAL 文件恢复数据

        Returns:
            List[WALEntry]: 恢复的条目列表
        """
        entries = []
        wal_files = self._list_wal_files()

        for wal_file in wal_files:
            file_entries = self._recover_file(wal_file)
            entries.extend(file_entries)

        return entries

    def cleanup(self, keep_files: int = 3) -> int:
        """
        清理旧的 WAL 文件

        Args:
            keep_files: 保留的文件数量

        Returns:
            int: 删除的文件数量
        """
        wal_files = self._list_wal_files()
        if len(wal_files) <= keep_files:
            return 0

        files_to_delete = wal_files[:-keep_files]
        count = 0
        for f in files_to_delete:
            if f != self.current_file_path:
                os.remove(f)
                count += 1

        return count

    def _open_latest_file(self) -> None:
        """打开最新的 WAL 文件或创建新文件"""
        wal_files = self._list_wal_files()

        if wal_files:
            # 打开最新的文件
            self.current_file_path = wal_files[-1]
            self.current_file = open(self.current_file_path, 'ab')
            self.current_size = os.path.getsize(self.current_file_path)
        else:
            # 创建新文件
            self._create_new_file()

    def _create_new_file(self) -> None:
        """创建新的 WAL 文件"""
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}.wal"
        self.current_file_path = self.wal_dir / filename

        self.current_file = open(self.current_file_path, 'wb')

        # 写入 header
        header = struct.pack('I', self.MAGIC) + \
                 struct.pack('I', self.VERSION) + \
                 struct.pack('q', int(time.time()))
        self.current_file.write(header)
        self.current_file.flush()

        self.current_size = self.HEADER_SIZE

    def _rotate_file(self) -> None:
        """轮转到新文件"""
        self.close()
        self._create_new_file()

    def _list_wal_files(self) -> List[Path]:
        """列出所有 WAL 文件，按时间排序"""
        wal_files = sorted(self.wal_dir.glob('*.wal'))
        return wal_files

    def _recover_file(self, file_path: Path) -> List[WALEntry]:
        """从单个 WAL 文件恢复"""
        entries = []

        with open(file_path, 'rb') as f:
            data = f.read()

        if len(data) < self.HEADER_SIZE:
            return entries

        # 验证 header
        magic = struct.unpack('I', data[:4])[0]
        if magic != self.MAGIC:
            return entries

        # 跳过 header
        pos = self.HEADER_SIZE

        while pos < len(data):
            if pos + self.ENTRY_HEADER_SIZE > len(data):
                break

            # 读取条目头
            entry_len = struct.unpack('I', data[pos:pos+4])[0]
            expected_crc = struct.unpack('I', data[pos+4:pos+8])[0]
            pos += self.ENTRY_HEADER_SIZE

            if pos + entry_len > len(data):
                break

            # 读取条目数据
            entry_data = data[pos:pos+entry_len]
            pos += entry_len

            # 验证 CRC32
            actual_crc = zlib.crc32(entry_data) & 0xFFFFFFFF
            if actual_crc != expected_crc:
                # CRC 不匹配，跳过此条目
                continue

            # 解码条目
            try:
                entry, _ = WALEntry.decode(entry_data)
                entries.append(entry)
            except Exception:
                # 解码失败，跳过
                continue

        return entries

    def get_stats(self) -> Dict[str, Any]:
        """获取 WAL 统计信息"""
        wal_files = self._list_wal_files()
        total_size = sum(os.path.getsize(f) for f in wal_files)

        return {
            'file_count': len(wal_files),
            'total_size': total_size,
            'current_file': str(self.current_file_path) if self.current_file_path else None,
            'current_size': self.current_size,
        }
