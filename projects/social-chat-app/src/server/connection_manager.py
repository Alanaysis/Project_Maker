"""
连接管理器
管理所有WebSocket连接
"""

import asyncio
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import websockets


@dataclass
class ConnectionInfo:
    """连接信息"""
    user_id: int
    username: str
    websocket: Any
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 用户ID -> 连接信息
        self._connections: Dict[int, ConnectionInfo] = {}
        # 群组ID -> 用户ID集合
        self._group_members: Dict[int, Set[int]] = {}
        # 锁
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, username: str, websocket: Any):
        """添加连接"""
        async with self._lock:
            # 如果用户已连接，断开旧连接
            if user_id in self._connections:
                old_conn = self._connections[user_id]
                try:
                    await old_conn.websocket.close(1000, "New connection established")
                except Exception:
                    pass

            self._connections[user_id] = ConnectionInfo(
                user_id=user_id,
                username=username,
                websocket=websocket
            )

    async def disconnect(self, user_id: int):
        """移除连接"""
        async with self._lock:
            if user_id in self._connections:
                del self._connections[user_id]

    def is_connected(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self._connections

    def get_connection(self, user_id: int) -> Optional[ConnectionInfo]:
        """获取用户连接信息"""
        return self._connections.get(user_id)

    def get_online_users(self) -> list:
        """获取所有在线用户"""
        return [
            {
                'user_id': info.user_id,
                'username': info.username,
                'connected_at': info.connected_at.isoformat()
            }
            for info in self._connections.values()
        ]

    def get_online_count(self) -> int:
        """获取在线用户数量"""
        return len(self._connections)

    async def send_to_user(self, user_id: int, message: dict) -> bool:
        """向单个用户发送消息"""
        conn = self._connections.get(user_id)
        if conn:
            try:
                await conn.websocket.send_json(message)
                return True
            except Exception:
                await self.disconnect(user_id)
                return False
        return False

    async def send_to_users(self, user_ids: list, message: dict) -> Dict[int, bool]:
        """向多个用户发送消息"""
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.send_to_user(user_id, message)
        return results

    async def broadcast(self, message: dict, exclude_user_id: int = None):
        """广播消息给所有在线用户"""
        disconnected = []
        for user_id, conn in self._connections.items():
            if user_id == exclude_user_id:
                continue
            try:
                await conn.websocket.send_json(message)
            except Exception:
                disconnected.append(user_id)

        # 清理断开的连接
        for user_id in disconnected:
            await self.disconnect(user_id)

    async def join_group(self, group_id: int, user_id: int):
        """用户加入群组"""
        async with self._lock:
            if group_id not in self._group_members:
                self._group_members[group_id] = set()
            self._group_members[group_id].add(user_id)

    async def leave_group(self, group_id: int, user_id: int):
        """用户离开群组"""
        async with self._lock:
            if group_id in self._group_members:
                self._group_members[group_id].discard(user_id)
                if not self._group_members[group_id]:
                    del self._group_members[group_id]

    async def send_to_group(self, group_id: int, message: dict, exclude_user_id: int = None) -> int:
        """向群组发送消息"""
        if group_id not in self._group_members:
            return 0

        sent_count = 0
        disconnected = []

        for user_id in self._group_members[group_id]:
            if user_id == exclude_user_id:
                continue
            if await self.send_to_user(user_id, message):
                sent_count += 1

        return sent_count

    def update_heartbeat(self, user_id: int):
        """更新心跳时间"""
        if user_id in self._connections:
            self._connections[user_id].last_heartbeat = datetime.utcnow()

    async def cleanup_stale_connections(self, timeout_seconds: int = 300):
        """清理超时连接"""
        now = datetime.utcnow()
        stale_users = []

        for user_id, conn in self._connections.items():
            if (now - conn.last_heartbeat).total_seconds() > timeout_seconds:
                stale_users.append(user_id)

        for user_id in stale_users:
            await self.disconnect(user_id)

        return len(stale_users)
