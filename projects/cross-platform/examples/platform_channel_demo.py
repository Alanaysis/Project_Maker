"""
示例 2: 平台通道演示
演示 Flutter 与原生平台之间的通信

跨平台原理：
Flutter 使用 Platform Channel 与原生平台通信。
MethodChannel 用于方法调用，EventChannel 用于事件流，
BasicMessageChannel 用于双向消息传递。

通信流程：
Dart (MethodChannel) → StandardCodec → Platform Channel → Native Code
Native Code → StandardCodec → Platform Channel → Dart (MethodChannel)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.platform_channel import (
    MethodChannel, EventChannel, BasicMessageChannel,
    PlatformChannelManager, PlatformType, StandardCodec
)
from src.dart_vm import DartVM


def demo():
    """平台通道演示"""
    print("=" * 60)
    print("平台通道 (Platform Channel) 演示")
    print("Platform Channel Demo")
    print("=" * 60)

    # 1. 创建平台通道管理器
    print("\n1. 初始化平台通道管理器")
    print("-" * 40)
    manager = PlatformChannelManager(PlatformType.ANDROID)
    print(f"平台类型: {manager._platform.value}")

    # 2. 注册方法通道
    print("\n2. 注册方法通道")
    print("-" * 40)

    device_channel = manager.register_method_channel("app/device")
    info_channel = manager.register_method_channel("app/info")

    # 注册原生端处理器
    def handle_get_device_info(encoded_args):
        return {
            "platform": "android",
            "version": "14",
            "model": "Pixel 7",
            "api_level": 34,
        }

    def handle_get_battery_level(encoded_args):
        return {"level": 85, "charging": False}

    def handle_open_url(encoded_args):
        return {"success": True, "url": "https://example.com"}

    device_channel.register_handler("getDeviceInfo", handle_get_device_info)
    device_channel.register_handler("getBatteryLevel", handle_get_battery_level)
    info_channel.register_handler("openURL", handle_open_url)

    print(f"已注册通道: {list(manager._method_channels.keys())}")

    # 3. 调用方法
    print("\n3. 调用原生方法 (Dart → Native)")
    print("-" * 40)

    result1 = device_channel.invoke("getDeviceInfo")
    print(f"getDeviceInfo: {result1}")

    result2 = device_channel.invoke("getBatteryLevel")
    print(f"getBatteryLevel: {result2}")

    result3 = info_channel.invoke("openURL", {"url": "https://flutter.dev"})
    print(f"openURL: {result3}")

    # 4. 查看编解码器统计
    print("\n4. 编解码器统计")
    print("-" * 40)
    codec_stats = device_channel._codec.stats
    print(f"编码次数: {codec_stats['encode_count']}")
    print(f"解码次数: {codec_stats['decode_count']}")

    # 5. 事件通道演示
    print("\n5. 事件通道 (EventChannel)")
    print("-" * 40)

    location_channel = manager.register_event_channel("app/location")

    received_events = []
    def location_listener(event_data, error):
        if error:
            received_events.append(f"错误: {error}")
        else:
            received_events.append(f"位置: {event_data}")

    location_channel.add_listener(location_listener)

    # 模拟原生端发出位置事件
    location_channel.emit_event({"lat": 39.9, "lng": 116.4})
    location_channel.emit_event({"lat": 31.2, "lng": 121.5})
    location_channel.emit_event({"lat": 23.1, "lng": 113.3})

    print(f"收到事件: {received_events}")
    print(f"事件总数: {len(location_channel.get_event_log())}")

    # 6. 消息通道演示
    print("\n6. 消息通道 (BasicMessageChannel)")
    print("-" * 40)

    msg_channel = manager.register_message_channel("app/messages")

    def msg_handler(msg):
        return {"echo": msg, "received": True}

    msg_channel.register_handler(msg_handler)
    msg_channel.send({"type": "ping", "data": "hello"})
    msg_channel.send({"type": "data", "data": {"key": "value"}})

    print(f"发送消息数: {len(msg_channel.get_message_queue())}")
    for item in msg_channel.get_message_queue():
        print(f"  消息: {item['message']}")

    # 7. 平台通道管理器摘要
    print("\n7. 通道管理器摘要")
    print("-" * 40)
    summary = manager.get_summary()
    print(f"平台: {summary['platform']}")
    print(f"方法通道: {list(summary['method_channels'].keys())}")
    print(f"事件通道: {list(summary['event_channels'].keys())}")
    print(f"消息通道: {list(summary['message_channels'].keys())}")

    # 8. 与 Dart VM 集成
    print("\n8. 与 Dart VM 集成")
    print("-" * 40)
    vm = DartVM()
    vm.set_platform_channel(device_channel)
    vm.set_global("deviceChannel", device_channel)

    # 模拟 Dart 代码调用
    vm.set_global("result", device_channel.invoke("getDeviceInfo"))
    print(f"Dart VM 中获取的设备信息: {vm.get_global('result')}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("Key concept: Platform Channel 是 Flutter 与原生平台通信的桥梁。")
    print("=" * 60)


if __name__ == "__main__":
    demo()
