"""
认证服务
处理用户认证、JWT令牌、密码加密等
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class AuthService:
    """认证服务类"""

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expire_hours = 24

    def hash_password(self, password: str) -> str:
        """加密密码"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def generate_token(self, user_id: int, username: str) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expire_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # 令牌已过期
        except jwt.InvalidTokenError:
            return None  # 无效令牌

    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """从Authorization头提取令牌"""
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
