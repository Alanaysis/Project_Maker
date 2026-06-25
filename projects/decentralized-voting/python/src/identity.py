"""
身份验证模块
实现选民注册、投票权验证和身份管理
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any


class VoterStatus(Enum):
    """选民状态枚举"""
    REGISTERED = "registered"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class Voter:
    """选民数据结构"""
    address: str
    name: str
    email: str
    registration_time: float = field(default_factory=time.time)
    status: VoterStatus = VoterStatus.REGISTERED
    voting_power: int = 1  # 默认一人一票
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "name": self.name,
            "email": self.email,
            "registration_time": self.registration_time,
            "status": self.status.value,
            "voting_power": self.voting_power,
        }


@dataclass
class VoterCredential:
    """选民凭证"""
    voter_address: str
    credential_hash: str
    issued_at: float = field(default_factory=time.time)
    expires_at: float = 0
    is_valid: bool = True


class VoterRegistry:
    """选民注册表"""

    def __init__(self):
        self.voters: Dict[str, Voter] = {}
        self.credentials: Dict[str, VoterCredential] = {}
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.registration_events: List[Dict[str, Any]] = []

    def register_voter(
        self,
        address: str,
        name: str,
        email: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Voter:
        """
        注册选民

        Args:
            address: 选民地址
            name: 选民姓名
            email: 选民邮箱
            metadata: 额外元数据

        Returns:
            注册的选民对象
        """
        if address in self.voters:
            raise ValueError(f"选民 {address} 已注册")

        if address in self.blacklist:
            raise PermissionError(f"选民 {address} 已被列入黑名单")

        voter = Voter(
            address=address,
            name=name,
            email=email,
            metadata=metadata or {},
        )

        self.voters[address] = voter

        self.registration_events.append({
            "action": "register",
            "address": address,
            "name": name,
            "timestamp": time.time(),
        })

        return voter

    def verify_voter(self, address: str) -> bool:
        """
        验证选民身份

        Args:
            address: 选民地址

        Returns:
            验证是否成功
        """
        if address not in self.voters:
            return False

        voter = self.voters[address]

        if address in self.blacklist:
            return False

        voter.status = VoterStatus.VERIFIED

        self.registration_events.append({
            "action": "verify",
            "address": address,
            "timestamp": time.time(),
        })

        return True

    def issue_credential(
        self,
        address: str,
        validity_duration: float = 86400,  # 默认24小时
    ) -> VoterCredential:
        """
        发行选民凭证

        Args:
            address: 选民地址
            validity_duration: 凭证有效期（秒）

        Returns:
            选民凭证
        """
        if address not in self.voters:
            raise ValueError(f"选民 {address} 未注册")

        voter = self.voters[address]

        if voter.status != VoterStatus.VERIFIED:
            raise ValueError(f"选民 {address} 未验证")

        if address in self.blacklist:
            raise PermissionError(f"选民 {address} 已被列入黑名单")

        # 生成凭证哈希
        credential_data = f"{address}:{voter.name}:{time.time()}"
        credential_hash = hashlib.sha256(credential_data.encode()).hexdigest()

        credential = VoterCredential(
            voter_address=address,
            credential_hash=credential_hash,
            expires_at=time.time() + validity_duration,
        )

        self.credentials[address] = credential

        return credential

    def validate_credential(self, address: str) -> bool:
        """
        验证选民凭证

        Args:
            address: 选民地址

        Returns:
            凭证是否有效
        """
        if address not in self.credentials:
            return False

        credential = self.credentials[address]

        if not credential.is_valid:
            return False

        if time.time() > credential.expires_at:
            credential.is_valid = False
            return False

        return True

    def add_to_whitelist(self, address: str) -> None:
        """添加到白名单"""
        self.whitelist.add(address)
        if address in self.blacklist:
            self.blacklist.remove(address)

    def remove_from_whitelist(self, address: str) -> None:
        """从白名单移除"""
        self.whitelist.discard(address)

    def add_to_blacklist(self, address: str) -> None:
        """添加到黑名单"""
        self.blacklist.add(address)
        if address in self.whitelist:
            self.whitelist.remove(address)

        # 吊销凭证
        if address in self.credentials:
            self.credentials[address].is_valid = False

        # 更新选民状态
        if address in self.voters:
            self.voters[address].status = VoterStatus.REVOKED

    def remove_from_blacklist(self, address: str) -> None:
        """从黑名单移除"""
        self.blacklist.discard(address)

    def suspend_voter(self, address: str, reason: str = "") -> None:
        """暂停选民"""
        if address not in self.voters:
            raise ValueError(f"选民 {address} 未注册")

        self.voters[address].status = VoterStatus.SUSPENDED

        self.registration_events.append({
            "action": "suspend",
            "address": address,
            "reason": reason,
            "timestamp": time.time(),
        })

    def reactivate_voter(self, address: str) -> None:
        """重新激活选民"""
        if address not in self.voters:
            raise ValueError(f"选民 {address} 未注册")

        voter = self.voters[address]
        if voter.status == VoterStatus.SUSPENDED:
            voter.status = VoterStatus.VERIFIED

    def get_voter(self, address: str) -> Optional[Voter]:
        """获取选民信息"""
        return self.voters.get(address)

    def get_all_voters(self) -> List[Voter]:
        """获取所有选民"""
        return list(self.voters.values())

    def get_verified_voters(self) -> List[Voter]:
        """获取所有已验证选民"""
        return [
            voter for voter in self.voters.values()
            if voter.status == VoterStatus.VERIFIED
        ]

    def is_eligible(self, address: str) -> bool:
        """
        检查选民是否有投票资格

        Args:
            address: 选民地址

        Returns:
            是否有投票资格
        """
        if address not in self.voters:
            return False

        if address in self.blacklist:
            return False

        voter = self.voters[address]

        if voter.status != VoterStatus.VERIFIED:
            return False

        if not self.validate_credential(address):
            return False

        return True

    def get_registration_events(self) -> List[Dict[str, Any]]:
        """获取注册事件"""
        return self.registration_events.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取注册统计"""
        total = len(self.voters)
        verified = sum(
            1 for v in self.voters.values()
            if v.status == VoterStatus.VERIFIED
        )
        suspended = sum(
            1 for v in self.voters.values()
            if v.status == VoterStatus.SUSPENDED
        )
        revoked = sum(
            1 for v in self.voters.values()
            if v.status == VoterStatus.REVOKED
        )

        return {
            "total_voters": total,
            "verified": verified,
            "registered": total - verified - suspended - revoked,
            "suspended": suspended,
            "revoked": revoked,
            "whitelist_size": len(self.whitelist),
            "blacklist_size": len(self.blacklist),
        }
