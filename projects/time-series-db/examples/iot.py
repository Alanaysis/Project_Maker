"""
IoT 数据存储示例

演示如何使用时间序列数据库存储和查询 IoT 传感器数据。
"""

import time
import random
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import TimeSeriesDB


def generate_iot_data(db: TimeSeriesDB, num_sensors: int = 10, duration: int = 3600):
    """
    生成模拟 IoT 传感器数据

    Args:
        db: 数据库实例
        num_sensors: 传感器数量
        duration: 数据持续时间（秒）
    """
    print(f"Generating data for {num_sensors} sensors over {duration} seconds...")

    current_time = int(time.time()) - duration
    points = []

    # 传感器配置
    sensor_configs = [
        {'id': f'sensor-{i:03d}', 'location': f'warehouse-{chr(65 + i % 3)}', 'floor': str(i % 3 + 1)}
        for i in range(num_sensors)
    ]

    for i in range(duration):
        timestamp = current_time + i

        for sensor in sensor_configs:
            # 温度 (20-30°C)
            temp_base = 25 + 5 * (i % 600) / 600
            temp_value = temp_base + random.uniform(-2, 2)

            points.append({
                'metric': 'temperature',
                'tags': {
                    'device': sensor['id'],
                    'location': sensor['location'],
                    'floor': sensor['floor']
                },
                'timestamp': timestamp,
                'value': temp_value
            })

            # 湿度 (40-60%)
            humidity_base = 50 + 10 * (i % 300) / 300
            humidity_value = humidity_base + random.uniform(-5, 5)

            points.append({
                'metric': 'humidity',
                'tags': {
                    'device': sensor['id'],
                    'location': sensor['location'],
                    'floor': sensor['floor']
                },
                'timestamp': timestamp,
                'value': humidity_value
            })

            # 空气质量 (0-500 AQI)
            aqi_base = 50 + 30 * (i % 900) / 900
            aqi_value = aqi_base + random.uniform(-10, 10)

            points.append({
                'metric': 'air_quality',
                'tags': {
                    'device': sensor['id'],
                    'location': sensor['location'],
                    'floor': sensor['floor']
                },
                'timestamp': timestamp,
                'value': aqi_value
            })

        # 每 1000 个点批量写入一次
        if len(points) >= 1000:
            db.write_batch(points)
            points = []

    # 写入剩余数据
    if points:
        db.write_batch(points)

    print(f"Generated {duration * num_sensors * 3} data points")


def query_examples(db: TimeSeriesDB):
    """查询示例"""
    print("\n=== Query Examples ===")

    now = int(time.time())
    one_hour_ago = now - 3600
    ten_minutes_ago = now - 600

    # 1. 查询单个传感器的温度
    print("\n1. Temperature for sensor-001 (last 10 minutes):")
    results = db.query(
        metric='temperature',
        start=ten_minutes_ago,
        end=now,
        tags={'device': 'sensor-001'}
    )
    print(f"   Found {len(results)} data points")
    if results:
        print(f"   Latest: {results[-1][1]:.2f}°C")

    # 2. 查询某个仓库的平均温度
    print("\n2. Average temperature for warehouse-A (last hour):")
    avg_temp = db.query(
        metric='temperature',
        start=one_hour_ago,
        end=now,
        tags={'location': 'warehouse-A'},
        aggregation='avg'
    )
    if avg_temp:
        print(f"   Average: {avg_temp[0][1]:.2f}°C")

    # 3. 查询温度最大值
    print("\n3. Max temperature (last hour):")
    max_temp = db.query(
        metric='temperature',
        start=one_hour_ago,
        end=now,
        aggregation='max'
    )
    if max_temp:
        print(f"   Max: {max_temp[0][1]:.2f}°C")

    # 4. 按 10 分钟降采样
    print("\n4. Temperature downsampled to 10 minutes:")
    results = db.query(
        metric='temperature',
        start=one_hour_ago,
        end=now,
        downsample='10m',
        aggregation='avg'
    )
    print(f"   Found {len(results)} data points")

    # 5. 查询最新值
    print("\n5. Latest values for sensor-001:")
    latest_temp = db.latest('temperature', {'device': 'sensor-001'})
    if latest_temp:
        print(f"   Temperature: {latest_temp[1]:.2f}°C")

    latest_humidity = db.latest('humidity', {'device': 'sensor-001'})
    if latest_humidity:
        print(f"   Humidity: {latest_humidity[1]:.2f}%")

    latest_aqi = db.latest('air_quality', {'device': 'sensor-001'})
    if latest_aqi:
        print(f"   Air Quality: {latest_aqi[1]:.2f} AQI")

    # 6. 获取所有指标
    print("\n6. Available metrics:")
    metrics = db.metrics()
    for metric in metrics:
        print(f"   - {metric}")

    # 7. 获取标签值
    print("\n7. Available locations:")
    locations = db.tag_values('temperature', 'location')
    for location in locations:
        print(f"   - {location}")


def temperature_alert(db: TimeSeriesDB, threshold: float = 30.0):
    """温度告警示例"""
    print("\n=== Temperature Alert Check ===")

    now = int(time.time())
    five_minutes_ago = now - 300

    # 查询所有传感器的最新温度
    metrics = db.metrics()
    if 'temperature' not in metrics:
        print("No temperature data found")
        return

    # 获取所有设备
    devices = db.tag_values('temperature', 'device')

    alerts = []
    for device in devices:
        latest = db.latest('temperature', {'device': device})
        if latest and latest[1] > threshold:
            alerts.append({
                'device': device,
                'temperature': latest[1],
                'timestamp': latest[0]
            })

    if alerts:
        print(f"Found {len(alerts)} alerts (threshold: {threshold}°C):")
        for alert in alerts:
            print(f"   {alert['device']}: {alert['temperature']:.2f}°C")
    else:
        print(f"No alerts (threshold: {threshold}°C)")


def main():
    """主函数"""
    # 创建数据库实例
    db = TimeSeriesDB(
        data_dir='./iot_data',
        default_ttl=86400 * 90  # 90 天保留
    )

    try:
        # 生成 IoT 数据
        generate_iot_data(db, num_sensors=10, duration=3600)

        # 查询示例
        query_examples(db)

        # 温度告警检查
        temperature_alert(db, threshold=28.0)

        # 显示统计信息
        print("\n=== Database Stats ===")
        stats = db.get_stats()
        print(f"Storage stats: {stats['storage']}")

    finally:
        db.close()


if __name__ == '__main__':
    main()
