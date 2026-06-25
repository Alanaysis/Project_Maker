"""
数据库模型定义
定义用户、消息、群组等核心数据模型
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table, Text, Enum
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# 好友关系多对多关联表
friendship_table = Table(
    'friendships',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('status', String(20), default='pending')  # pending, accepted, blocked
)

# 群组成员关联表
group_members_table = Table(
    'group_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('role', String(20), default='member'),  # admin, member
    Column('joined_at', DateTime, default=datetime.utcnow)
)


class MessageType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class UserStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class User(Base):
    """用户模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), default='')
    avatar_url = Column(String(500), default='')
    bio = Column(String(500), default='')
    status = Column(String(20), default=UserStatus.OFFLINE.value)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sent_messages = relationship('Message', back_populates='sender', foreign_keys='Message.sender_id')
    owned_groups = relationship('Group', back_populates='owner')
    friends = relationship(
        'User',
        secondary=friendship_table,
        primaryjoin=id == friendship_table.c.user_id,
        secondaryjoin=id == friendship_table.c.friend_id,
        backref='friend_of'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname or self.username,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Group(Base):
    """群组模型"""
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default='')
    avatar_url = Column(String(500), default='')
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    max_members = Column(Integer, default=500)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship('User', back_populates='owned_groups')
    members = relationship('User', secondary=group_members_table, backref='groups')
    messages = relationship('Message', back_populates='group')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'avatar_url': self.avatar_url,
            'owner_id': self.owner_id,
            'member_count': len(self.members),
            'max_members': self.max_members,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Message(Base):
    """消息模型"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 单聊接收者
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)    # 群聊ID
    message_type = Column(String(20), default=MessageType.TEXT.value)
    content = Column(Text, nullable=False)
    file_url = Column(String(500), nullable=True)   # 文件/图片URL
    file_name = Column(String(255), nullable=True)   # 文件名
    file_size = Column(Integer, nullable=True)       # 文件大小
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    sender = relationship('User', back_populates='sent_messages', foreign_keys=[sender_id])
    receiver = relationship('User', foreign_keys=[receiver_id])
    group = relationship('Group', back_populates='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'group_id': self.group_id,
            'message_type': self.message_type,
            'content': self.content,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sender': self.sender.to_dict() if self.sender else None
        }


class FriendRequest(Base):
    """好友请求模型"""
    __tablename__ = 'friend_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    to_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(String(200), default='')
    status = Column(String(20), default='pending')  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])


class OfflineMessage(Base):
    """离线消息队列"""
    __tablename__ = 'offline_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship('User')
    message = relationship('Message')
