"""IoT 网关模块测试"""

import time
import pytest
from src.iot_gateway import (
    DeviceStatus, DataType, AlertLevel,
    IoTDevice, SensorReading, Alert,
    DeviceRegistry, DataBuffer, AlertManager, RealtimeAnalyzer, IoTGateway,
)


@pytest.fixture
def sample_device():
    """创建测试设备"""
    return IoTDevice(
        device_id="device-1",
        name="Temperature Sensor",
        device_type="sensor",
        location={"lat": 39.9, "lon": 116.4},
    )


@pytest.fixture
def sample_reading():
    """创建测试传感器读数"""
    return SensorReading(
        reading_id="reading-1",
        device_id="device-1",
        data_type=DataType.TEMPERATURE,
        value=25.5,
        unit="°C",
    )


@pytest.fixture
def device_registry():
    """创建设备注册表"""
    registry = DeviceRegistry()
    # 注册测试设备
    for i in range(3):
        device = IoTDevice(
            device_id=f"device-{i}",
            name=f"Sensor {i}",
            device_type="sensor",
        )
        device.update_status(DeviceStatus.ONLINE)
        registry.register(device)
    return registry


class TestIoTDevice:
    """IoT 设备测试"""

    def test_device_creation(self, sample_device):
        """测试设备创建"""
        assert sample_device.device_id == "device-1"
        assert sample_device.name == "Temperature Sensor"
        assert sample_device.device_type == "sensor"
        assert sample_device.status == DeviceStatus.OFFLINE

    def test_update_status(self, sample_device):
        """测试状态更新"""
        sample_device.update_status(DeviceStatus.ONLINE)
        assert sample_device.status == DeviceStatus.ONLINE
        assert sample_device.last_seen is not None

    def test_is_alive(self, sample_device):
        """测试存活检查"""
        # 刚创建，last_seen 为 None
        assert sample_device.is_alive() is False

        # 更新状态后
        sample_device.update_status(DeviceStatus.ONLINE)
        assert sample_device.is_alive() is True

    def test_to_dict(self, sample_device):
        """测试字典转换"""
        data = sample_device.to_dict()
        assert data["device_id"] == "device-1"
        assert data["status"] == "offline"


class TestSensorReading:
    """传感器读数测试"""

    def test_reading_creation(self, sample_reading):
        """测试读数创建"""
        assert sample_reading.device_id == "device-1"
        assert sample_reading.data_type == DataType.TEMPERATURE
        assert sample_reading.value == 25.5
        assert sample_reading.unit == "°C"

    def test_to_dict(self, sample_reading):
        """测试字典转换"""
        data = sample_reading.to_dict()
        assert data["data_type"] == "temperature"
        assert data["value"] == 25.5


class TestDeviceRegistry:
    """设备注册表测试"""

    def test_register_device(self, sample_device):
        """测试设备注册"""
        registry = DeviceRegistry()
        result = registry.register(sample_device)
        assert result is True

    def test_register_duplicate(self, sample_device):
        """测试重复注册"""
        registry = DeviceRegistry()
        registry.register(sample_device)
        result = registry.register(sample_device)
        assert result is False

    def test_unregister_device(self, sample_device):
        """测试设备注销"""
        registry = DeviceRegistry()
        registry.register(sample_device)

        result = registry.unregister("device-1")
        assert result is True
        assert registry.get_device("device-1") is None

    def test_get_device(self, device_registry):
        """测试获取设备"""
        device = device_registry.get_device("device-0")
        assert device is not None
        assert device.device_id == "device-0"

    def test_get_devices_by_type(self, device_registry):
        """测试按类型获取设备"""
        sensors = device_registry.get_devices_by_type("sensor")
        assert len(sensors) == 3

    def test_get_online_devices(self, device_registry):
        """测试获取在线设备"""
        online = device_registry.get_online_devices()
        assert len(online) == 3

    def test_heartbeat(self, device_registry):
        """测试心跳"""
        result = device_registry.heartbeat("device-0")
        assert result is True

        device = device_registry.get_device("device-0")
        assert device.status == DeviceStatus.ONLINE

    def test_check_device_health(self, device_registry):
        """测试设备健康检查"""
        health = device_registry.check_device_health()
        assert health["total_devices"] == 3
        assert health["online"] == 3
        assert health["offline"] == 0

    def test_stats(self, device_registry):
        """测试统计信息"""
        stats = device_registry.get_stats()
        assert stats["total_devices"] == 3
        assert stats["device_types"] == 1


