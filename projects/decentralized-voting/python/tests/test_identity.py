"""
身份验证模块测试
"""

import pytest
import time
from src.identity import VoterRegistry, Voter, VoterStatus


class TestVoterRegistry:
    """选民注册表测试"""

    def setup_method(self):
        self.registry = VoterRegistry()

    def test_register_voter(self):
        voter = self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        assert voter.address == "0xVoter1"
        assert voter.name == "张三"
        assert voter.status == VoterStatus.REGISTERED

    def test_register_duplicate_voter(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )

        with pytest.raises(ValueError):
            self.registry.register_voter(
                address="0xVoter1",
                name="张三",
                email="zhangsan@example.com",
            )

    def test_verify_voter(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )

        result = self.registry.verify_voter("0xVoter1")
        assert result is True

        voter = self.registry.get_voter("0xVoter1")
        assert voter.status == VoterStatus.VERIFIED

    def test_verify_nonexistent_voter(self):
        result = self.registry.verify_voter("0xNonExistent")
        assert result is False

    def test_issue_credential(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")

        credential = self.registry.issue_credential("0xVoter1")
        assert credential.voter_address == "0xVoter1"
        assert credential.is_valid is True

    def test_issue_credential_unverified(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )

        with pytest.raises(ValueError):
            self.registry.issue_credential("0xVoter1")

    def test_validate_credential(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")
        self.registry.issue_credential("0xVoter1")

        assert self.registry.validate_credential("0xVoter1") is True

    def test_blacklist_voter(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")

        self.registry.add_to_blacklist("0xVoter1")

        voter = self.registry.get_voter("0xVoter1")
        assert voter.status == VoterStatus.REVOKED

    def test_blacklist_prevents_registration(self):
        self.registry.add_to_blacklist("0xVoter1")

        with pytest.raises(PermissionError):
            self.registry.register_voter(
                address="0xVoter1",
                name="张三",
                email="zhangsan@example.com",
            )

    def test_suspend_voter(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")
        self.registry.suspend_voter("0xVoter1", "违规行为")

        voter = self.registry.get_voter("0xVoter1")
        assert voter.status == VoterStatus.SUSPENDED

    def test_reactivate_voter(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")
        self.registry.suspend_voter("0xVoter1")
        self.registry.reactivate_voter("0xVoter1")

        voter = self.registry.get_voter("0xVoter1")
        assert voter.status == VoterStatus.VERIFIED

    def test_is_eligible(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")
        self.registry.issue_credential("0xVoter1")

        assert self.registry.is_eligible("0xVoter1") is True

    def test_is_eligible_blacklisted(self):
        self.registry.register_voter(
            address="0xVoter1",
            name="张三",
            email="zhangsan@example.com",
        )
        self.registry.verify_voter("0xVoter1")
        self.registry.add_to_blacklist("0xVoter1")

        assert self.registry.is_eligible("0xVoter1") is False

    def test_get_statistics(self):
        self.registry.register_voter("0xV1", "张三", "v1@example.com")
        self.registry.register_voter("0xV2", "李四", "v2@example.com")
        self.registry.verify_voter("0xV1")

        stats = self.registry.get_statistics()
        assert stats["total_voters"] == 2
        assert stats["verified"] == 1

    def test_whitelist_and_blacklist(self):
        self.registry.add_to_whitelist("0xVoter1")
        assert "0xVoter1" in self.registry.whitelist

        self.registry.add_to_blacklist("0xVoter1")
        assert "0xVoter1" in self.registry.blacklist
        assert "0xVoter1" not in self.registry.whitelist

    def test_get_all_voters(self):
        self.registry.register_voter("0xV1", "张三", "v1@example.com")
        self.registry.register_voter("0xV2", "李四", "v2@example.com")

        voters = self.registry.get_all_voters()
        assert len(voters) == 2

    def test_get_verified_voters(self):
        self.registry.register_voter("0xV1", "张三", "v1@example.com")
        self.registry.register_voter("0xV2", "李四", "v2@example.com")
        self.registry.verify_voter("0xV1")

        verified = self.registry.get_verified_voters()
        assert len(verified) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
