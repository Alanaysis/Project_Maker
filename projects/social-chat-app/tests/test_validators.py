"""
验证器测试
"""

import pytest
from src.utils.validators import (
    validate_email,
    validate_password,
    validate_username,
    validate_message_content,
    validate_group_name
)


class TestValidators:
    """验证器测试类"""

    def test_validate_email(self):
        """测试邮箱验证"""
        # 有效邮箱
        valid, msg = validate_email('test@example.com')
        assert valid is True

        valid, msg = validate_email('user.name@domain.co.uk')
        assert valid is True

        # 无效邮箱
        valid, msg = validate_email('')
        assert valid is False

        valid, msg = validate_email('invalid-email')
        assert valid is False

        valid, msg = validate_email('@domain.com')
        assert valid is False

    def test_validate_password(self):
        """测试密码验证"""
        # 有效密码
        valid, msg = validate_password('password123')
        assert valid is True

        valid, msg = validate_password('123456')
        assert valid is True

        # 无效密码
        valid, msg = validate_password('')
        assert valid is False

        valid, msg = validate_password('12345')
        assert valid is False

        valid, msg = validate_password('a' * 51)
        assert valid is False

    def test_validate_username(self):
        """测试用户名验证"""
        # 有效用户名
        valid, msg = validate_username('testuser')
        assert valid is True

        valid, msg = validate_username('user_123')
        assert valid is True

        # 无效用户名
        valid, msg = validate_username('')
        assert valid is False

        valid, msg = validate_username('ab')
        assert valid is False

        valid, msg = validate_username('a' * 21)
        assert valid is False

        valid, msg = validate_username('user@name')
        assert valid is False

    def test_validate_message_content(self):
        """测试消息内容验证"""
        # 有效内容
        valid, msg = validate_message_content('Hello')
        assert valid is True

        # 无效内容
        valid, msg = validate_message_content('')
        assert valid is False

        valid, msg = validate_message_content('a' * 5001)
        assert valid is False

    def test_validate_group_name(self):
        """测试群组名称验证"""
        # 有效名称
        valid, msg = validate_group_name('Test Group')
        assert valid is True

        # 无效名称
        valid, msg = validate_group_name('')
        assert valid is False

        valid, msg = validate_group_name('a' * 51)
        assert valid is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