class TestDataBuffer:
    """数据缓冲区测试"""

    def test_add_reading(self):
        """测试添加读数"""
        buffer = DataBuffer(max_size=100)

        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=25.0,
            unit="°C",
        )

        buffer.add(reading)
        assert buffer.get_stats()["buffer_size"] == 1

    def test_get_recent(self):
        """测试获取最近数据"""
        buffer = DataBuffer(max_size=100)

        for i in range(10):
            buffer.add(SensorReading(
                reading_id=f"r-{i}",
                device_id="device-1",
                data_type=DataType.TEMPERATURE,
                value=float(i),
                unit="°C",
            ))

        recent = buffer.get_recent(count=5)
        assert len(recent) == 5
        assert recent[-1].value == 9.0

    def test_get_recent_by_device(self):
        """测试按设备获取数据"""
        buffer = DataBuffer(max_size=100)

        # 添加来自不同设备的数据
        for i in range(5):
            buffer.add(SensorReading(
                reading_id=f"r1-{i}",
                device_id="device-1",
                data_type=DataType.TEMPERATURE,
                value=float(i),
                unit="°C",
            ))
            buffer.add(SensorReading(
                reading_id=f"r2-{i}",
                device_id="device-2",
                data_type=DataType.HUMIDITY,
                value=float(i + 50),
                unit="%",
            ))

        device1_data = buffer.get_recent(device_id="device-1")
        assert len(device1_data) == 5

    def test_max_size(self):
        """测试最大容量"""
        buffer = DataBuffer(max_size=5)

        for i in range(10):
            buffer.add(SensorReading(
                reading_id=f"r-{i}",
                device_id="device-1",
                data_type=DataType.TEMPERATURE,
                value=float(i),
                unit="°C",
            ))

        assert buffer.get_stats()["buffer_size"] == 5

    def test_clear(self):
        """测试清空缓冲区"""
        buffer = DataBuffer(max_size=100)

        buffer.add(SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=25.0,
            unit="°C",
        ))

        buffer.clear()
        assert buffer.get_stats()["buffer_size"] == 0


class TestAlertManager:
    """告警管理器测试"""

    def test_add_rule(self):
        """测试添加规则"""
        manager = AlertManager()
        manager.add_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
            level=AlertLevel.WARNING,
        )

        stats = manager.get_stats()
        assert stats["active_rules"] == 1

    def test_check_triggers_alert(self):
        """测试检查触发告警"""
        manager = AlertManager()
        manager.add_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
            level=AlertLevel.WARNING,
            message="Temperature too high: {value}",
        )

        # 创建高温读数
        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=35.0,
            unit="°C",
        )

        alert = manager.check_reading(reading)
        assert alert is not None
        assert alert.level == AlertLevel.WARNING
        assert "35.0" in alert.message

    def test_no_alert_within_threshold(self):
        """测试阈值内不触发告警"""
        manager = AlertManager()
        manager.add_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
        )

        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=25.0,
            unit="°C",
        )

        alert = manager.check_reading(reading)
        assert alert is None

    def test_alert_callback(self):
        """测试告警回调"""
        manager = AlertManager()

        alerts_received = []
        manager.register_callback(lambda a: alerts_received.append(a))

        manager.add_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
        )

        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=35.0,
            unit="°C",
        )

        manager.check_reading(reading)
        assert len(alerts_received) == 1

    def test_acknowledge_alert(self):
        """测试确认告警"""
        manager = AlertManager()
        manager.add_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
        )

        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=35.0,
            unit="°C",
        )

        alert = manager.check_reading(reading)
        assert alert.acknowledged is False

        manager.acknowledge_alert(alert.alert_id)
        alerts = manager.get_alerts(acknowledged=False)
        assert len(alerts) == 0

    def test_get_alerts_by_device(self):
        """测试按设备获取告警"""
        manager = AlertManager()
        manager.add_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
        )

        # 来自不同设备的告警
        for device_id in ["device-1", "device-2"]:
            reading = SensorReading(
                reading_id=f"r-{device_id}",
                device_id=device_id,
                data_type=DataType.TEMPERATURE,
                value=35.0,
                unit="°C",
            )
            manager.check_reading(reading)

        device1_alerts = manager.get_alerts(device_id="device-1")
        assert len(device1_alerts) == 1


