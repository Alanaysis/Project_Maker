# 02 - 架构设计

## 2.1 系统架构

### 2.1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (Frontend)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   页面组件   │  │   业务组件   │  │    自定义 Hooks     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    区块链交互层 (ethers.js)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  合约 ABI   │  │   Provider  │  │      Signer        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   智能合约层 (Solidity)                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Voting.sol                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ 投票管理    │  │ 提案管理    │  │ 投票执行    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    区块链网络层 (Ethereum)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  本地网络   │  │  测试网络   │  │      主网          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.1.2 组件架构

```
Frontend
├── App
│   ├── Layout
│   └── Pages
│       └── Home
├── Components
│   ├── WalletConnect
│   ├── VoteSessionList
│   ├── VoteSessionCard
│   ├── CreateVoteForm
│   └── AddProposalForm
├── Hooks
│   ├── useVoting
│   └── useWallet
└── Lib
    ├── contracts.ts
    └── utils.ts
```

## 2.2 智能合约设计

### 2.2.1 数据结构

```solidity
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
```

### 2.2.2 状态变量

```solidity
uint256 public voteSessionCount;  // 投票活动计数
mapping(uint256 => VoteSession) public voteSessions;  // 投票活动映射
```

### 2.2.3 核心函数

#### 创建投票活动

```solidity
function createVoteSession(
    string memory _title,
    string memory _description,
    uint256 _startTime,
    uint256 _endTime
) external returns (uint256 sessionId)
```

**参数说明:**
- `_title`: 投票标题
- `_description`: 投票描述
- `_startTime`: 开始时间 (Unix 时间戳)
- `_endTime`: 结束时间 (Unix 时间戳)

**返回值:**
- `sessionId`: 新创建的投票活动 ID

**业务逻辑:**
1. 验证时间参数有效性
2. 创建新的投票活动
3. 设置初始状态为 NotStarted
4. 触发 VoteSessionCreated 事件

#### 添加提案

```solidity
function addProposal(
    uint256 _sessionId,
    string memory _name,
    string memory _description
) external
```

**参数说明:**
- `_sessionId`: 投票活动 ID
- `_name`: 提案名称
- `_description`: 提案描述

**业务逻辑:**
1. 验证投票活动存在
2. 验证调用者是创建者
3. 验证投票活动状态为 NotStarted
4. 添加新提案到列表
5. 触发 ProposalAdded 事件

#### 开始投票

```solidity
function startVoting(uint256 _sessionId) external
```

**参数说明:**
- `_sessionId`: 投票活动 ID

**业务逻辑:**
1. 验证投票活动存在
2. 验证调用者是创建者
3. 验证投票活动状态为 NotStarted
4. 验证至少有一个提案
5. 验证当前时间已到开始时间
6. 设置状态为 Active

#### 进行投票

```solidity
function vote(uint256 _sessionId, uint256 _proposalIndex) external
```

**参数说明:**
- `_sessionId`: 投票活动 ID
- `_proposalIndex`: 提案索引

**业务逻辑:**
1. 验证投票活动存在
2. 验证投票活动状态为 Active
3. 验证当前时间在有效期内
4. 验证提案存在
5. 验证用户未投票
6. 增加提案投票数
7. 记录用户投票
8. 增加总投票数
9. 触发 VoteCast 事件

#### 结束投票

```solidity
function endVoting(uint256 _sessionId) external
```

**参数说明:**
- `_sessionId`: 投票活动 ID

**业务逻辑:**
1. 验证投票活动存在
2. 验证调用者是创建者
3. 验证投票活动状态为 Active
4. 设置状态为 Ended
5. 触发 VoteSessionEnded 事件

### 2.2.4 查询函数

```solidity
function getVoteSession(uint256 _sessionId) external view returns (...)
function getProposal(uint256 _sessionId, uint256 _proposalIndex) external view returns (...)
function getProposalCount(uint256 _sessionId) external view returns (uint256)
function hasVoted(uint256 _sessionId, address _voter) external view returns (bool)
function getVotedProposal(uint256 _sessionId, address _voter) external view returns (uint256)
```

### 2.2.5 事件

```solidity
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
```

### 2.2.6 修饰符

```solidity
modifier onlySessionCreator(uint256 _sessionId) {
    require(msg.sender == voteSessions[_sessionId].creator, "只有创建者可以执行此操作");
    _;
}

modifier sessionExists(uint256 _sessionId) {
    require(_sessionId < voteSessionCount, "投票活动不存在");
    _;
}

modifier sessionActive(uint256 _sessionId) {
    VoteSession storage session = voteSessions[_sessionId];
    require(session.status == VoteStatus.Active, "投票活动未处于进行中状态");
    require(block.timestamp >= session.startTime, "投票尚未开始");
    require(block.timestamp <= session.endTime, "投票已结束");
    _;
}
```

## 2.3 前端架构

