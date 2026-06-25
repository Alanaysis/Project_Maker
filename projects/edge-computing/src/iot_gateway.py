"""IoT 网关模块 - IoT 数据处理和实时分析"""

import time
import json
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict, deque
import threading


class DeviceStatus(Enum):
    """设备状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class DataType(Enum):
    """数据类型"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    LIGHT = "light"
    MOTION = "motion"
    GPS = "gps"
    VOLTAGE = "voltage"
    CURRENT = "current"
    CUSTOM = "custom"


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class IoTDevice:
    """IoT 设备"""
    device_id: str
    name: str
    device_type: str
    location: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_seen: Optional[float] = None
    battery_level: Optional[float] = None

    def update_status(self, status: DeviceStatus) -> None:
        """更新设备状态"""
        self.status = status
        if status == DeviceStatus.ONLINE:
            self.last_seen = time.time()

    def is_alive(self, timeout: float = 300.0) -> bool:
        """检查设备是否在线"""
        if self.last_seen is None:
            return False
        return (time.time() - self.last_seen) < timeout

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.device_type,
            "location": self.location,
            "metadata": self.metadata,
            "status": self.status.value,
            "last_seen": self.last_seen,
            "battery_level": self.battery_level,
        }


@dataclass
class SensorReading:
    """传感器读数"""
    reading_id: str
    device_id: str
    data_type: DataType
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    quality: float = 1.0  # 数据质量 (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "device_id": self.device_id,
            "data_type": self.data_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "quality": self.quality,
            "metadata": self.metadata,
        }


@dataclass
class Alert:
    """告警"""
    alert_id: str
    device_id: str
    level: AlertLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    data: Optional[Dict[str, Any]] = None
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "device_id": self.device_id,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data,
            "acknowledged": self.acknowledged,
        }


