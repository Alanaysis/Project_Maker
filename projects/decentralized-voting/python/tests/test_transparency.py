"""
透明性模块测试
"""

import pytest
import time
from src.transparency import (
    VoteLedger,
    AuditTrail,
    TransparencyReport,
    VoteRecord,
    AuditEntry,
)


class TestVoteLedger:
    """投票账本测试"""

    def setup_method(self):
        self.ledger = VoteLedger()

    def test_record_vote(self):
        record = self.ledger.record_vote(
            session_id=1,
            voter_address="0xVoter1",
            proposal_id=0,
        )
        assert record.session_id == 1
        assert record.voter_address == "0xVoter1"
        assert record.proposal_id == 0

    def test_get_session_records(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(1, "0xVoter2", 1)
        self.ledger.record_vote(2, "0xVoter3", 0)

        records = self.ledger.get_session_records(1)
        assert len(records) == 2

    def test_get_voter_records(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(2, "0xVoter1", 1)

        records = self.ledger.get_voter_records("0xVoter1")
        assert len(records) == 2

    def test_verify_record(self):
        record = self.ledger.record_vote(1, "0xVoter1", 0)
        assert self.ledger.verify_record(record) is True

    def test_get_record_count(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(1, "0xVoter2", 1)
        assert self.ledger.get_record_count() == 2

    def test_export_records(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(1, "0xVoter2", 1)

        records = self.ledger.export_records(session_id=1)
        assert len(records) == 2
        assert "session_id" in records[0]


class TestAuditTrail:
    """审计追踪测试"""

    def setup_method(self):
        self.trail = AuditTrail()

    def test_add_entry(self):
        entry = self.trail.add_entry(
            action="create_session",
            actor="0xCreator",
            details={"session_id": 1},
        )
        assert entry.action == "create_session"
        assert entry.actor == "0xCreator"

    def test_chain_integrity(self):
        self.trail.add_entry("action1", "actor1", {"data": 1})
        self.trail.add_entry("action2", "actor2", {"data": 2})
        self.trail.add_entry("action3", "actor3", {"data": 3})

        assert self.trail.verify_chain() is True

    def test_get_entries_by_action(self):
        self.trail.add_entry("vote", "actor1", {"data": 1})
        self.trail.add_entry("vote", "actor2", {"data": 2})
        self.trail.add_entry("create", "actor3", {"data": 3})

        entries = self.trail.get_entries_by_action("vote")
        assert len(entries) == 2

    def test_get_entries_by_actor(self):
        self.trail.add_entry("action1", "actor1", {"data": 1})
        self.trail.add_entry("action2", "actor1", {"data": 2})
        self.trail.add_entry("action3", "actor2", {"data": 3})

        entries = self.trail.get_entries_by_actor("actor1")
        assert len(entries) == 2

    def test_get_entries_in_time_range(self):
        start = time.time()
        self.trail.add_entry("action1", "actor1", {"data": 1})
        time.sleep(0.1)
        self.trail.add_entry("action2", "actor2", {"data": 2})
        end = time.time()

        entries = self.trail.get_entries_in_time_range(start, end)
        assert len(entries) == 2

    def test_export_audit_trail(self):
        self.trail.add_entry("action1", "actor1", {"data": 1})
        self.trail.add_entry("action2", "actor2", {"data": 2})

        exported = self.trail.export_audit_trail()
        assert len(exported) == 2
        assert "action" in exported[0]

    def test_get_statistics(self):
        self.trail.add_entry("vote", "actor1", {"data": 1})
        self.trail.add_entry("vote", "actor2", {"data": 2})
        self.trail.add_entry("create", "actor1", {"data": 3})

        stats = self.trail.get_statistics()
        assert stats["total_entries"] == 3
        assert stats["action_counts"]["vote"] == 2
        assert stats["actor_counts"]["actor1"] == 2


class TestTransparencyReport:
    """透明度报告测试"""

    def setup_method(self):
        self.ledger = VoteLedger()
        self.trail = AuditTrail()
        self.report = TransparencyReport(self.ledger, self.trail)

    def test_generate_session_report(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(1, "0xVoter2", 1)
        self.ledger.record_vote(1, "0xVoter3", 0)

        report = self.report.generate_session_report(1)
        assert report["session_id"] == 1
        assert report["total_votes"] == 3
        assert report["vote_distribution"][0] == 2
        assert report["vote_distribution"][1] == 1

    def test_generate_voter_report(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(2, "0xVoter1", 1)

        report = self.report.generate_voter_report("0xVoter1")
        assert report["voter_address"] == "0xVoter1"
        assert report["total_votes"] == 2
        assert 1 in report["sessions_participated"]
        assert 2 in report["sessions_participated"]

    def test_generate_full_report(self):
        self.ledger.record_vote(1, "0xVoter1", 0)
        self.ledger.record_vote(1, "0xVoter2", 1)

        report = self.report.generate_full_report()
        assert report["total_records"] == 2
        assert report["blockchain_valid"] is True
        assert report["audit_trail_valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
