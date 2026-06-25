"""
投票规则模块测试
"""

import pytest
from src.consensus import (
    VotingEngine,
    VotingRules,
    VotingMethod,
    QuorumType,
    VoteResult,
    OnePersonOneVote,
)


class TestVotingRules:
    """投票规则测试"""

    def test_default_rules(self):
        rules = VotingRules()
        assert rules.voting_method == VotingMethod.SIMPLE_MAJORITY
        assert rules.quorum_type == QuorumType.NONE
        assert rules.majority_threshold == 0.5

    def test_custom_rules(self):
        rules = VotingRules(
            voting_method=VotingMethod.ABSOLUTE_MAJORITY,
            quorum_type=QuorumType.PERCENTAGE,
            quorum_value=0.5,
            majority_threshold=0.6,
        )
        assert rules.voting_method == VotingMethod.ABSOLUTE_MAJORITY
        assert rules.quorum_type == QuorumType.PERCENTAGE
        assert rules.quorum_value == 0.5

    def test_rules_to_dict(self):
        rules = VotingRules()
        rules_dict = rules.to_dict()
        assert "voting_method" in rules_dict
        assert "quorum_type" in rules_dict


class TestVotingEngine:
    """投票引擎测试"""

    def setup_method(self):
        self.engine = VotingEngine()

    def test_validate_vote_valid(self):
        is_valid, errors = self.engine.validate_vote(
            voter_address="0xVoter1",
            proposal_ids=[0],
            total_proposals=3,
            has_voted=False,
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_vote_already_voted(self):
        is_valid, errors = self.engine.validate_vote(
            voter_address="0xVoter1",
            proposal_ids=[0],
            total_proposals=3,
            has_voted=True,
        )
        assert is_valid is False
        assert "该选民已经投过票" in errors[0]

    def test_validate_vote_invalid_proposal(self):
        is_valid, errors = self.engine.validate_vote(
            voter_address="0xVoter1",
            proposal_ids=[5],
            total_proposals=3,
            has_voted=False,
        )
        assert is_valid is False

    def test_check_quorum_none(self):
        met, rate = self.engine.check_quorum(10, 100)
        assert met is True
        assert rate == 0.1

    def test_check_quorum_percentage(self):
        rules = VotingRules(
            quorum_type=QuorumType.PERCENTAGE,
            quorum_value=0.5,
        )
        engine = VotingEngine(rules)

        met, rate = engine.check_quorum(60, 100)
        assert met is True
        assert rate == 0.6

        met, rate = engine.check_quorum(40, 100)
        assert met is False
        assert rate == 0.4

    def test_check_quorum_absolute(self):
        rules = VotingRules(
            quorum_type=QuorumType.ABSOLUTE,
            quorum_value=50,
        )
        engine = VotingEngine(rules)

        met, rate = engine.check_quorum(60, 100)
        assert met is True

        met, rate = engine.check_quorum(40, 100)
        assert met is False

    def test_simple_majority(self):
        proposals = [
            {"id": 0, "name": "A", "votes": 60},
            {"id": 1, "name": "B", "votes": 40},
        ]

        winner = self.engine.determine_winner(proposals, 100)
        assert winner["name"] == "A"

    def test_absolute_majority(self):
        rules = VotingRules(voting_method=VotingMethod.ABSOLUTE_MAJORITY)
        engine = VotingEngine(rules)

        proposals = [
            {"id": 0, "name": "A", "votes": 60},
            {"id": 1, "name": "B", "votes": 40},
        ]

        winner = engine.determine_winner(proposals, 100)
        assert winner["name"] == "A"

        proposals = [
            {"id": 0, "name": "A", "votes": 40},
            {"id": 1, "name": "B", "votes": 30},
            {"id": 2, "name": "C", "votes": 30},
        ]

        winner = engine.determine_winner(proposals, 100)
        assert winner is None

    def test_super_majority(self):
        rules = VotingRules(voting_method=VotingMethod.SUPER_MAJORITY)
        engine = VotingEngine(rules)

        proposals = [
            {"id": 0, "name": "A", "votes": 70},
            {"id": 1, "name": "B", "votes": 30},
        ]

        winner = engine.determine_winner(proposals, 100)
        assert winner["name"] == "A"

        proposals = [
            {"id": 0, "name": "A", "votes": 60},
            {"id": 1, "name": "B", "votes": 40},
        ]

        winner = engine.determine_winner(proposals, 100)
        assert winner is None

    def test_plurality(self):
        rules = VotingRules(voting_method=VotingMethod.PLURALITY)
        engine = VotingEngine(rules)

        proposals = [
            {"id": 0, "name": "A", "votes": 40},
            {"id": 1, "name": "B", "votes": 35},
            {"id": 2, "name": "C", "votes": 25},
        ]

        winner = engine.determine_winner(proposals, 100)
        assert winner["name"] == "A"

    def test_calculate_results(self):
        proposals = [
            {"id": 0, "name": "A", "votes": 60},
            {"id": 1, "name": "B", "votes": 40},
        ]

        result = self.engine.calculate_results(
            session_id=1,
            proposals=proposals,
            total_eligible_voters=100,
        )

        assert result.session_id == 1
        assert result.total_votes_cast == 100
        assert result.winner["name"] == "A"


class TestOnePersonOneVote:
    """一人一票测试"""

    def setup_method(self):
        self.opov = OnePersonOneVote()

    def test_can_vote_initially(self):
        assert self.opov.can_vote(1, "0xVoter1") is True

    def test_record_vote(self):
        self.opov.record_vote(1, "0xVoter1")
        assert self.opov.has_voted(1, "0xVoter1") is True
        assert self.opov.can_vote(1, "0xVoter1") is False

    def test_cannot_vote_twice(self):
        self.opov.record_vote(1, "0xVoter1")
        assert self.opov.can_vote(1, "0xVoter1") is False

    def test_different_sessions(self):
        self.opov.record_vote(1, "0xVoter1")
        assert self.opov.can_vote(2, "0xVoter1") is True

    def test_different_voters(self):
        self.opov.record_vote(1, "0xVoter1")
        assert self.opov.can_vote(1, "0xVoter2") is True

    def test_get_voter_count(self):
        self.opov.record_vote(1, "0xVoter1")
        self.opov.record_vote(1, "0xVoter2")
        assert self.opov.get_voter_count(1) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