class DeviceRegistry:
    """设备注册表

    管理所有连接的 IoT 设备。
    """

    def __init__(self):
        self._devices: Dict[str, IoTDevice] = {}
        self._device_types: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def register(self, device: IoTDevice) -> bool:
        """注册设备"""
        with self._lock:
            if device.device_id in self._devices:
                return False

            self._devices[device.device_id] = device
            self._device_types[device.device_type].add(device.device_id)
            return True

    def unregister(self, device_id: str) -> bool:
        """注销设备"""
        with self._lock:
            device = self._devices.pop(device_id, None)
            if device is None:
                return False

            self._device_types[device.device_type].discard(device_id)
            return True

    def get_device(self, device_id: str) -> Optional[IoTDevice]:
        """获取设备"""
        return self._devices.get(device_id)

    def get_devices_by_type(self, device_type: str) -> List[IoTDevice]:
        """按类型获取设备"""
        device_ids = self._device_types.get(device_type, set())
        return [self._devices[did] for did in device_ids if did in self._devices]

    def get_online_devices(self) -> List[IoTDevice]:
        """获取在线设备"""
        return [d for d in self._devices.values() if d.status == DeviceStatus.ONLINE]

    def update_device_status(self, device_id: str, status: DeviceStatus) -> bool:
        """更新设备状态"""
        device = self.get_device(device_id)
        if device is None:
            return False

        device.update_status(status)
        return True

    def heartbeat(self, device_id: str) -> bool:
        """设备心跳"""
        device = self.get_device(device_id)
        if device is None:
            return False

        device.last_seen = time.time()
        device.status = DeviceStatus.ONLINE
        return True

    def check_device_health(self, timeout: float = 300.0) -> Dict[str, Any]:
        """检查设备健康状态"""
        online_count = 0
        offline_count = 0

        for device in self._devices.values():
            if device.is_alive(timeout):
                online_count += 1
            else:
                device.status = DeviceStatus.OFFLINE
                offline_count += 1

        return {
            "total_devices": len(self._devices),
            "online": online_count,
            "offline": offline_count,
        }

    def get_all_devices(self) -> List[IoTDevice]:
        """获取所有设备"""
        return list(self._devices.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        status_counts = defaultdict(int)
        for device in self._devices.values():
            status_counts[device.status.value] += 1

        return {
            "total_devices": len(self._devices),
            "device_types": len(self._device_types),
            "status_counts": dict(status_counts),
        }


class DataBuffer:
    """数据缓冲区

    缓存传感器数据，支持批量读取和时间窗口查询。
    """

    def __init__(self, max_size: int = 10000, ttl: float = 3600.0):
        self.max_size = max_size
        self.ttl = ttl  # 数据存活时间（秒）
        self._buffer: deque = deque(maxlen=max_size)
        self._index_by_device: Dict[str, List[SensorReading]] = defaultdict(list)
        self._lock = threading.Lock()

    def add(self, reading: SensorReading) -> None:
        """添加传感器读数"""
        with self._lock:
            self._buffer.append(reading)
            self._index_by_device[reading.device_id].append(reading)
            self._cleanup()

    def _cleanup(self) -> None:
        """清理过期数据"""
        cutoff = time.time() - self.ttl
        while self._buffer and self._buffer[0].timestamp < cutoff:
            old_reading = self._buffer.popleft()
            device_readings = self._index_by_device.get(old_reading.device_id, [])
            if device_readings and device_readings[0] == old_reading:
                device_readings.pop(0)

    def get_recent(
        self,
        count: int = 100,
        device_id: Optional[str] = None,
        data_type: Optional[DataType] = None,
    ) -> List[SensorReading]:
        """获取最近的数据"""
        with self._lock:
            if device_id:
                readings = self._index_by_device.get(device_id, [])
            else:
                readings = list(self._buffer)

            if data_type:
                readings = [r for r in readings if r.data_type == data_type]

            return readings[-count:]

    def get_time_range(
        self,
        start_time: float,
        end_time: float,
        device_id: Optional[str] = None,
    ) -> List[SensorReading]:
        """获取时间范围内的数据"""
        with self._lock:
            if device_id:
                readings = self._index_by_device.get(device_id, [])
            else:
                readings = list(self._buffer)

            return [
                r for r in readings
                if start_time <= r.timestamp <= end_time
            ]

    def get_latest(self, device_id: str, data_type: DataType) -> Optional[SensorReading]:
        """获取设备最新的指定类型数据"""
        with self._lock:
            readings = self._index_by_device.get(device_id, [])
            for reading in reversed(readings):
                if reading.data_type == data_type:
                    return reading
            return None

    def clear(self) -> None:
        """清空缓冲区"""
        with self._lock:
            self._buffer.clear()
            self._index_by_device.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "buffer_size": len(self._buffer),
            "max_size": self.max_size,
            "device_count": len(self._index_by_device),
            "ttl": self.ttl,
        }


