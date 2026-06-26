"""
设备管理 - Device Manager

模拟鸿蒙的分布式设备管理能力：
- 设备发现
- 设备连接
- 设备状态管理
- 设备能力描述
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DeviceInfo:
    """
    设备信息 - 模拟鸿蒙设备信息

    鸿蒙设备信息包含：
    - 设备 ID
    - 设备名称
    - 设备类型（手机、平板、手表、电视等）
    - 设备能力（屏幕尺寸、算力、传感器等）
    - 在线状态
    - 安全等级
    """
    device_id: str
    device_name: str
    device_type: str = 'phone'  # phone, tablet, watch, tv, pc, car
    os_version: str = 'HarmonyOS 4.0'
    capabilities: Dict[str, Any] = field(default_factory=dict)
    is_online: bool = True
    security_level: int = 3  # 1-5
    last_seen: float = field(default_factory=time.time)
    ip_address: str = ''
    signal_strength: int = 100  # 0-100

    def to_dict(self) -> Dict:
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'os_version': self.os_version,
            'is_online': self.is_online,
            'security_level': self.security_level,
            'signal_strength': self.signal_strength,
            'capabilities': self.capabilities,
        }


class DeviceManager:
    """
    设备管理器 - 模拟鸿蒙分布式设备管理

    核心功能：
    1. 设备发现：自动发现附近设备
    2. 设备连接：建立设备间连接
    3. 设备管理：添加、移除、更新设备信息
    4. 设备筛选：按条件筛选可用设备
    """

    def __init__(self):
        self._devices: Dict[str, DeviceInfo] = {}
        self._connected_devices: Set[str] = set()
        self._discovery_callbacks: List[callable] = []
        self._device_events: List[Dict] = []

    def add_device(self, device: DeviceInfo) -> bool:
        """添加设备"""
        self._devices[device.device_id] = device
        self._log_event('device_added', device_id=device.device_id, name=device.device_name)
        return True

    def remove_device(self, device_id: str) -> bool:
        """移除设备"""
        if device_id in self._devices:
            del self._devices[device_id]
            self._connected_devices.discard(device_id)
            self._log_event('device_removed', device_id=device_id)
            return True
        return False

    def set_device_online(self, device_id: str, online: bool = True):
        """设置设备在线状态"""
        if device_id in self._devices:
            self._devices[device_id].is_online = online
            self._devices[device_id].last_seen = time.time()
            if online:
                self._connected_devices.add(device_id)
            else:
                self._connected_devices.discard(device_id)
            self._log_event('device_status_change', device_id=device_id, online=online)

    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """获取设备信息"""
        return self._devices.get(device_id)

    def get_all_devices(self) -> List[DeviceInfo]:
        return list(self._devices.values())

    def get_online_devices(self) -> List[DeviceInfo]:
        """获取在线设备"""
        return [d for d in self._devices.values() if d.is_online]

    def get_connected_devices(self) -> List[str]:
        """获取已连接设备 ID 列表"""
        return list(self._connected_devices)

    def find_devices(self, device_type: Optional[str] = None,
                     min_security: int = 1) -> List[DeviceInfo]:
        """
        按条件筛选设备

        模拟鸿蒙的设备发现能力：
        - 按类型筛选
        - 按安全等级筛选
        """
        results = []
        for device in self._devices.values():
            if not device.is_online:
                continue
            if device_type and device.device_type != device_type:
                continue
            if device.security_level < min_security:
                continue
            results.append(device)
        return results

    def connect_device(self, device_id: str) -> bool:
        """
        连接设备

        模拟分布式软总线连接：
        1. 设备认证
        2. 建立连接
        3. 能力协商
        """
        device = self._devices.get(device_id)
        if not device:
            return False

        # 模拟连接流程
        device.is_online = True
        self._connected_devices.add(device_id)
        self._log_event('device_connected', device_id=device_id)
        return True

    def disconnect_device(self, device_id: str):
        """断开设备连接"""
        self._connected_devices.discard(device_id)
        self._log_event('device_disconnected', device_id=device_id)

    def get_device_capabilities(self, device_id: str) -> Dict:
        """获取设备能力描述"""
        device = self._devices.get(device_id)
        if device:
            return device.capabilities
        return {}

    def _log_event(self, event_type: str, **kwargs):
        """记录设备事件"""
        self._device_events.append({
            'timestamp': time.time(),
            'event': event_type,
            **kwargs,
        })

    def get_device_events(self) -> List[Dict]:
        return list(self._device_events)

    def get_device_count(self) -> int:
        return len(self._devices)

    def get_online_count(self) -> int:
        return len(self._connected_devices)

    def __repr__(self):
        return f'DeviceManager(devices={len(self._devices)}, connected={len(self._connected_devices)})'
