"""
去中心化投票系统 - Python 实现
基于区块链技术的去中心化投票系统
"""

__version__ = "1.0.0"
__author__ = "Decentralized Voting Team"

from .blockchain import Block, Blockchain
from .voting import VotingContract, Proposal, VoteSession
from .identity import VoterRegistry, Voter
from .consensus import VotingRules, VoteResult
from .transparency import VoteLedger, AuditTrail

__all__ = [
    "Block",
    "Blockchain",
    "VotingContract",
    "Proposal",
    "VoteSession",
    "VoterRegistry",
    "Voter",
    "VotingRules",
    "VoteResult",
    "VoteLedger",
    "AuditTrail",
]
