"""
WebSocket 服务器
处理所有WebSocket连接和消息
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import websockets
from aiohttp import web

from ..models import DatabaseManager, MessageType, UserStatus
from ..utils import AuthService
from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket服务器"""

    def __init__(self, host: str = '0.0.0.0', port: int = 8765, db_path: str = 'social_chat.db'):
        self.host = host
        self.port = port
        self.db = DatabaseManager(db_path)
        self.auth = AuthService()
        self.connections = ConnectionManager()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """设置HTTP路由"""
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_post('/api/register', self.handle_register)
        self.app.router.add_post('/api/login', self.handle_login)
        self.app.router.add_get('/api/users/search', self.handle_search_users)
        self.app.router.add_static('/static/', path='static', name='static')

    async def start(self):
        """启动服务器"""
        await self.db.init_db()
        logger.info(f"服务器启动在 {self.host}:{self.port}")

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        # 启动心跳检查
        asyncio.create_task(self._heartbeat_checker())

        # 保持运行
        await asyncio.Event().wait()

    async def _heartbeat_checker(self):
        """定期检查心跳"""
        while True:
            await asyncio.sleep(60)
            cleaned = await self.connections.cleanup_stale_connections()
            if cleaned > 0:
                logger.info(f"清理了 {cleaned} 个超时连接")

    # ==================== HTTP处理器 ====================

    async def handle_register(self, request: web.Request) -> web.Response:
        """处理用户注册"""
        try:
            data = await request.json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            nickname = data.get('nickname', '').strip()

            # 验证输入
            from ..utils import validate_username, validate_email, validate_password

            valid, msg = validate_username(username)
            if not valid:
                return web.json_response({'error': msg}, status=400)

            valid, msg = validate_email(email)
            if not valid:
                return web.json_response({'error': msg}, status=400)

            valid, msg = validate_password(password)
            if not valid:
                return web.json_response({'error': msg}, status=400)

            # 检查用户名是否已存在
            existing = await self.db.get_user_by_username(username)
            if existing:
                return web.json_response({'error': '用户名已存在'}, status=400)

            # 检查邮箱是否已存在
            existing = await self.db.get_user_by_email(email)
            if existing:
                return web.json_response({'error': '邮箱已被注册'}, status=400)

            # 创建用户
            password_hash = self.auth.hash_password(password)
            user = await self.db.create_user(
                username=username,
                email=email,
                password_hash=password_hash,
                nickname=nickname
            )

            # 生成令牌
            token = self.auth.generate_token(user.id, user.username)

            return web.json_response({
                'message': '注册成功',
                'user': user.to_dict(),
                'token': token
            })

        except Exception as e:
            logger.error(f"注册失败: {e}")
            return web.json_response({'error': '注册失败'}, status=500)

    async def handle_login(self, request: web.Request) -> web.Response:
        """处理用户登录"""
        try:
            data = await request.json()
            username = data.get('username', '').strip()
            password = data.get('password', '')

            if not username or not password:
                return web.json_response({'error': '用户名和密码不能为空'}, status=400)

            # 查找用户
            user = await self.db.get_user_by_username(username)
            if not user:
                return web.json_response({'error': '用户名或密码错误'}, status=401)

            # 验证密码
            if not self.auth.verify_password(password, user.password_hash):
                return web.json_response({'error': '用户名或密码错误'}, status=401)

            # 生成令牌
            token = self.auth.generate_token(user.id, user.username)

            return web.json_response({
                'message': '登录成功',
                'user': user.to_dict(),
                'token': token
            })

        except Exception as e:
            logger.error(f"登录失败: {e}")
            return web.json_response({'error': '登录失败'}, status=500)

    async def handle_search_users(self, request: web.Request) -> web.Response:
        """搜索用户"""
        try:
            # 验证令牌
            token = self.auth.extract_token_from_header(request.headers.get('Authorization'))
            if not token:
                return web.json_response({'error': '未授权'}, status=401)

            payload = self.auth.verify_token(token)
            if not payload:
                return web.json_response({'error': '令牌无效或已过期'}, status=401)

            query = request.query.get('q', '').strip()
            if not query:
                return web.json_response({'users': []})

            users = await self.db.search_users(query)
            return web.json_response({
                'users': [u.to_dict() for u in users]
            })

        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            return web.json_response({'error': '搜索失败'}, status=500)

    # ==================== WebSocket处理器 ====================

    async def handle_websocket(self, request: web.Request):
        """处理WebSocket连接"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # 获取令牌
        token = request.query.get('token')
        if not token:
            await ws.send_json({'type': 'error', 'message': '缺少认证令牌'})
            await ws.close()
            return ws

        # 验证令牌
        payload = self.auth.verify_token(token)
        if not payload:
            await ws.send_json({'type': 'error', 'message': '令牌无效或已过期'})
            await ws.close()
            return ws

        user_id = payload['user_id']
        username = payload['username']

        # 注册连接
        await self.connections.connect(user_id, username, ws)
        await self.db.update_user_status(user_id, UserStatus.ONLINE.value)

        # 通知其他用户
        await self.connections.broadcast({
            'type': 'user_online',
            'user_id': user_id,
            'username': username
        }, exclude_user_id=user_id)

        # 发送离线消息
        offline_messages = await self.db.get_offline_messages(user_id)
        for msg in offline_messages:
            await ws.send_json({
                'type': 'new_message',
                'message': msg.to_dict()
            })

        logger.info(f"用户 {username} ({user_id}) 已连接")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self._handle_message(user_id, json.loads(msg.data))
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket错误: {ws.exception()}")
        finally:
            # 断开连接
            await self.connections.disconnect(user_id)
            await self.db.update_user_status(user_id, UserStatus.OFFLINE.value)

            # 通知其他用户
            await self.connections.broadcast({
                'type': 'user_offline',
                'user_id': user_id,
                'username': username
            }, exclude_user_id=user_id)

            logger.info(f"用户 {username} ({user_id}) 已断开连接")

        return ws

    async def _handle_message(self, user_id: int, data: Dict[str, Any]):
        """处理WebSocket消息"""
        msg_type = data.get('type')

        handlers = {
            'send_message': self._handle_send_message,
            'typing': self._handle_typing,
            'read_receipt': self._handle_read_receipt,
            'heartbeat': self._handle_heartbeat,
            'join_group': self._handle_join_group,
            'leave_group': self._handle_leave_group,
            'get_online_users': self._handle_get_online_users,
            'get_friends': self._handle_get_friends,
            'send_friend_request': self._handle_send_friend_request,
            'accept_friend_request': self._handle_accept_friend_request,
            'reject_friend_request': self._handle_reject_friend_request,
            'create_group': self._handle_create_group,
            'get_messages': self._handle_get_messages,
            'search_messages': self._handle_search_messages,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(user_id, data)
        else:
            await self.connections.send_to_user(user_id, {
                'type': 'error',
                'message': f'未知消息类型: {msg_type}'
            })

    async def _handle_send_message(self, user_id: int, data: Dict[str, Any]):
        """发送消息"""
        receiver_id = data.get('receiver_id')
        group_id = data.get('group_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', MessageType.TEXT.value)
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        file_size = data.get('file_size')

        if not content and message_type == MessageType.TEXT.value:
            await self.connections.send_to_user(user_id, {
                'type': 'error',
                'message': '消息内容不能为空'
            })
            return

        # 创建消息
        message = await self.db.create_message(
            sender_id=user_id,
            content=content,
            receiver_id=receiver_id,
            group_id=group_id,
            message_type=message_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size
        )

        message_data = {
            'type': 'new_message',
            'message': message.to_dict()
        }

        if group_id:
            # 群聊消息
            await self.connections.send_to_group(group_id, message_data, exclude_user_id=user_id)
        elif receiver_id:
            # 私聊消息
            sent = await self.connections.send_to_user(receiver_id, message_data)
            if not sent:
                # 用户离线，存储离线消息
                await self.db.add_offline_message(receiver_id, message.id)

            # 发送确认给发送者
            await self.connections.send_to_user(user_id, {
                'type': 'message_sent',
                'message': message.to_dict()
            })

    async def _handle_typing(self, user_id: int, data: Dict[str, Any]):
        """处理输入状态"""
        receiver_id = data.get('receiver_id')
        group_id = data.get('group_id')

        typing_data = {
            'type': 'typing',
            'user_id': user_id,
            'is_typing': data.get('is_typing', True)
        }

        if group_id:
            await self.connections.send_to_group(group_id, typing_data, exclude_user_id=user_id)
        elif receiver_id:
            await self.connections.send_to_user(receiver_id, typing_data)

    async def _handle_read_receipt(self, user_id: int, data: Dict[str, Any]):
        """处理已读回执"""
        sender_id = data.get('sender_id')
        if sender_id:
            count = await self.db.mark_messages_read(sender_id, user_id)
            await self.connections.send_to_user(sender_id, {
                'type': 'read_receipt',
                'reader_id': user_id,
                'count': count
            })

    async def _handle_heartbeat(self, user_id: int, data: Dict[str, Any]):
        """处理心跳"""
        self.connections.update_heartbeat(user_id)
        await self.connections.send_to_user(user_id, {
            'type': 'heartbeat_ack',
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _handle_join_group(self, user_id: int, data: Dict[str, Any]):
        """加入群组"""
        group_id = data.get('group_id')
        if not group_id:
            return

        # 检查是否是群组成员
        members = await self.db.get_group_members(group_id)
        member_ids = [m['id'] for m in members]

        if user_id in member_ids:
            await self.connections.join_group(group_id, user_id)
            await self.connections.send_to_user(user_id, {
                'type': 'group_joined',
                'group_id': group_id
            })

    async def _handle_leave_group(self, user_id: int, data: Dict[str, Any]):
        """离开群组"""
        group_id = data.get('group_id')
        if group_id:
            await self.connections.leave_group(group_id, user_id)
            await self.connections.send_to_user(user_id, {
                'type': 'group_left',
                'group_id': group_id
            })

    async def _handle_get_online_users(self, user_id: int, data: Dict[str, Any]):
        """获取在线用户"""
        online_users = self.connections.get_online_users()
        await self.connections.send_to_user(user_id, {
            'type': 'online_users',
            'users': online_users,
            'count': len(online_users)
        })

    async def _handle_get_friends(self, user_id: int, data: Dict[str, Any]):
        """获取好友列表"""
        friends = await self.db.get_friends(user_id)
        friends_data = []
        for friend in friends:
            friend_dict = friend.to_dict()
            friend_dict['is_online'] = self.connections.is_connected(friend.id)
            friends_data.append(friend_dict)

        await self.connections.send_to_user(user_id, {
            'type': 'friends_list',
            'friends': friends_data
        })

    async def _handle_send_friend_request(self, user_id: int, data: Dict[str, Any]):
        """发送好友请求"""
        to_user_id = data.get('to_user_id')
        message = data.get('message', '')

        if not to_user_id:
            return

        request = await self.db.send_friend_request(user_id, to_user_id, message)
        if request:
            # 通知目标用户
            await self.connections.send_to_user(to_user_id, {
                'type': 'friend_request',
                'request': {
                    'id': request.id,
                    'from_user': (await self.db.get_user_by_id(user_id)).to_dict(),
                    'message': message
                }
            })

            await self.connections.send_to_user(user_id, {
                'type': 'friend_request_sent',
                'request_id': request.id
            })
        else:
            await self.connections.send_to_user(user_id, {
                'type': 'error',
                'message': '好友请求已存在'
            })

    async def _handle_accept_friend_request(self, user_id: int, data: Dict[str, Any]):
        """接受好友请求"""
        request_id = data.get('request_id')
        if request_id:
            success = await self.db.handle_friend_request(request_id, accept=True)
            if success:
                await self.connections.send_to_user(user_id, {
                    'type': 'friend_request_accepted',
                    'request_id': request_id
                })

    async def _handle_reject_friend_request(self, user_id: int, data: Dict[str, Any]):
        """拒绝好友请求"""
        request_id = data.get('request_id')
        if request_id:
            success = await self.db.handle_friend_request(request_id, accept=False)
            if success:
                await self.connections.send_to_user(user_id, {
                    'type': 'friend_request_rejected',
                    'request_id': request_id
                })

    async def _handle_create_group(self, user_id: int, data: Dict[str, Any]):
        """创建群组"""
        name = data.get('name', '').strip()
        description = data.get('description', '')

        if not name:
            await self.connections.send_to_user(user_id, {
                'type': 'error',
                'message': '群组名称不能为空'
            })
            return

        group = await self.db.create_group(name, user_id, description)
        await self.connections.join_group(group.id, user_id)

        await self.connections.send_to_user(user_id, {
            'type': 'group_created',
            'group': group.to_dict()
        })

    async def _handle_get_messages(self, user_id: int, data: Dict[str, Any]):
        """获取消息历史"""
        receiver_id = data.get('receiver_id')
        group_id = data.get('group_id')
        limit = data.get('limit', 50)
        before_id = data.get('before_id')

        if group_id:
            messages = await self.db.get_group_messages(group_id, limit, before_id)
        elif receiver_id:
            messages = await self.db.get_private_messages(user_id, receiver_id, limit, before_id)
        else:
            messages = []

        await self.connections.send_to_user(user_id, {
            'type': 'message_history',
            'messages': [m.to_dict() for m in messages],
            'receiver_id': receiver_id,
            'group_id': group_id
        })

    async def _handle_search_messages(self, user_id: int, data: Dict[str, Any]):
        """搜索消息"""
        query = data.get('query', '').strip()
        if not query:
            return

        messages = await self.db.search_messages(user_id, query)
        await self.connections.send_to_user(user_id, {
            'type': 'search_results',
            'query': query,
            'messages': [m.to_dict() for m in messages]
        })
