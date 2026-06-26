"""
跨平台框架原理 - Cross-Platform Framework Principles

核心模块：Platform Channel / 桥接机制
功能：模拟 Flutter 与原生平台之间的通信通道

跨平台框架原理说明：
Flutter 应用运行在 Dart VM 中，但需要访问原生平台功能：
- iOS: UIKit, CoreLocation, Camera
- Android: View, LocationManager, Camera2
- Web: DOM, localStorage, Geolocation API

Flutter 通过 Platform Channel 实现跨平台通信：
1. MethodChannel - 方法调用（请求/响应）
2. EventChannel - 事件流（推送）
3. BasicMessageChannel - 消息传递（双向）

通信流程：
Dart ↔ Platform Channel ↔ Platform View ↔ Native Code

本模块模拟：
1. MethodChannel - 方法通道
2. BasicMessageChannel - 消息通道
3. Platform View - 原生视图嵌入
4. Platform Codec - 编解码器
"""

import json
import time
import random
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


# ============================================================
# 平台类型 (Platform Types)
# ============================================================
class PlatformType(Enum):
    """目标平台类型"""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    DESKTOP = "desktop"


# ============================================================
# 平台编解码器 (Platform Codec)
# ============================================================
class StandardCodec:
    """
    StandardCodec - 标准编解码器

    Flutter 使用标准编解码器在 Dart 和原生平台之间序列化数据。
    支持的数据类型：
    - null
    - bool
    - int (64-bit)
    - double
    - String
    - List
    - Map
    - Uint8List
    - Int64List
    - Float64List

    编解码方向：
    Dart → Platform: encode()
    Platform → Dart: decode()
    """

    def __init__(self):
        self._decode_count = 0
        self._encode_count = 0

    def encode(self, value: Any) -> bytes:
        """
        将 Dart 对象编码为平台字节

        模拟序列化过程：
        1. 将 Dart 对象转换为 JSON
        2. 转换为字节数组
        """
        self._encode_count += 1
        json_str = json.dumps(self._encode_value(value), ensure_ascii=False)
        return json_str.encode('utf-8')

    def decode(self, data: bytes) -> Any:
        """
        将平台字节解码为 Dart 对象

        反序列化过程：
        1. 从字节数组解码为 JSON
        2. 转换为 Dart 对象
        """
        self._decode_count += 1
        json_str = data.decode('utf-8')
        return json.loads(json_str)

    def _encode_value(self, value: Any) -> Any:
        """递归编码值"""
        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return value
        elif isinstance(value, float):
            return value
        elif isinstance(value, str):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._encode_value(v) for v in value]
        elif isinstance(value, dict):
            return {str(k): self._encode_value(v) for k, v in value.items()}
        else:
            return str(value)

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "encode_count": self._encode_count,
            "decode_count": self._decode_count,
        }


# ============================================================
# 方法通道 (MethodChannel)
# ============================================================
class MethodChannel:
    """
    MethodChannel - 方法通道

    MethodChannel 用于在 Dart 和原生平台之间进行方法调用。
    这是最常见的 Platform Channel 类型。

    使用场景：
    - 获取设备信息
    - 调用原生 API（相机、位置、文件系统）
    - 显示原生对话框
    - 处理通知

    通信模式：请求/响应（Request/Response）

    Dart 端：
      const channel = MethodChannel('app/channel')
      final result = await channel.invokeMethod('getDeviceInfo')

    原生端（Android）：
      channel.setMethodCallHandler { call, _ ->
          when(call.method) {
              "getDeviceInfo" -> respondWith(deviceInfo)
          }
      }
    """

    def __init__(self, name: str, platform: PlatformType = PlatformType.ANDROID):
        self._name = name
        self._platform = platform
        self._codec = StandardCodec()
        self._handlers: Dict[str, Callable] = {}
        self._call_log: List[Dict[str, Any]] = []
        self._response_delay_ms = random.uniform(1, 10)  # 模拟网络延迟

    @property
    def name(self) -> str:
        return self._name

    @property
    def platform(self) -> PlatformType:
        return self._platform

    def register_handler(self, method: str, handler: Callable):
        """注册方法处理器"""
        self._handlers[method] = handler

    def invoke(self, method: str, args: Optional[Any] = None) -> Any:
        """
        调用原生方法

        Args:
            method: 方法名称
            args: 方法参数

        Returns:
            原生方法的响应
        """
        start_time = time.time()

        # 编码参数
        encoded_args = self._codec.encode(args) if args is not None else None

        # 模拟跨平台通信延迟
        time.sleep(self._response_delay_ms / 1000)

        # 查找并调用处理器
        handler = self._handlers.get(method)
        if handler:
            try:
                response = handler(encoded_args)
            except Exception as e:
                response = {"error": str(e), "code": -32603}
        else:
            response = {
                "error": f"Method not found: {method}",
                "code": -32601,
            }

        # 记录调用
        elapsed = (time.time() - start_time) * 1000
        self._call_log.append({
            "method": method,
            "args": args,
            "response": response,
            "elapsed_ms": round(elapsed, 2),
            "timestamp": time.time(),
        })

        return response

    def invoke_list_method(self, method: str, args_list: List[Any]) -> List[Any]:
        """批量调用方法"""
        results = []
        for args in args_list:
            result = self.invoke(method, args)
            results.append(result)
        return results

    def get_call_log(self) -> List[Dict[str, Any]]:
        return self._call_log.copy()

    def clear_call_log(self):
        self._call_log.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "platform": self._platform.value,
            "registered_handlers": list(self._handlers.keys()),
            "codec_stats": self._codec.stats,
            "call_count": len(self._call_log),
        }