class TestRealtimeAnalyzer:
    """实时分析器测试"""

    def test_calculate_stats(self):
        """测试统计计算"""
        analyzer = RealtimeAnalyzer()

        readings = [
            SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, float(i), "°C")
            for i in range(10)
        ]

        stats = analyzer.calculate_stats(readings)
        assert stats["count"] == 10
        assert stats["mean"] == 4.5
        assert stats["min"] == 0.0
        assert stats["max"] == 9.0

    def test_detect_trend_increasing(self):
        """测试上升趋势检测"""
        analyzer = RealtimeAnalyzer()

        # 使用小的相对时间戳避免浮点精度问题
        readings = [
            SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, float(i) * 10, "°C", timestamp=float(i))
            for i in range(10)
        ]

        trend = analyzer.detect_trend(readings)
        assert trend["trend"] == "increasing"
        assert trend["slope"] > 0

    def test_detect_trend_stable(self):
        """测试稳定趋势检测"""
        analyzer = RealtimeAnalyzer()

        # 使用小的相对时间戳
        readings = [
            SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, 25.0, "°C", timestamp=float(i))
            for i in range(10)
        ]

        trend = analyzer.detect_trend(readings)
        assert trend["trend"] == "stable"

    def test_detect_anomalies(self):
        """测试异常检测"""
        analyzer = RealtimeAnalyzer()

        # 正常数据 + 异常值
        readings = [
            SensorReading(f"r-{i}", "device-1", DataType.TEMPERATURE, 25.0, "°C")
            for i in range(9)
        ]
        readings.append(
            SensorReading("r-anomaly", "device-1", DataType.TEMPERATURE, 100.0, "°C")
        )

        anomalies = analyzer.detect_anomalies(readings)
        assert len(anomalies) == 1
        assert anomalies[0].value == 100.0

    def test_empty_readings(self):
        """测试空数据"""
        analyzer = RealtimeAnalyzer()

        stats = analyzer.calculate_stats([])
        assert stats == {}

        trend = analyzer.detect_trend([])
        assert trend["trend"] == "insufficient_data"


class TestIoTGateway:
    """IoT 网关测试"""

    def test_gateway_creation(self):
        """测试网关创建"""
        gateway = IoTGateway(gateway_id="gw-1")
        assert gateway.gateway_id == "gw-1"

    def test_register_device(self, sample_device):
        """测试设备注册"""
        gateway = IoTGateway()
        result = gateway.register_device(sample_device)
        assert result is True

    def test_start_stop(self):
        """测试启动和停止"""
        gateway = IoTGateway()
        gateway.start()
        assert gateway._running is True

        gateway.stop()
        assert gateway._running is False

    def test_receive_data(self, sample_device):
        """测试接收数据"""
        gateway = IoTGateway()
        gateway.register_device(sample_device)
        gateway.start()

        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=25.0,
            unit="°C",
        )

        result = gateway.receive_data(reading)
        assert result["success"] is True
        assert result["alert"] is None

    def test_receive_data_triggers_alert(self, sample_device):
        """测试数据接收触发告警"""
        gateway = IoTGateway()
        gateway.register_device(sample_device)
        gateway.start()

        # 添加告警规则
        gateway.add_alert_rule(
            rule_id="r1",
            data_type=DataType.TEMPERATURE,
            condition="gt",
            threshold=30.0,
            level=AlertLevel.WARNING,
        )

        # 高温数据
        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=35.0,
            unit="°C",
        )

        result = gateway.receive_data(reading)
        assert result["success"] is True
        assert result["alert"] is not None

    def test_data_callback(self, sample_device):
        """测试数据回调"""
        gateway = IoTGateway()
        gateway.register_device(sample_device)
        gateway.start()

        received_data = []
        gateway.register_data_callback(lambda r: received_data.append(r))

        reading = SensorReading(
            reading_id="r-1",
            device_id="device-1",
            data_type=DataType.TEMPERATURE,
            value=25.0,
            unit="°C",
        )

        gateway.receive_data(reading)
        assert len(received_data) == 1

    def test_get_device_summary(self, sample_device):
        """测试获取设备摘要"""
        gateway = IoTGateway()
        gateway.register_device(sample_device)
        gateway.start()

        # 添加一些数据
        for i in range(5):
            reading = SensorReading(
                reading_id=f"r-{i}",
                device_id="device-1",
                data_type=DataType.TEMPERATURE,
                value=20.0 + i,
                unit="°C",
            )
            gateway.receive_data(reading)

        summary = gateway.get_device_summary("device-1")
        assert "device" in summary
        assert "data_summaries" in summary

    def test_gateway_stats(self, sample_device):
        """测试网关统计"""
        gateway = IoTGateway()
        gateway.register_device(sample_device)
        gateway.start()

        stats = gateway.get_gateway_stats()
        assert stats["gateway_id"] == "gateway-1"
        assert stats["device_stats"]["total_devices"] == 1

    def test_device_offline_after_timeout(self, sample_device):
        """测试设备超时离线"""
        gateway = IoTGateway()
        gateway.register_device(sample_device)

        # 模拟设备很长时间没有心跳
        sample_device.last_seen = time.time() - 600  # 10分钟前

        health = gateway.device_registry.check_device_health(timeout=300)
        assert health["offline"] == 1
