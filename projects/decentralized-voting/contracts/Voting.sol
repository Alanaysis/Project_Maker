// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title Voting - 去中心化投票系统
 * @notice 实现投票创建、投票、计票和结果公示功能
 * @dev 使用 OpenZeppelin 的 Ownable 进行权限管理
 */
contract Voting {
    // 投票状态枚举
    enum VoteStatus {
        NotStarted,  // 未开始
        Active,       // 进行中
        Ended         // 已结束
    }

    // 提案结构
    struct Proposal {
        string name;           // 提案名称
        string description;    // 提案描述
        uint256 voteCount;     // 投票数
    }

    // 投票活动结构
    struct VoteSession {
        string title;           // 投票标题
        string description;     // 投票描述
        address creator;        // 创建者
        uint256 startTime;      // 开始时间
        uint256 endTime;        // 结束时间
        VoteStatus status;      // 投票状态
        Proposal[] proposals;   // 提案列表
        mapping(address => bool) hasVoted;  // 投票记录
        mapping(address => uint256) votedProposal;  // 投票选择
        uint256 totalVotes;    // 总投票数
    }

    // 状态变量
    uint256 public voteSessionCount;  // 投票活动计数
    mapping(uint256 => VoteSession) public voteSessions;  // 投票活动映射
    mapping(uint256 => mapping(address => bool)) public sessionHasVoted;  // 投票记录

    // 事件
    event VoteSessionCreated(
        uint256 indexed sessionId,
        string title,
        address indexed creator,
        uint256 startTime,
        uint256 endTime
    );

    event ProposalAdded(
        uint256 indexed sessionId,
        uint256 proposalIndex,
        string name
    );

    event VoteCast(
        uint256 indexed sessionId,
        address indexed voter,
        uint256 proposalIndex
    );

    event VoteSessionEnded(
        uint256 indexed sessionId,
        uint256 totalVotes
    );

    // 修饰符
    modifier onlySessionCreator(uint256 _sessionId) {
        require(
            msg.sender == voteSessions[_sessionId].creator,
            "只有创建者可以执行此操作"
        );
        _;
    }

    modifier sessionExists(uint256 _sessionId) {
        require(
            _sessionId < voteSessionCount,
            "投票活动不存在"
        );
        _;
    }

    modifier sessionActive(uint256 _sessionId) {
        VoteSession storage session = voteSessions[_sessionId];
        require(
            session.status == VoteStatus.Active,
            "投票活动未处于进行中状态"
        );
        require(
            block.timestamp >= session.startTime,
            "投票尚未开始"
        );
        require(
            block.timestamp <= session.endTime,
            "投票已结束"
        );
        _;
    }

    /**
     * @notice 创建新的投票活动
     * @param _title 投票标题
     * @param _description 投票描述
     * @param _startTime 开始时间
     * @param _endTime 结束时间
     * @return sessionId 新创建的投票活动ID
     */
    function createVoteSession(
        string memory _title,
        string memory _description,
        uint256 _startTime,
        uint256 _endTime
    ) external returns (uint256 sessionId) {
        require(_startTime < _endTime, "开始时间必须早于结束时间");
        require(_startTime >= block.timestamp, "开始时间不能早于当前时间");

        sessionId = voteSessionCount++;

        VoteSession storage session = voteSessions[sessionId];
        session.title = _title;
        session.description = _description;
        session.creator = msg.sender;
        session.startTime = _startTime;
        session.endTime = _endTime;
        session.status = VoteStatus.NotStarted;

        emit VoteSessionCreated(sessionId, _title, msg.sender, _startTime, _endTime);

        return sessionId;
    }

    /**
     * @notice 向投票活动添加提案
     * @param _sessionId 投票活动ID
     * @param _name 提案名称
     * @param _description 提案描述
     */
    function addProposal(
        uint256 _sessionId,
        string memory _name,
        string memory _description
    ) external sessionExists(_sessionId) onlySessionCreator(_sessionId) {
        VoteSession storage session = voteSessions[_sessionId];
        require(
            session.status == VoteStatus.NotStarted,
            "只能在投票开始前添加提案"
        );

        uint256 proposalIndex = session.proposals.length;
        session.proposals.push(Proposal({
            name: _name,
            description: _description,
            voteCount: 0
        }));

        emit ProposalAdded(_sessionId, proposalIndex, _name);
    }

    /**
     * @notice 开始投票活动
     * @param _sessionId 投票活动ID
     */
    function startVoting(uint256 _sessionId)
        external
        sessionExists(_sessionId)
        onlySessionCreator(_sessionId)
    {
        VoteSession storage session = voteSessions[_sessionId];
        require(
            session.status == VoteStatus.NotStarted,
            "投票活动已经开始或已结束"
        );
        require(
            session.proposals.length > 0,
            "至少需要一个提案"
        );
        require(
            block.timestamp >= session.startTime,
            "尚未到达开始时间"
        );

        session.status = VoteStatus.Active;
    }

    /**
     * @notice 进行投票
     * @param _sessionId 投票活动ID
     * @param _proposalIndex 提案索引
     */
    function vote(uint256 _sessionId, uint256 _proposalIndex)
        external
        sessionExists(_sessionId)
        sessionActive(_sessionId)
    {
        VoteSession storage session = voteSessions[_sessionId];

        require(
            _proposalIndex < session.proposals.length,
            "提案不存在"
        );
        require(
            !session.hasVoted[msg.sender],
            "您已经投过票了"
        );

        session.proposals[_proposalIndex].voteCount++;
        session.hasVoted[msg.sender] = true;
        session.votedProposal[msg.sender] = _proposalIndex;
        session.totalVotes++;

        emit VoteCast(_sessionId, msg.sender, _proposalIndex);
    }

    /**
     * @notice 结束投票活动
     * @param _sessionId 投票活动ID
     */
    function endVoting(uint256 _sessionId)
        external
        sessionExists(_sessionId)
        onlySessionCreator(_sessionId)
    {
        VoteSession storage session = voteSessions[_sessionId];
        require(
            session.status == VoteStatus.Active,
            "投票活动未处于进行中状态"
        );

        session.status = VoteStatus.Ended;

        emit VoteSessionEnded(_sessionId, session.totalVotes);
    }

    /**
     * @notice 获取投票活动的提案数量
     * @param _sessionId 投票活动ID
     * @return 提案数量
     */
    function getProposalCount(uint256 _sessionId)
        external
        view
        sessionExists(_sessionId)
        returns (uint256)
    {
        return voteSessions[_sessionId].proposals.length;
    }

    /**
     * @notice 获取提案详情
     * @param _sessionId 投票活动ID
     * @param _proposalIndex 提案索引
     * @return name 提案名称
     * @return description 提案描述
     * @return voteCount 投票数
     */
    function getProposal(uint256 _sessionId, uint256 _proposalIndex)
        external
        view
        sessionExists(_sessionId)
        returns (
            string memory name,
            string memory description,
            uint256 voteCount
        )
    {
        require(
            _proposalIndex < voteSessions[_sessionId].proposals.length,
            "提案不存在"
        );

        Proposal storage proposal = voteSessions[_sessionId].proposals[_proposalIndex];
        return (proposal.name, proposal.description, proposal.voteCount);
    }

    /**
     * @notice 获取投票活动详情
     * @param _sessionId 投票活动ID
     * @return title 投票标题
     * @return description 投票描述
     * @return creator 创建者
     * @return startTime 开始时间
     * @return endTime 结束时间
     * @return status 投票状态
     * @return totalVotes 总投票数
     */
    function getVoteSession(uint256 _sessionId)
        external
        view
        sessionExists(_sessionId)
        returns (
            string memory title,
            string memory description,
            address creator,
            uint256 startTime,
            uint256 endTime,
            VoteStatus status,
            uint256 totalVotes
        )
    {
        VoteSession storage session = voteSessions[_sessionId];
        return (
            session.title,
            session.description,
            session.creator,
            session.startTime,
            session.endTime,
            session.status,
            session.totalVotes
        );
    }

    /**
     * @notice 检查用户是否已投票
     * @param _sessionId 投票活动ID
     * @param _voter 投票者地址
     * @return 是否已投票
     */
    function hasVoted(uint256 _sessionId, address _voter)
        external
        view
        sessionExists(_sessionId)
        returns (bool)
    {
        return voteSessions[_sessionId].hasVoted[_voter];
    }

    /**
     * @notice 获取用户的投票选择
     * @param _sessionId 投票活动ID
     * @param _voter 投票者地址
     * @return proposalIndex 投票的提案索引
     */
    function getVotedProposal(uint256 _sessionId, address _voter)
        external
        view
        sessionExists(_sessionId)
        returns (uint256 proposalIndex)
    {
        require(
            voteSessions[_sessionId].hasVoted[_voter],
            "用户尚未投票"
        );
        return voteSessions[_sessionId].votedProposal[_voter];
    }
}
