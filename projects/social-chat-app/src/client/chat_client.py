"""
聊天客户端
用于连接WebSocket服务器
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
import websockets

logger = logging.getLogger(__name__)


class ChatClient:
    """聊天客户端类"""

    def __init__(self, server_url: str = 'ws://localhost:8765/ws'):
        self.server_url = server_url
        self.websocket = None
        self.token = None
        self.user_id = None
        self.username = None
        self._running = False
        self._handlers: Dict[str, List[Callable]] = {}
        self._heartbeat_task = None

    def on(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable = None):
        """移除事件处理器"""
        if event_type in self._handlers:
            if handler:
                self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]
            else:
                del self._handlers[event_type]

    async def _emit(self, event_type: str, data: Any = None):
        """触发事件"""
        for handler in self._handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"事件处理器错误: {e}")

    async def connect(self, token: str):
        """连接到服务器"""
        self.token = token
        url = f"{self.server_url}?token={token}"

        try:
            self.websocket = await websockets.connect(url)
            self._running = True

            # 启动心跳
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # 启动消息接收
            asyncio.create_task(self._receive_loop())

            await self._emit('connected')
            logger.info("已连接到服务器")
            return True

        except Exception as e:
            logger.error(f"连接失败: {e}")
            await self._emit('error', {'message': f'连接失败: {e}'})
            return False

    async def disconnect(self):
        """断开连接"""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        await self._emit('disconnected')
        logger.info("已断开连接")

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await asyncio.sleep(30)
                if self.websocket:
                    await self.send({'type': 'heartbeat'})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳错误: {e}")

    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for message in self.websocket:
                if not self._running:
                    break

                data = json.loads(message)
                msg_type = data.get('type')

                # 处理特定消息类型
                if msg_type == 'new_message':
                    await self._emit('message', data.get('message'))
                elif msg_type == 'user_online':
                    await self._emit('user_online', data)
                elif msg_type == 'user_offline':
                    await self._emit('user_offline', data)
                elif msg_type == 'typing':
                    await self._emit('typing', data)
                elif msg_type == 'read_receipt':
                    await self._emit('read_receipt', data)
                elif msg_type == 'friend_request':
                    await self._emit('friend_request', data)
                elif msg_type == 'message_history':
                    await self._emit('message_history', data)
                elif msg_type == 'search_results':
                    await self._emit('search_results', data)
                elif msg_type == 'online_users':
                    await self._emit('online_users', data)
                elif msg_type == 'friends_list':
                    await self._emit('friends_list', data)
                elif msg_type == 'error':
                    await self._emit('error', data)
                else:
                    await self._emit(msg_type, data)

        except websockets.exceptions.ConnectionClosed:
            logger.info("连接已关闭")
        except Exception as e:
            logger.error(f"接收消息错误: {e}")
        finally:
            if self._running:
                await self.disconnect()

    async def send(self, data: Dict[str, Any]):
        """发送消息"""
        if self.websocket:
            await self.websocket.send(json.dumps(data))

    # ==================== 业务方法 ====================

    async def send_message(self, content: str, receiver_id: int = None,
                          group_id: int = None, message_type: str = 'text',
                          file_url: str = None, file_name: str = None,
                          file_size: int = None):
        """发送消息"""
        await self.send({
            'type': 'send_message',
            'content': content,
            'receiver_id': receiver_id,
            'group_id': group_id,
            'message_type': message_type,
            'file_url': file_url,
            'file_name': file_name,
            'file_size': file_size
        })

    async def send_text(self, content: str, receiver_id: int = None, group_id: int = None):
        """发送文本消息"""
        await self.send_message(content, receiver_id, group_id)

    async def send_typing(self, receiver_id: int = None, group_id: int = None, is_typing: bool = True):
        """发送输入状态"""
        await self.send({
            'type': 'typing',
            'receiver_id': receiver_id,
            'group_id': group_id,
            'is_typing': is_typing
        })

    async def mark_read(self, sender_id: int):
        """标记消息为已读"""
        await self.send({
            'type': 'read_receipt',
            'sender_id': sender_id
        })

    async def get_friends(self):
        """获取好友列表"""
        await self.send({'type': 'get_friends'})

    async def send_friend_request(self, to_user_id: int, message: str = ''):
        """发送好友请求"""
        await self.send({
            'type': 'send_friend_request',
            'to_user_id': to_user_id,
            'message': message
        })

    async def accept_friend_request(self, request_id: int):
        """接受好友请求"""
        await self.send({
            'type': 'accept_friend_request',
            'request_id': request_id
        })

    async def reject_friend_request(self, request_id: int):
        """拒绝好友请求"""
        await self.send({
            'type': 'reject_friend_request',
            'request_id': request_id
        })

    async def create_group(self, name: str, description: str = ''):
        """创建群组"""
        await self.send({
            'type': 'create_group',
            'name': name,
            'description': description
        })

    async def join_group(self, group_id: int):
        """加入群组"""
        await self.send({
            'type': 'join_group',
            'group_id': group_id
        })

    async def leave_group(self, group_id: int):
        """离开群组"""
        await self.send({
            'type': 'leave_group',
            'group_id': group_id
        })

    async def get_messages(self, receiver_id: int = None, group_id: int = None,
                          limit: int = 50, before_id: int = None):
        """获取消息历史"""
        await self.send({
            'type': 'get_messages',
            'receiver_id': receiver_id,
            'group_id': group_id,
            'limit': limit,
            'before_id': before_id
        })

    async def search_messages(self, query: str):
        """搜索消息"""
        await self.send({
            'type': 'search_messages',
            'query': query
        })

    async def get_online_users(self):
        """获取在线用户"""
        await self.send({'type': 'get_online_users'})


class ChatClientCLI(ChatClient):
    """命令行聊天客户端"""

    def __init__(self, server_url: str = 'ws://localhost:8765/ws'):
        super().__init__(server_url)
        self._setup_handlers()

    def _setup_handlers(self):
        """设置事件处理器"""
        self.on('message', self._on_message)
        self.on('user_online', self._on_user_online)
        self.on('user_offline', self._on_user_offline)
        self.on('typing', self._on_typing)
        self.on('error', self._on_error)

    async def _on_message(self, message: Dict):
        """处理收到的消息"""
        sender = message.get('sender', {})
        content = message.get('content', '')
        print(f"\n[{sender.get('username', 'Unknown')}]: {content}")

    async def _on_user_online(self, data: Dict):
        """用户上线通知"""
        print(f"\n[系统] {data.get('username')} 已上线")

    async def _on_user_offline(self, data: Dict):
        """用户下线通知"""
        print(f"\n[系统] {data.get('username')} 已下线")

    async def _on_typing(self, data: Dict):
        """输入状态通知"""
        if data.get('is_typing'):
            print(f"\n[系统] 用户 {data.get('user_id')} 正在输入...")

    async def _on_error(self, data: Dict):
        """错误通知"""
        print(f"\n[错误] {data.get('message')}")
