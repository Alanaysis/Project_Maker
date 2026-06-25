"""
聊天客户端示例
演示如何使用ChatClient类
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client import ChatClient


async def main():
    """主函数"""
    # 创建客户端
    client = ChatClient('ws://localhost:8765/ws')

    # 注册事件处理器
    @client.on('connected')
    async def on_connected():
        print("已连接到服务器")

    @client.on('message')
    async def on_message(message):
        sender = message.get('sender', {})
        content = message.get('content', '')
        print(f"[{sender.get('username', '未知')}]: {content}")

    @client.on('user_online')
    async def on_user_online(data):
        print(f"[系统] {data.get('username')} 已上线")

    @client.on('user_offline')
    async def on_user_offline(data):
        print(f"[系统] {data.get('username')} 已下线")

    @client.on('error')
    async def on_error(data):
        print(f"[错误] {data.get('message')}")

    # 连接到服务器（需要先获取token）
    token = input("请输入认证令牌: ")
    connected = await client.connect(token)

    if not connected:
        print("连接失败")
        return

    # 获取好友列表
    await client.get_friends()

    # 简单的命令行交互
    print("\n命令:")
    print("  /msg <用户名> <消息> - 发送私聊消息")
    print("  /group <群组名> <消息> - 发送群聊消息")
    print("  /friends - 查看好友列表")
    print("  /online - 查看在线用户")
    print("  /quit - 退出")
    print()

    try:
        while True:
            line = input("> ")
            if not line:
                continue

            if line.startswith('/'):
                parts = line.split(' ', 2)
                cmd = parts[0].lower()

                if cmd == '/quit':
                    break
                elif cmd == '/friends':
                    await client.get_friends()
                elif cmd == '/online':
                    await client.get_online_users()
                elif cmd == '/msg' and len(parts) >= 3:
                    # 这里需要实现用户名到ID的转换
                    print("请使用用户ID发送消息")
                else:
                    print("未知命令")
            else:
                # 发送到当前聊天
                print("请使用 /msg 命令指定接收者")
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