class AlertManager:
    """告警管理器

    管理 IoT 设备的告警，支持告警规则和告警通知。
    """

    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self._alerts: deque = deque(maxlen=max_alerts)
        self._rules: List[Dict[str, Any]] = []
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

        # 统计
        self._stats = defaultdict(int)

    def add_rule(
        self,
        rule_id: str,
        device_id: Optional[str] = None,
        data_type: Optional[DataType] = None,
        condition: str = "gt",
        threshold: float = 0.0,
        level: AlertLevel = AlertLevel.WARNING,
        message: str = "",
    ) -> None:
        """添加告警规则

        Args:
            rule_id: 规则 ID
            device_id: 设备 ID (None 表示所有设备)
            data_type: 数据类型 (None 表示所有类型)
            condition: 条件 (gt, lt, eq, gte, lte)
            threshold: 阈值
            level: 告警级别
            message: 告警消息模板
        """
        rule = {
            "rule_id": rule_id,
            "device_id": device_id,
            "data_type": data_type,
            "condition": condition,
            "threshold": threshold,
            "level": level,
            "message": message,
        }

        with self._lock:
            self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        with self._lock:
            for i, rule in enumerate(self._rules):
                if rule["rule_id"] == rule_id:
                    self._rules.pop(i)
                    return True
            return False

    def check_reading(self, reading: SensorReading) -> Optional[Alert]:
        """检查传感器读数是否触发告警"""
        with self._lock:
            for rule in self._rules:
                if self._match_rule(reading, rule):
                    if self._evaluate_condition(reading.value, rule["condition"], rule["threshold"]):
                        alert = self._create_alert(reading, rule)
                        self._alerts.append(alert)
                        self._stats[rule["level"].value] += 1
                        self._notify_callbacks(alert)
                        return alert

        return None

    def _match_rule(self, reading: SensorReading, rule: Dict[str, Any]) -> bool:
        """检查读数是否匹配规则"""
        if rule["device_id"] and rule["device_id"] != reading.device_id:
            return False
        if rule["data_type"] and rule["data_type"] != reading.data_type:
            return False
        return True

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估条件"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.0001
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        return False

    def _create_alert(self, reading: SensorReading, rule: Dict[str, Any]) -> Alert:
        """创建告警"""
        message = rule["message"] or f"{reading.data_type.value} {rule['condition']} {rule['threshold']}"
        message = message.replace("{device}", reading.device_id)
        message = message.replace("{value}", str(reading.value))

        return Alert(
            alert_id=str(uuid.uuid4()),
            device_id=reading.device_id,
            level=rule["level"],
            message=message,
            data=reading.to_dict(),
        )

    def _notify_callbacks(self, alert: Alert) -> None:
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception:
                pass

    def register_callback(self, callback: Callable) -> None:
        """注册告警回调"""
        self._callbacks.append(callback)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    return True
            return False

    def get_alerts(
        self,
        device_id: Optional[str] = None,
        level: Optional[AlertLevel] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """获取告警列表"""
        with self._lock:
            alerts = list(self._alerts)

        if device_id:
            alerts = [a for a in alerts if a.device_id == device_id]
        if level:
            alerts = [a for a in alerts if a.level == level]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return alerts[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_alerts": len(self._alerts),
                "active_rules": len(self._rules),
                "stats": dict(self._stats),
            }


class RealtimeAnalyzer:
    """实时分析器

    对 IoT 数据进行实时分析，包括统计计算、趋势检测等。
    """

    def __init__(self, window_size: float = 300.0):
        self.window_size = window_size  # 分析窗口大小（秒）
        self._stats_cache: Dict[str, Dict[str, float]] = {}
        self._cache_ttl: float = 10.0  # 缓存有效期（秒）
        self._last_cache_time: float = 0.0

    def calculate_stats(self, readings: List[SensorReading]) -> Dict[str, float]:
        """计算统计信息"""
        if not readings:
            return {}

        values = [r.value for r in readings if r.quality >= 0.5]
        if not values:
            return {}

        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n if n > 1 else 0

        return {
            "count": n,
            "sum": sum(values),
            "mean": mean,
            "min": min(values),
            "max": max(values),
            "stddev": variance ** 0.5,
            "range": max(values) - min(values),
        }

    def detect_trend(self, readings: List[SensorReading]) -> Dict[str, Any]:
        """检测趋势

        使用简单的线性回归检测数据趋势。
        """
        if len(readings) < 2:
            return {"trend": "insufficient_data"}

        values = [(r.timestamp, r.value) for r in readings if r.quality >= 0.5]
        if len(values) < 2:
            return {"trend": "insufficient_data"}

        # 简单线性回归
        n = len(values)
        sum_x = sum(x for x, _ in values)
        sum_y = sum(y for _, y in values)
        sum_xy = sum(x * y for x, y in values)
        sum_x2 = sum(x * x for x, _ in values)

        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return {"trend": "stable", "slope": 0.0}

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # 判断趋势
        if abs(slope) < 0.001:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        return {
            "trend": trend,
            "slope": slope,
            "intercept": intercept,
            "confidence": min(1.0, abs(slope) * 100),
        }

    def detect_anomalies(
        self,
        readings: List[SensorReading],
        threshold: float = 2.0,
    ) -> List[SensorReading]:
        """检测异常值

        使用 Z-score 方法检测异常。
        """
        if len(readings) < 3:
            return []

        values = [r.value for r in readings if r.quality >= 0.5]
        if len(values) < 3:
            return []

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = variance ** 0.5

        if stddev < 1e-10:
            return []

        anomalies = []
        for reading in readings:
            if reading.quality < 0.5:
                continue

            z_score = abs(reading.value - mean) / stddev
            if z_score > threshold:
                anomalies.append(reading)

        return anomalies

    def get_summary(
        self,
        device_id: str,
        data_type: DataType,
        buffer: DataBuffer,
    ) -> Dict[str, Any]:
        """获取数据摘要"""
        readings = buffer.get_recent(
            count=1000,
            device_id=device_id,
            data_type=data_type,
        )

        if not readings:
            return {"device_id": device_id, "data_type": data_type.value, "no_data": True}

        stats = self.calculate_stats(readings)
        trend = self.detect_trend(readings)
        anomalies = self.detect_anomalies(readings)

        return {
            "device_id": device_id,
            "data_type": data_type.value,
            "stats": stats,
            "trend": trend,
            "anomaly_count": len(anomalies),
            "latest_value": readings[-1].value if readings else None,
            "latest_timestamp": readings[-1].timestamp if readings else None,
        }


class IoTGateway:
    """IoT 网关

    边缘计算 IoT 网关，负责设备管理、数据收集、实时分析和告警。
    """

    def __init__(self, gateway_id: str = "gateway-1"):
        self.gateway_id = gateway_id

        # 核心组件
        self.device_registry = DeviceRegistry()
        self.data_buffer = DataBuffer()
        self.alert_manager = AlertManager()
        self.analyzer = RealtimeAnalyzer()

        # 回调
        self._data_callbacks: List[Callable] = []
        self._running = False
        self._stats = defaultdict(int)

    def start(self) -> None:
        """启动网关"""
        self._running = True

    def stop(self) -> None:
        """停止网关"""
        self._running = False

    def register_device(self, device: IoTDevice) -> bool:
        """注册设备"""
        success = self.device_registry.register(device)
        if success:
            self._stats["devices_registered"] += 1
        return success

    def unregister_device(self, device_id: str) -> bool:
        """注销设备"""
        return self.device_registry.unregister(device_id)

    def receive_data(self, reading: SensorReading) -> Dict[str, Any]:
        """接收传感器数据

        Args:
            reading: 传感器读数

        Returns:
            处理结果
        """
        if not self._running:
            return {"success": False, "error": "Gateway not running"}

        # 更新设备状态
        self.device_registry.heartbeat(reading.device_id)

        # 存入缓冲区
        self.data_buffer.add(reading)

        # 检查告警
        alert = self.alert_manager.check_reading(reading)

        # 触发数据回调
        for callback in self._data_callbacks:
            try:
                callback(reading)
            except Exception:
                pass

        self._stats["readings_received"] += 1
        if alert:
            self._stats["alerts_triggered"] += 1

        return {
            "success": True,
            "reading_id": reading.reading_id,
            "alert": alert.to_dict() if alert else None,
        }

    def register_data_callback(self, callback: Callable) -> None:
        """注册数据回调"""
        self._data_callbacks.append(callback)

    def add_alert_rule(self, **kwargs) -> None:
        """添加告警规则"""
        self.alert_manager.add_rule(**kwargs)

    def get_device_summary(self, device_id: str) -> Dict[str, Any]:
        """获取设备数据摘要"""
        device = self.device_registry.get_device(device_id)
        if device is None:
            return {"error": "Device not found"}

        summaries = {}
        for data_type in DataType:
            summary = self.analyzer.get_summary(
                device_id, data_type, self.data_buffer
            )
            if not summary.get("no_data"):
                summaries[data_type.value] = summary

        return {
            "device": device.to_dict(),
            "data_summaries": summaries,
        }

    def get_gateway_stats(self) -> Dict[str, Any]:
        """获取网关统计信息"""
        return {
            "gateway_id": self.gateway_id,
            "running": self._running,
            "device_stats": self.device_registry.get_stats(),
            "buffer_stats": self.data_buffer.get_stats(),
            "alert_stats": self.alert_manager.get_stats(),
            "processing_stats": dict(self._stats),
        }

    def __repr__(self) -> str:
        return (
            f"IoTGateway(id={self.gateway_id}, "
            f"devices={self.device_registry.get_stats()['total_devices']}, "
            f"buffer={self.data_buffer.get_stats()['buffer_size']})"
        )
