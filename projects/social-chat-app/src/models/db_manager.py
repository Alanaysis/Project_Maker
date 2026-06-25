"""
数据库管理器
处理所有数据库操作
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from .database import Base, User, Group, Message, FriendRequest, OfflineMessage, MessageType, UserStatus, friendship_table, group_members_table


class DatabaseManager:
    """数据库管理类"""

    def __init__(self, db_path: str = "social_chat.db"):
        self.db_url = f"sqlite+aiosqlite:///{db_path}"
        self.engine = create_async_engine(self.db_url, echo=False)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db(self):
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()

    # ==================== 用户操作 ====================

    async def create_user(self, username: str, email: str, password_hash: str,
                         nickname: str = '', avatar_url: str = '', bio: str = '') -> User:
        """创建新用户"""
        async with self.async_session() as session:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                nickname=nickname or username,
                avatar_url=avatar_url,
                bio=bio
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()

    async def update_user_status(self, user_id: int, status: str) -> bool:
        """更新用户在线状态"""
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.status = status
                user.last_seen = datetime.utcnow()
                await session.commit()
                return True
            return False

    async def update_user_profile(self, user_id: int, **kwargs) -> bool:
        """更新用户资料"""
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                user.updated_at = datetime.utcnow()
                await session.commit()
                return True
            return False

    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """搜索用户"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(
                    or_(
                        User.username.ilike(f"%{query}%"),
                        User.nickname.ilike(f"%{query}%"),
                        User.email.ilike(f"%{query}%")
                    )
                ).limit(limit)
            )
            return list(result.scalars().all())

    # ==================== 好友操作 ====================

    async def send_friend_request(self, from_user_id: int, to_user_id: int, message: str = '') -> Optional[FriendRequest]:
        """发送好友请求"""
        async with self.async_session() as session:
            # 检查是否已存在请求
            existing = await session.execute(
                select(FriendRequest).where(
                    and_(
                        FriendRequest.from_user_id == from_user_id,
                        FriendRequest.to_user_id == to_user_id,
                        FriendRequest.status == 'pending'
                    )
                )
            )
            if existing.scalar_one_or_none():
                return None

            request = FriendRequest(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                message=message
            )
            session.add(request)
            await session.commit()
            await session.refresh(request)
            return request

    async def handle_friend_request(self, request_id: int, accept: bool) -> bool:
        """处理好友请求"""
        async with self.async_session() as session:
            request = await session.get(FriendRequest, request_id)
            if not request or request.status != 'pending':
                return False

            request.status = 'accepted' if accept else 'rejected'
            request.updated_at = datetime.utcnow()

            if accept:
                # 添加双向好友关系
                stmt1 = friendship_table.insert().values(
                    user_id=request.from_user_id,
                    friend_id=request.to_user_id,
                    status='accepted'
                )
                stmt2 = friendship_table.insert().values(
                    user_id=request.to_user_id,
                    friend_id=request.from_user_id,
                    status='accepted'
                )
                await session.execute(stmt1)
                await session.execute(stmt2)

            await session.commit()
            return True

    async def get_friends(self, user_id: int) -> List[User]:
        """获取好友列表"""
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                await session.refresh(user, ['friends'])
                return list(user.friends)
            return []

    async def get_friend_requests(self, user_id: int) -> List[FriendRequest]:
        """获取好友请求列表"""
        async with self.async_session() as session:
            result = await session.execute(
                select(FriendRequest).where(
                    and_(
                        FriendRequest.to_user_id == user_id,
                        FriendRequest.status == 'pending'
                    )
                ).options(selectinload(FriendRequest.from_user))
            )
            return list(result.scalars().all())

    async def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """删除好友"""
        async with self.async_session() as session:
            stmt1 = friendship_table.delete().where(
                and_(
                    friendship_table.c.user_id == user_id,
                    friendship_table.c.friend_id == friend_id
                )
            )
            stmt2 = friendship_table.delete().where(
                and_(
                    friendship_table.c.user_id == friend_id,
                    friendship_table.c.friend_id == user_id
                )
            )
            await session.execute(stmt1)
            await session.execute(stmt2)
            await session.commit()
            return True

    # ==================== 消息操作 ====================

    async def create_message(self, sender_id: int, content: str,
                           receiver_id: int = None, group_id: int = None,
                           message_type: str = MessageType.TEXT.value,
                           file_url: str = None, file_name: str = None,
                           file_size: int = None) -> Message:
        """创建消息"""
        async with self.async_session() as session:
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                group_id=group_id,
                message_type=message_type,
                content=content,
                file_url=file_url,
                file_name=file_name,
                file_size=file_size
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    async def get_private_messages(self, user1_id: int, user2_id: int,
                                  limit: int = 50, before_id: int = None) -> List[Message]:
        """获取私聊消息"""
        async with self.async_session() as session:
            query = select(Message).where(
                or_(
                    and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
                    and_(Message.sender_id == user2_id, Message.receiver_id == user1_id)
                )
            ).options(selectinload(Message.sender))

            if before_id:
                query = query.where(Message.id < before_id)

            query = query.order_by(desc(Message.created_at)).limit(limit)
            result = await session.execute(query)
            messages = list(result.scalars().all())
            messages.reverse()
            return messages

    async def get_group_messages(self, group_id: int, limit: int = 50,
                               before_id: int = None) -> List[Message]:
        """获取群聊消息"""
        async with self.async_session() as session:
            query = select(Message).where(
                Message.group_id == group_id
            ).options(selectinload(Message.sender))

            if before_id:
                query = query.where(Message.id < before_id)

            query = query.order_by(desc(Message.created_at)).limit(limit)
            result = await session.execute(query)
            messages = list(result.scalars().all())
            messages.reverse()
            return messages

    async def mark_messages_read(self, sender_id: int, receiver_id: int) -> int:
        """标记消息为已读"""
        async with self.async_session() as session:
            stmt = (
                Message.__table__.update()
                .where(
                    and_(
                        Message.sender_id == sender_id,
                        Message.receiver_id == receiver_id,
                        Message.is_read == False
                    )
                )
                .values(is_read=True)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def search_messages(self, user_id: int, query: str, limit: int = 50) -> List[Message]:
        """搜索消息"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Message).where(
                    and_(
                        Message.content.ilike(f"%{query}%"),
                        or_(
                            Message.sender_id == user_id,
                            Message.receiver_id == user_id,
                            Message.group_id.in_(
                                select(group_members_table.c.group_id).where(
                                    group_members_table.c.user_id == user_id
                                )
                            )
                        )
                    )
                ).options(selectinload(Message.sender))
                .order_by(desc(Message.created_at))
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_unread_count(self, user_id: int) -> Dict[int, int]:
        """获取未读消息数量"""
        async with self.async_session() as session:
            result = await session.execute(
                select(
                    Message.sender_id,
                    func.count(Message.id).label('count')
                ).where(
                    and_(
                        Message.receiver_id == user_id,
                        Message.is_read == False
                    )
                ).group_by(Message.sender_id)
            )
            return {row.sender_id: row.count for row in result}

    # ==================== 离线消息 ====================

    async def add_offline_message(self, user_id: int, message_id: int):
        """添加离线消息"""
        async with self.async_session() as session:
            offline_msg = OfflineMessage(user_id=user_id, message_id=message_id)
            session.add(offline_msg)
            await session.commit()

    async def get_offline_messages(self, user_id: int) -> List[Message]:
        """获取离线消息"""
        async with self.async_session() as session:
            result = await session.execute(
                select(OfflineMessage)
                .where(OfflineMessage.user_id == user_id)
                .options(selectinload(OfflineMessage.message).selectinload(Message.sender))
            )
            offline_messages = list(result.scalars().all())

            # 删除已读取的离线消息
            for om in offline_messages:
                await session.delete(om)
            await session.commit()

            return [om.message for om in offline_messages]

    # ==================== 群组操作 ====================

    async def create_group(self, name: str, owner_id: int,
                          description: str = '', avatar_url: str = '') -> Group:
        """创建群组"""
        async with self.async_session() as session:
            group = Group(
                name=name,
                owner_id=owner_id,
                description=description,
                avatar_url=avatar_url
            )
            session.add(group)
            await session.flush()

            # 添加创建者为管理员
            stmt = group_members_table.insert().values(
                user_id=owner_id,
                group_id=group.id,
                role='admin'
            )
            await session.execute(stmt)
            await session.commit()
            await session.refresh(group)
            return group

    async def add_group_member(self, group_id: int, user_id: int, role: str = 'member') -> bool:
        """添加群组成员"""
        async with self.async_session() as session:
            # 检查是否已是成员
            existing = await session.execute(
                select(group_members_table).where(
                    and_(
                        group_members_table.c.group_id == group_id,
                        group_members_table.c.user_id == user_id
                    )
                )
            )
            if existing.first():
                return False

            stmt = group_members_table.insert().values(
                user_id=user_id,
                group_id=group_id,
                role=role
            )
            await session.execute(stmt)
            await session.commit()
            return True

    async def remove_group_member(self, group_id: int, user_id: int) -> bool:
        """移除群组成员"""
        async with self.async_session() as session:
            stmt = group_members_table.delete().where(
                and_(
                    group_members_table.c.group_id == group_id,
                    group_members_table.c.user_id == user_id
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """获取群组成员"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User, group_members_table.c.role)
                .join(group_members_table, User.id == group_members_table.c.user_id)
                .where(group_members_table.c.group_id == group_id)
            )
            members = []
            for user, role in result:
                user_dict = user.to_dict()
                user_dict['role'] = role
                members.append(user_dict)
            return members

    async def get_user_groups(self, user_id: int) -> List[Group]:
        """获取用户加入的群组"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Group)
                .join(group_members_table, Group.id == group_members_table.c.group_id)
                .where(group_members_table.c.user_id == user_id)
            )
            return list(result.scalars().all())
