import { expect } from "chai";
import { ethers } from "hardhat";
import { Voting } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("Voting", function () {
  let voting: Voting;
  let owner: HardhatEthersSigner;
  let voter1: HardhatEthersSigner;
  let voter2: HardhatEthersSigner;
  let voter3: HardhatEthersSigner;

  beforeEach(async function () {
    [owner, voter1, voter2, voter3] = await ethers.getSigners();

    const VotingFactory = await ethers.getContractFactory("Voting");
    voting = await VotingFactory.deploy();
    await voting.waitForDeployment();
  });

  describe("创建投票活动", function () {
    it("应该成功创建投票活动", async function () {
      const startTime = Math.floor(Date.now() / 1000) + 10;
      const endTime = startTime + 3600;

      await expect(
        voting.createVoteSession(
          "测试投票",
          "这是一个测试投票",
          startTime,
          endTime
        )
      ).to.emit(voting, "VoteSessionCreated");

      expect(await voting.voteSessionCount()).to.equal(1);
    });

    it("应该拒绝无效的时间参数", async function () {
      const startTime = Math.floor(Date.now() / 1000) + 3600;
      const endTime = startTime - 100;

      await expect(
        voting.createVoteSession(
          "测试投票",
          "这是一个测试投票",
          startTime,
          endTime
        )
      ).to.be.revertedWith("开始时间必须早于结束时间");
    });
  });

  describe("添加提案", function () {
    let sessionId: number;

    beforeEach(async function () {
      const startTime = Math.floor(Date.now() / 1000) + 10;
      const endTime = startTime + 3600;

      await voting.createVoteSession(
        "测试投票",
        "这是一个测试投票",
        startTime,
        endTime
      );
      sessionId = 0;
    });

    it("应该成功添加提案", async function () {
      await expect(
        voting.addProposal(sessionId, "提案1", "提案1描述")
      ).to.emit(voting, "ProposalAdded");

      const proposalCount = await voting.getProposalCount(sessionId);
      expect(proposalCount).to.equal(1);
    });

    it("应该拒绝非创建者添加提案", async function () {
      await expect(
        voting.connect(voter1).addProposal(sessionId, "提案1", "提案1描述")
      ).to.be.revertedWith("只有创建者可以执行此操作");
    });
  });

  describe("投票功能", function () {
    let sessionId: number;

    beforeEach(async function () {
      const startTime = Math.floor(Date.now() / 1000) + 1;
      const endTime = startTime + 3600;

      await voting.createVoteSession(
        "测试投票",
        "这是一个测试投票",
        startTime,
        endTime
      );
      sessionId = 0;

      await voting.addProposal(sessionId, "提案1", "提案1描述");
      await voting.addProposal(sessionId, "提案2", "提案2描述");

      // 等待开始时间到达
      await new Promise((resolve) => setTimeout(resolve, 2000));

      await voting.startVoting(sessionId);
    });

    it("应该成功投票", async function () {
      await expect(
        voting.connect(voter1).vote(sessionId, 0)
      ).to.emit(voting, "VoteCast");

      expect(await voting.hasVoted(sessionId, voter1.address)).to.be.true;
    });

    it("应该拒绝重复投票", async function () {
      await voting.connect(voter1).vote(sessionId, 0);

      await expect(
        voting.connect(voter1).vote(sessionId, 1)
      ).to.be.revertedWith("您已经投过票了");
    });

    it("应该正确计票", async function () {
      await voting.connect(voter1).vote(sessionId, 0);
      await voting.connect(voter2).vote(sessionId, 0);
      await voting.connect(voter3).vote(sessionId, 1);

      const [name1, desc1, count1] = await voting.getProposal(sessionId, 0);
      const [name2, desc2, count2] = await voting.getProposal(sessionId, 1);

      expect(count1).to.equal(2);
      expect(count2).to.equal(1);
    });
  });

  describe("结束投票", function () {
    let sessionId: number;

    beforeEach(async function () {
      const startTime = Math.floor(Date.now() / 1000) + 1;
      const endTime = startTime + 3600;

      await voting.createVoteSession(
        "测试投票",
        "这是一个测试投票",
        startTime,
        endTime
      );
      sessionId = 0;

      await voting.addProposal(sessionId, "提案1", "提案1描述");
      await voting.addProposal(sessionId, "提案2", "提案2描述");

      // 等待开始时间到达
      await new Promise((resolve) => setTimeout(resolve, 2000));

      await voting.startVoting(sessionId);
    });

    it("应该成功结束投票", async function () {
      await voting.connect(voter1).vote(sessionId, 0);
      await voting.connect(voter2).vote(sessionId, 1);

      await expect(
        voting.endVoting(sessionId)
      ).to.emit(voting, "VoteSessionEnded");

      const session = await voting.getVoteSession(sessionId);
      expect(session.status).to.equal(2); // VoteStatus.Ended
    });

    it("应该拒绝在投票结束后投票", async function () {
      await voting.connect(voter1).vote(sessionId, 0);
      await voting.endVoting(sessionId);

      await expect(
        voting.connect(voter2).vote(sessionId, 0)
      ).to.be.revertedWith("投票活动未处于进行中状态");
    });
  });

  describe("查询功能", function () {
    let sessionId: number;

    beforeEach(async function () {
      const startTime = Math.floor(Date.now() / 1000) + 1;
      const endTime = startTime + 3600;

      await voting.createVoteSession(
        "测试投票",
        "这是一个测试投票",
        startTime,
        endTime
      );
      sessionId = 0;

      await voting.addProposal(sessionId, "提案1", "提案1描述");
      await voting.addProposal(sessionId, "提案2", "提案2描述");

      // 等待开始时间到达
      await new Promise((resolve) => setTimeout(resolve, 2000));

      await voting.startVoting(sessionId);
    });

    it("应该正确返回投票活动详情", async function () {
      const session = await voting.getVoteSession(sessionId);

      expect(session.title).to.equal("测试投票");
      expect(session.description).to.equal("这是一个测试投票");
      expect(session.creator).to.equal(owner.address);
    });

    it("应该正确返回提案详情", async function () {
      const [name, description, voteCount] = await voting.getProposal(sessionId, 0);

      expect(name).to.equal("提案1");
      expect(description).to.equal("提案1描述");
      expect(voteCount).to.equal(0);
    });

    it("应该正确返回用户的投票选择", async function () {
      await voting.connect(voter1).vote(sessionId, 1);

      const votedProposal = await voting.getVotedProposal(sessionId, voter1.address);
      expect(votedProposal).to.equal(1);
    });
  });
});
