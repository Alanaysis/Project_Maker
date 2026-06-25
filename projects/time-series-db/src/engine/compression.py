"""
数据压缩模块

实现时间戳和值的压缩算法:
- 时间戳: Delta 编码
- 值: 简单的差值编码
"""

import struct
from typing import List, Tuple


def compress_timestamps(timestamps: List[int]) -> bytes:
    """
    压缩时间戳序列

    使用 Delta 编码 + 变长编码

    Args:
        timestamps: 时间戳列表（已排序）

    Returns:
        bytes: 压缩后的数据
    """
    if not timestamps:
        return b''

    # Delta 编码
    deltas = [timestamps[0]]
    for i in range(1, len(timestamps)):
        deltas.append(timestamps[i] - timestamps[i-1])

    # 使用固定长度编码 (每个 delta 8 字节)
    result = bytearray()
    result.extend(struct.pack('I', len(timestamps)))  # 数量

    for delta in deltas:
        result.extend(struct.pack('q', delta))  # int64

    return bytes(result)


def decompress_timestamps(data: bytes) -> List[int]:
    """
    解压时间戳序列

    Args:
        data: 压缩的数据

    Returns:
        List[int]: 时间戳列表
    """
    if not data:
        return []

    pos = 0
    count = struct.unpack('I', data[pos:pos+4])[0]
    pos += 4

    deltas = []
    for _ in range(count):
        delta = struct.unpack('q', data[pos:pos+8])[0]
        pos += 8
        deltas.append(delta)

    # 还原时间戳
    timestamps = [deltas[0]]
    for i in range(1, len(deltas)):
        timestamps.append(timestamps[-1] + deltas[i])

    return timestamps


def compress_values(values: List[float]) -> bytes:
    """
    压缩浮点数值序列

    使用简单存储（每个值 8 字节）

    Args:
        values: 浮点数值列表

    Returns:
        bytes: 压缩后的数据
    """
    if not values:
        return b''

    result = bytearray()
    result.extend(struct.pack('I', len(values)))  # 数量

    # 存储所有值（简单实现）
    for val in values:
        result.extend(struct.pack('d', val))

    return bytes(result)


def decompress_values(data: bytes) -> List[float]:
    """
    解压浮点数值序列

    Args:
        data: 压缩的数据

    Returns:
        List[float]: 浮点数值列表
    """
    if not data:
        return []

    pos = 0
    count = struct.unpack('I', data[pos:pos+4])[0]
    pos += 4

    if count == 0:
        return []

    values = []
    for _ in range(count):
        val = struct.unpack('d', data[pos:pos+8])[0]
        pos += 8
        values.append(val)

    return values


def compress_block(timestamps: List[int], values: List[float]) -> bytes:
    """
    压缩一个数据块

    Args:
        timestamps: 时间戳列表
        values: 值列表

    Returns:
        bytes: 压缩后的数据块
    """
    ts_data = compress_timestamps(timestamps)
    val_data = compress_values(values)

    # 组装: ts_len(4) + ts_data + val_data
    result = struct.pack('I', len(ts_data)) + ts_data + val_data
    return result


def decompress_block(data: bytes) -> Tuple[List[int], List[float]]:
    """
    解压数据块

    Args:
        data: 压缩的数据块

    Returns:
        Tuple[List[int], List[float]]: (时间戳列表, 值列表)
    """
    ts_len = struct.unpack('I', data[:4])[0]
    ts_data = data[4:4+ts_len]
    val_data = data[4+ts_len:]

    timestamps = decompress_timestamps(ts_data)
    values = decompress_values(val_data)

    return timestamps, values
