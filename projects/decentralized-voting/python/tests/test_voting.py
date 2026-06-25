"""
投票合约模块测试
"""

import pytest
import time
from src.voting import VotingContract, VoteStatus, Proposal, VoteSession


class TestVotingContract:
    """投票合约测试"""

    def setup_method(self):
        self.contract = VotingContract()
        self.creator = "0xCreator123"
        self.voter1 = "0xVoter1"
        self.voter2 = "0xVoter2"

    def test_create_vote_session(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )
        assert session_id == 0
        assert session_id in self.contract.vote_sessions

    def test_create_session_invalid_times(self):
        with pytest.raises(ValueError):
            self.contract.create_vote_session(
                title="测试投票",
                description="这是一个测试投票",
                start_time=time.time() + 3600,
                end_time=time.time(),
                creator=self.creator,
            )

    def test_add_proposal(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        proposal_id = self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )
        assert proposal_id == 0

        session = self.contract.get_session(session_id)
        assert len(session.proposals) == 1

    def test_add_proposal_not_creator(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        with pytest.raises(PermissionError):
            self.contract.add_proposal(
                session_id=session_id,
                name="提案A",
                description="提案A描述",
                caller=self.voter1,
            )

    def test_start_voting(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )

        self.contract.start_voting(session_id, self.creator)

        session = self.contract.get_session(session_id)
        assert session.status == VoteStatus.ACTIVE

    def test_vote(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )

        self.contract.start_voting(session_id, self.creator)

        self.contract.vote(
            session_id=session_id,
            proposal_id=0,
            voter_address=self.voter1,
        )

        assert self.contract.has_voted(session_id, self.voter1) is True

    def test_vote_twice(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )

        self.contract.start_voting(session_id, self.creator)

        self.contract.vote(
            session_id=session_id,
            proposal_id=0,
            voter_address=self.voter1,
        )

        with pytest.raises(ValueError):
            self.contract.vote(
                session_id=session_id,
                proposal_id=0,
                voter_address=self.voter1,
            )

    def test_end_voting(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )

        self.contract.start_voting(session_id, self.creator)

        self.contract.vote(
            session_id=session_id,
            proposal_id=0,
            voter_address=self.voter1,
        )

        self.contract.end_voting(session_id, self.creator)

        session = self.contract.get_session(session_id)
        assert session.status == VoteStatus.ENDED

    def test_get_results(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案B",
            description="提案B描述",
            caller=self.creator,
        )

        self.contract.start_voting(session_id, self.creator)

        self.contract.vote(session_id, 0, self.voter1)
        self.contract.vote(session_id, 1, self.voter2)

        results = self.contract.get_results(session_id)

        assert results["total_votes"] == 2
        assert len(results["proposals"]) == 2

    def test_get_voted_proposal(self):
        session_id = self.contract.create_vote_session(
            title="测试投票",
            description="这是一个测试投票",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        self.contract.add_proposal(
            session_id=session_id,
            name="提案A",
            description="提案A描述",
            caller=self.creator,
        )

        self.contract.start_voting(session_id, self.creator)

        self.contract.vote(session_id, 0, self.voter1)

        proposal_id = self.contract.get_voted_proposal(session_id, self.voter1)
        assert proposal_id == 0

    def test_multiple_sessions(self):
        session_id1 = self.contract.create_vote_session(
            title="投票1",
            description="投票1描述",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        session_id2 = self.contract.create_vote_session(
            title="投票2",
            description="投票2描述",
            start_time=time.time(),
            end_time=time.time() + 3600,
            creator=self.creator,
        )

        assert session_id1 == 0
        assert session_id2 == 1
        assert len(self.contract.get_all_sessions()) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
