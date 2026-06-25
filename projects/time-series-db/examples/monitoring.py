"""
监控数据存储示例

演示如何使用时间序列数据库存储和查询系统监控数据。
"""

import time
import random
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import TimeSeriesDB


def generate_monitoring_data(db: TimeSeriesDB, duration: int = 3600):
    """
    生成模拟监控数据

    Args:
        db: 数据库实例
        duration: 数据持续时间（秒）
    """
    print(f"Generating {duration} seconds of monitoring data...")

    current_time = int(time.time()) - duration
    points = []

    for i in range(duration):
        timestamp = current_time + i

        # CPU 使用率 (正弦波 + 随机噪声)
        cpu_base = 50 + 20 * (i % 300) / 300
        cpu_value = cpu_base + random.uniform(-5, 5)
        cpu_value = max(0, min(100, cpu_value))

        points.append({
            'metric': 'cpu_usage',
            'tags': {'host': 'web-server-1', 'region': 'us-east'},
            'timestamp': timestamp,
            'value': cpu_value
        })

        # 内存使用
        memory_base = 4096 + 2048 * (i % 600) / 600
        memory_value = memory_base + random.uniform(-100, 100)

        points.append({
            'metric': 'memory_usage',
            'tags': {'host': 'web-server-1', 'region': 'us-east'},
            'timestamp': timestamp,
            'value': memory_value
        })

        # 磁盘 I/O
        disk_io = random.uniform(100, 1000) if i % 10 < 3 else random.uniform(10, 100)

        points.append({
            'metric': 'disk_io',
            'tags': {'host': 'web-server-1', 'region': 'us-east'},
            'timestamp': timestamp,
            'value': disk_io
        })

        # 网络流量
        network_in = random.uniform(1000, 10000)
        network_out = random.uniform(500, 5000)

        points.append({
            'metric': 'network_in',
            'tags': {'host': 'web-server-1', 'region': 'us-east'},
            'timestamp': timestamp,
            'value': network_in
        })

        points.append({
            'metric': 'network_out',
            'tags': {'host': 'web-server-1', 'region': 'us-east'},
            'timestamp': timestamp,
            'value': network_out
        })

        # 每 100 个点批量写入一次
        if len(points) >= 500:
            db.write_batch(points)
            points = []

    # 写入剩余数据
    if points:
        db.write_batch(points)

    print(f"Generated {duration * 5} data points")


def query_examples(db: TimeSeriesDB):
    """查询示例"""
    print("\n=== Query Examples ===")

    now = int(time.time())
    one_hour_ago = now - 3600
    five_minutes_ago = now - 300

    # 1. 查询最近 5 分钟的 CPU 使用率
    print("\n1. CPU usage (last 5 minutes):")
    results = db.query(
        metric='cpu_usage',
        start=five_minutes_ago,
        end=now,
        tags={'host': 'web-server-1'}
    )
    print(f"   Found {len(results)} data points")
    if results:
        print(f"   Latest: {results[-1][1]:.2f}%")

    # 2. 查询最近 1 小时的平均 CPU
    print("\n2. Average CPU (last hour):")
    avg_cpu = db.query(
        metric='cpu_usage',
        start=one_hour_ago,
        end=now,
        tags={'host': 'web-server-1'},
        aggregation='avg'
    )
    if avg_cpu:
        print(f"   Average: {avg_cpu[0][1]:.2f}%")

    # 3. 查询最近 1 小时的 CPU 最大值
    print("\n3. Max CPU (last hour):")
    max_cpu = db.query(
        metric='cpu_usage',
        start=one_hour_ago,
        end=now,
        tags={'host': 'web-server-1'},
        aggregation='max'
    )
    if max_cpu:
        print(f"   Max: {max_cpu[0][1]:.2f}%")

    # 4. 按 5 分钟降采样
    print("\n4. CPU usage downsampled to 5 minutes:")
    results = db.query(
        metric='cpu_usage',
        start=one_hour_ago,
        end=now,
        downsample='5m',
        aggregation='avg'
    )
    print(f"   Found {len(results)} data points")

    # 5. 查询最新值
    print("\n5. Latest values:")
    latest_cpu = db.latest('cpu_usage', {'host': 'web-server-1'})
    if latest_cpu:
        print(f"   CPU: {latest_cpu[1]:.2f}%")

    latest_mem = db.latest('memory_usage', {'host': 'web-server-1'})
    if latest_mem:
        print(f"   Memory: {latest_mem[1]:.2f} MB")

    # 6. 获取所有指标
    print("\n6. Available metrics:")
    metrics = db.metrics()
    for metric in metrics:
        print(f"   - {metric}")


def main():
    """主函数"""
    # 创建数据库实例
    db = TimeSeriesDB(
        data_dir='./monitoring_data',
        default_ttl=86400 * 7  # 7 天保留
    )

    try:
        # 生成监控数据
        generate_monitoring_data(db, duration=3600)

        # 查询示例
        query_examples(db)

        # 显示统计信息
        print("\n=== Database Stats ===")
        stats = db.get_stats()
        print(f"Storage stats: {stats['storage']}")

    finally:
        db.close()


if __name__ == '__main__':
    main()
