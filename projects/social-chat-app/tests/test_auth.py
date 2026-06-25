"""
认证模块测试
"""

import pytest
from src.utils.auth import AuthService


class TestAuthService:
    """AuthService测试类"""

    def setup_method(self):
        """测试前准备"""
        self.auth = AuthService(secret_key='test-secret-key')

    def test_hash_password(self):
        """测试密码加密"""
        password = 'test123'
        hashed = self.auth.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self):
        """测试密码验证"""
        password = 'test123'
        hashed = self.auth.hash_password(password)

        assert self.auth.verify_password(password, hashed) is True
        assert self.auth.verify_password('wrong', hashed) is False

    def test_generate_token(self):
        """测试令牌生成"""
        token = self.auth.generate_token(1, 'testuser')

        assert token is not None
        assert len(token) > 0

    def test_verify_token(self):
        """测试令牌验证"""
        user_id = 1
        username = 'testuser'
        token = self.auth.generate_token(user_id, username)

        payload = self.auth.verify_token(token)

        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['username'] == username

    def test_invalid_token(self):
        """测试无效令牌"""
        payload = self.auth.verify_token('invalid-token')
        assert payload is None

    def test_extract_token_from_header(self):
        """测试从Header提取令牌"""
        token = 'test-token-123'

        # 有效的Authorization头
        header = f'Bearer {token}'
        assert self.auth.extract_token_from_header(header) == token

        # 无效的Authorization头
        assert self.auth.extract_token_from_header('Basic abc') is None
        assert self.auth.extract_token_from_header('') is None
        assert self.auth.extract_token_from_header(None) is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