# ============================================================
# 事件通道 (EventChannel)
# ============================================================
class EventChannel:
    """
    EventChannel - 事件通道

    EventChannel 用于从原生平台接收事件流。
    事件流是持续的、可能无限的数据序列。

    使用场景：
    - 传感器数据（加速度计、陀螺仪）
    - 位置更新
    - 网络连接状态变化
    - 电池电量变化

    通信模式：推送（Push）
    """

    def __init__(self, name: str, platform: PlatformType = PlatformType.ANDROID):
        self._name = name
        self._platform = platform
        self._listeners: List[Callable] = []
        self._event_log: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return self._name

    def add_listener(self, listener: Callable):
        """添加事件监听器"""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable):
        """移除事件监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit_event(self, event_data: Any, error: Optional[str] = None):
        """
        从原生平台发出事件

        Args:
            event_data: 事件数据
            error: 可选的错误信息
        """
        event = {
            "data": event_data,
            "error": error,
            "timestamp": time.time(),
        }
        self._event_log.append(event)

        # 通知所有监听器
        for listener in self._listeners:
            try:
                listener(event_data, error)
            except Exception as e:
                self._event_log.append({
                    "error": f"Listener error: {str(e)}",
                    "timestamp": time.time(),
                })

    def get_event_log(self) -> List[Dict[str, Any]]:
        return self._event_log.copy()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "platform": self._platform.value,
            "listeners": len(self._listeners),
            "events_emitted": len(self._event_log),
        }


# ============================================================
# 消息通道 (BasicMessageChannel)
# ============================================================
class BasicMessageChannel:
    """
    BasicMessageChannel - 基本消息通道

    BasicMessageChannel 用于在 Dart 和原生平台之间发送和接收消息。
    与 MethodChannel 不同，它支持双向消息传递，不限于方法调用。

    使用场景：
    - 实时数据交换
    - 消息队列
    - 双向通信协议

    通信模式：双向（Bidirectional）
    """

    def __init__(self, name: str, platform: PlatformType = PlatformType.ANDROID):
        self._name = name
        self._platform = platform
        self._codec = StandardCodec()
        self._message_handlers: List[Callable] = []
        self._message_queue: List[Any] = []
        self._reply_handlers: Dict[int, Callable] = {}
        self._msg_id = 0

    @property
    def name(self) -> str:
        return self._name

    def send(self, message: Any) -> 'BasicMessageChannel':
        """
        发送消息到原生平台

        Returns:
            self for chaining
        """
        encoded = self._codec.encode(message)
        self._message_queue.append({
            "message": message,
            "encoded": encoded,
            "timestamp": time.time(),
        })
        return self

    def register_handler(self, handler: Callable):
        """注册消息处理器"""
        self._message_handlers.append(handler)

    def receive_reply(self, msg_id: int, handler: Callable):
        """注册回复处理器"""
        self._reply_handlers[msg_id] = handler

    def process_reply(self, msg_id: int, reply: Any):
        """处理来自原生的回复"""
        handler = self._reply_handlers.get(msg_id)
        if handler:
            handler(reply)
        self._reply_handlers.pop(msg_id, None)

    def get_message_queue(self) -> List[Dict[str, Any]]:
        return self._message_queue.copy()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "platform": self._platform.value,
            "messages_sent": len(self._message_queue),
            "handlers": len(self._message_handlers),
        }


# ============================================================
# 平台视图嵌入 (Platform View)
# ============================================================
class PlatformView:
    """
    PlatformView - 原生视图嵌入

    PlatformView 允许在 Flutter 应用中嵌入原生视图。
    这是 Flutter 与原生 UI 集成的关键机制。

    在 Android 上：
    - FlutterView 嵌入原生 Android View
    - 原生 View 可以在 Flutter Widget 中显示

    在 iOS 上：
    - FlutterViewController 嵌入原生 UIViewController
    - 原生控件可以在 Flutter 界面中显示

    嵌入方式：
    1. 全嵌入（Full embedding）- 整个 Flutter 界面嵌入原生
    2. 部分嵌入（Partial embedding）- 原生视图嵌入 Flutter
    """

    def __init__(self, platform: PlatformType, view_id: str = "default"):
        self._platform = platform
        self._view_id = view_id
        self._is_created = False
        self._is_visible = False
        self._size = (0, 0)
        self._z_order = 0  # z-order 控制视图层级

    @property
    def platform(self) -> PlatformType:
        return self._platform

    @property
    def view_id(self) -> str:
        return self._view_id

    @property
    def is_created(self) -> bool:
        return self._is_created

    @property
    def is_visible(self) -> bool:
        return self._is_visible

    def create(self, size: Tuple[float, float]):
        """创建原生视图"""
        self._size = size
        self._is_created = True
        self._is_visible = True

    def destroy(self):
        """销毁原生视图"""
        self._is_created = False
        self._is_visible = False

    def set_visibility(self, visible: bool):
        """设置可见性"""
        self._is_visible = visible

    def set_z_order(self, z_order: int):
        """设置 z-order（控制视图层级）"""
        self._z_order = z_order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self._platform.value,
            "view_id": self._view_id,
            "created": self._is_created,
            "visible": self._is_visible,
            "size": self._size,
            "z_order": self._z_order,
        }


# ============================================================
# 平台通道管理器 (PlatformChannelManager)
# ============================================================
class PlatformChannelManager:
    """
    平台通道管理器

    管理所有 Platform Channel，提供统一的通道注册和查找接口。
    模拟 Flutter 的 PlatformDispatcher 角色。
    """

    def __init__(self, platform: PlatformType = PlatformType.ANDROID):
        self._platform = platform
        self._method_channels: Dict[str, MethodChannel] = {}
        self._event_channels: Dict[str, EventChannel] = {}
        self._message_channels: Dict[str, BasicMessageChannel] = {}

    def register_method_channel(self, name: str) -> MethodChannel:
        """注册方法通道"""
        channel = MethodChannel(name, self._platform)
        self._method_channels[name] = channel
        return channel

    def register_event_channel(self, name: str) -> EventChannel:
        """注册事件通道"""
        channel = EventChannel(name, self._platform)
        self._event_channels[name] = channel
        return channel

    def register_message_channel(self, name: str) -> BasicMessageChannel:
        """注册消息通道"""
        channel = BasicMessageChannel(name, self._platform)
        self._message_channels[name] = channel
        return channel

    def get_method_channel(self, name: str) -> Optional[MethodChannel]:
        return self._method_channels.get(name)

    def get_event_channel(self, name: str) -> Optional[EventChannel]:
        return self._event_channels.get(name)

    def get_message_channel(self, name: str) -> Optional[BasicMessageChannel]:
        return self._message_channels.get(name)

    def create_platform_view(self, view_id: str = "default") -> PlatformView:
        """创建平台视图"""
        return PlatformView(self._platform, view_id)

    def get_summary(self) -> Dict[str, Any]:
        """获取所有通道摘要"""
        return {
            "platform": self._platform.value,
            "method_channels": {
                name: ch.to_dict() for name, ch in self._method_channels.items()
            },
            "event_channels": {
                name: ch.to_dict() for name, ch in self._event_channels.items()
            },
            "message_channels": {
                name: ch.to_dict() for name, ch in self._message_channels.items()
            },
        }
