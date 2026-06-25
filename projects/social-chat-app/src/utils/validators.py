"""
数据验证工具
"""

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        return False, "邮箱不能为空"
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """验证密码强度"""
    if not password:
        return False, "密码不能为空"
    if len(password) < 6:
        return False, "密码长度不能少于6位"
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """验证用户名"""
    if not username:
        return False, "用户名不能为空"
    if len(username) < 3:
        return False, "用户名长度不能少于3位"
    if len(username) > 20:
        return False, "用户名长度不能超过20位"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    return True, ""


def validate_message_content(content: str, max_length: int = 5000) -> Tuple[bool, str]:
    """验证消息内容"""
    if not content:
        return False, "消息内容不能为空"
    if len(content) > max_length:
        return False, f"消息内容不能超过{max_length}个字符"
    return True, ""


def validate_group_name(name: str) -> Tuple[bool, str]:
    """验证群组名称"""
    if not name:
        return False, "群组名称不能为空"
    if len(name) > 50:
        return False, "群组名称不能超过50个字符"
    return True, ""