### 2.3.1 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│                        Header                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Logo        Title              WalletConnect          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        Main Content                          │
│  ┌────────────────────┐  ┌────────────────────────────────┐│
│  │   Left Sidebar     │  │       Main Area                ││
│  │  ┌──────────────┐  │  │  ┌──────────────────────────┐  ││
│  │  │ Create Vote  │  │  │  │  Vote Session List       │  ││
│  │  └──────────────┘  │  │  │  ┌────────────────────┐  │  ││
│  │  ┌──────────────┐  │  │  │  │  Session Card 1    │  │  ││
│  │  │ Add Proposal │  │  │  │  └────────────────────┘  │  ││
│  │  └──────────────┘  │  │  │  ┌────────────────────┐  │  ││
│  │                    │  │  │  │  Session Card 2    │  │  ││
│  └────────────────────┘  │  │  └────────────────────┘  │  ││
│                          │  └──────────────────────────┘  ││
│                          └────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.3.2 组件树

```
App
├── Header
│   ├── Logo
│   ├── Title
│   └── WalletConnect
└── Main
    ├── LeftSidebar
    │   ├── CreateVoteForm
    │   └── AddProposalForm
    └── MainArea
        └── VoteSessionList
            ├── VoteSessionCard
            │   ├── SessionInfo
            │   ├── ProposalList
            │   │   └── ProposalItem
            │   └── ActionButtons
            └── VoteSessionCard
                └── ...
```

### 2.3.3 状态管理

使用 React Hooks 进行状态管理：

```typescript
// 全局状态
const [sessions, setSessions] = useState<VoteSession[]>([]);
const [isConnected, setIsConnected] = useState(false);
const [account, setAccount] = useState<string>("");

// 表单状态
const [newSession, setNewSession] = useState({...});
const [newProposal, setNewProposal] = useState({...});

// 加载状态
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string>("");
```

### 2.3.4 数据流

```
User Action
    │
    ▼
Component Event Handler
    │
    ▼
Hook Function (useVoting)
    │
    ▼
ethers.js Contract Call
    │
    ▼
Blockchain Transaction
    │
    ▼
Transaction Receipt
    │
    ▼
Update State
    │
    ▼
Re-render UI
```

## 2.4 接口设计

### 2.4.1 智能合约接口

```typescript
// 合约 ABI
const VOTING_ABI = [
  "function createVoteSession(...) external returns (uint256)",
  "function addProposal(...) external",
  "function startVoting(uint256) external",
  "function vote(uint256, uint256) external",
  "function endVoting(uint256) external",
  "function getVoteSession(uint256) external view returns (...)",
  "function getProposal(uint256, uint256) external view returns (...)",
  "function getProposalCount(uint256) external view returns (uint256)",
  "function hasVoted(uint256, address) external view returns (bool)",
  "function getVotedProposal(uint256, address) external view returns (uint256)",
  "function voteSessionCount() external view returns (uint256)",
];
```

### 2.4.2 前端接口

```typescript
// useVoting Hook 返回值
interface UseVotingReturn {
  // 状态
  provider: ethers.BrowserProvider | null;
  signer: ethers.Signer | null;
  contract: ethers.Contract | null;
  account: string;
  isConnected: boolean;
  isLoading: boolean;
  error: string;

  // 方法
  connectWallet: () => Promise<void>;
  createVoteSession: (...) => Promise<number>;
  addProposal: (...) => Promise<void>;
  startVoting: (sessionId: number) => Promise<void>;
  vote: (sessionId: number, proposalIndex: number) => Promise<void>;
  endVoting: (sessionId: number) => Promise<void>;
  getVoteSession: (sessionId: number) => Promise<VoteSession | null>;
  getVoteSessionCount: () => Promise<number>;
  hasVoted: (sessionId: number, address: string) => Promise<boolean>;
  getVotedProposal: (sessionId: number, address: string) => Promise<number>;
}
```

## 2.5 安全架构

### 2.5.1 智能合约安全

1. **权限控制**
   - 使用 modifier 限制函数调用
   - 验证调用者身份

2. **输入验证**
   - 验证时间参数
   - 验证数组索引
   - 验证字符串长度

3. **状态管理**
   - 使用枚举管理状态
   - 状态转换验证

4. **防重入保护**
   - 使用 ReentrancyGuard
   - 状态更新在外部调用之前

### 2.5.2 前端安全

1. **输入消毒**
   - 过滤特殊字符
   - 验证数据格式

2. **错误处理**
   - 捕获并处理异常
   - 显示友好错误信息

3. **状态验证**
   - 验证用户操作权限
   - 验证数据一致性

## 2.6 性能优化

### 2.6.1 智能合约优化

1. **存储优化**
   - 使用 mapping 替代数组
   - 打包存储变量

2. **计算优化**
   - 减少循环次数
   - 使用事件替代存储

3. **Gas 优化**
   - 使用 calldata 替代 memory
   - 批量操作

### 2.6.2 前端优化

1. **数据缓存**
   - 缓存投票活动数据
   - 避免重复请求

2. **懒加载**
   - 按需加载组件
   - 延迟加载数据

3. **错误边界**
   - 捕获组件错误
   - 显示降级 UI

## 2.7 扩展性设计

### 2.7.1 合约扩展

1. **代理模式**
   - 使用 UUPS 代理
   - 支持合约升级

2. **模块化设计**
   - 分离关注点
   - 可复用组件

### 2.7.2 前端扩展

1. **插件系统**
   - 支持自定义组件
   - 支持主题定制

2. **多链支持**
   - 网络切换
   - 多合约管理
