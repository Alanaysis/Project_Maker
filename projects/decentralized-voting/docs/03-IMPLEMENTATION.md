# 03 - 实现细节

## 3.1 智能合约实现

### 3.1.1 合约结构

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Voting {
    // 数据结构定义
    enum VoteStatus { NotStarted, Active, Ended }
    struct Proposal { string name; string description; uint256 voteCount; }
    struct VoteSession { ... }

    // 状态变量
    uint256 public voteSessionCount;
    mapping(uint256 => VoteSession) public voteSessions;

    // 事件
    event VoteSessionCreated(...);
    event ProposalAdded(...);
    event VoteCast(...);
    event VoteSessionEnded(...);

    // 修饰符
    modifier onlySessionCreator(uint256 _sessionId) { ... }
    modifier sessionExists(uint256 _sessionId) { ... }
    modifier sessionActive(uint256 _sessionId) { ... }

    // 核心函数
    function createVoteSession(...) external returns (uint256) { ... }
    function addProposal(...) external { ... }
    function startVoting(uint256 _sessionId) external { ... }
    function vote(uint256 _sessionId, uint256 _proposalIndex) external { ... }
    function endVoting(uint256 _sessionId) external { ... }

    // 查询函数
    function getVoteSession(uint256 _sessionId) external view returns (...) { ... }
    function getProposal(uint256 _sessionId, uint256 _proposalIndex) external view returns (...) { ... }
    function getProposalCount(uint256 _sessionId) external view returns (uint256) { ... }
    function hasVoted(uint256 _sessionId, address _voter) external view returns (bool) { ... }
    function getVotedProposal(uint256 _sessionId, address _voter) external view returns (uint256) { ... }
}
```

### 3.1.2 关键实现细节

#### 数据存储

使用 `mapping` 存储投票活动数据，避免数组的 Gas 消耗：

```solidity
mapping(uint256 => VoteSession) public voteSessions;
```

#### 状态管理

使用枚举管理投票状态，确保状态转换的正确性：

```solidity
enum VoteStatus {
    NotStarted,  // 未开始
    Active,       // 进行中
    Ended         // 已结束
}
```

#### 权限控制

使用修饰符限制函数调用权限：

```solidity
modifier onlySessionCreator(uint256 _sessionId) {
    require(
        msg.sender == voteSessions[_sessionId].creator,
        "只有创建者可以执行此操作"
    );
    _;
}
```

#### 防重复投票

使用 mapping 记录用户投票状态：

```solidity
mapping(address => bool) hasVoted;
mapping(address => uint256) votedProposal;
```

### 3.1.3 Gas 优化

1. **使用 `memory` 替代 `storage`**
   - 函数参数使用 `memory`
   - 局部变量使用 `memory`

2. **减少存储操作**
   - 批量更新状态
   - 使用事件替代存储

3. **优化循环**
   - 避免无限循环
   - 使用 `break` 提前退出

### 3.1.4 错误处理

使用 `require` 进行输入验证：

```solidity
require(_startTime < _endTime, "开始时间必须早于结束时间");
require(_startTime >= block.timestamp, "开始时间不能早于当前时间");
require(_proposalIndex < session.proposals.length, "提案不存在");
require(!session.hasVoted[msg.sender], "您已经投过票了");
```

## 3.2 前端实现

### 3.2.1 项目结构

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # 布局组件
│   │   └── page.tsx        # 主页面
│   ├── components/
│   │   └── WalletConnect.tsx  # 钱包连接组件
│   ├── hooks/
│   │   └── useVoting.ts    # 投票 Hook
│   ├── lib/
│   │   └── contracts.ts    # 合约配置
│   └── types/
│       └── global.d.ts    # 类型定义
├── public/                  # 静态资源
└── package.json
```

### 3.2.2 钱包连接实现

```typescript
// hooks/useVoting.ts
const connectWallet = useCallback(async () => {
  try {
    if (!window.ethereum) {
      throw new Error("请安装 MetaMask 钱包");
    }

    const browserProvider = new ethers.BrowserProvider(window.ethereum);
    const signer = await browserProvider.getSigner();
    const address = await signer.getAddress();

    setProvider(browserProvider);
    setSigner(signer);
    setAccount(address);
    setIsConnected(true);

    // 初始化合约
    if (VOTING_CONTRACT_ADDRESS) {
      const votingContract = new ethers.Contract(
        VOTING_CONTRACT_ADDRESS,
        VOTING_ABI,
        signer
      );
      setContract(votingContract);
    }
  } catch (err: any) {
    setError(err.message || "连接钱包失败");
  }
}, []);
```

### 3.2.3 合约交互实现

```typescript
// 创建投票活动
const createVoteSession = useCallback(
  async (title: string, description: string, startTime: number, endTime: number) => {
    if (!contract || !signer) {
      throw new Error("请先连接钱包");
    }

    setIsLoading(true);
    setError("");

    try {
      const tx = await contract.createVoteSession(title, description, startTime, endTime);
      const receipt = await tx.wait();

      // 从事件中获取 sessionId
      const event = receipt.logs.find((log: any) => {
        try {
          const parsed = contract.interface.parseLog(log);
          return parsed?.name === "VoteSessionCreated";
        } catch {
          return false;
        }
      });

      if (event) {
        const parsed = contract.interface.parseLog(event);
        return parsed?.args.sessionId;
      }

      return null;
    } catch (err: any) {
      setError(err.message || "创建投票活动失败");
      throw err;
    } finally {
      setIsLoading(false);
    }
  },
  [contract, signer]
);
```

### 3.2.4 状态管理

使用 React Hooks 进行状态管理：

```typescript
// 状态定义
const [sessions, setSessions] = useState<VoteSession[]>([]);
const [isConnected, setIsConnected] = useState(false);
const [account, setAccount] = useState<string>("");
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string>("");

// 表单状态
const [newSession, setNewSession] = useState({
  title: "",
  description: "",
  startTime: "",
  endTime: "",
});
const [newProposal, setNewProposal] = useState({
  sessionId: 0,
  name: "",
  description: "",
});
```

### 3.2.5 事件处理

```typescript
// 创建投票活动
const handleCreateSession = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!isConnected) {
    alert("请先连接钱包");
    return;
  }

  try {
    const startTime = Math.floor(new Date(newSession.startTime).getTime() / 1000);
    const endTime = Math.floor(new Date(newSession.endTime).getTime() / 1000);

    await createVoteSession(
      newSession.title,
      newSession.description,
      startTime,
      endTime
    );

    // 重新加载投票活动
    const count = await getVoteSessionCount();
    const session = await getVoteSession(count - 1);
    if (session) {
      setSessions([...sessions, session]);
    }

    setNewSession({ title: "", description: "", startTime: "", endTime: "" });
  } catch (err) {
    console.error("创建投票活动失败:", err);
  }
};
```

### 3.2.6 UI 组件实现

#### 钱包连接组件

```typescript
// components/WalletConnect.tsx
export default function WalletConnect() {
  const { account, isConnected, isLoading, error, connectWallet } = useVoting();

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <div className="flex items-center gap-4">
      {isConnected ? (
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-sm font-medium text-gray-700">
            {formatAddress(account)}
          </span>
        </div>
      ) : (
        <button
          onClick={connectWallet}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? "连接中..." : "连接钱包"}
        </button>
      )}

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
```

#### 投票活动卡片

```typescript
// 页面中的投票活动卡片
<div className="bg-white rounded-lg shadow-md p-6">
  <div className="flex justify-between items-start mb-4">
    <div>
      <h3 className="text-xl font-semibold text-gray-900">
        {session.title}
      </h3>
      <p className="text-gray-600 mt-1">
        {session.description}
      </p>
    </div>
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(session.status)}`}>
      {getStatusText(session.status)}
    </span>
  </div>

  <div className="grid grid-cols-2 gap-4 mb-4 text-sm text-gray-500">
    <div>
      <span className="font-medium">开始时间：</span>
      {formatTime(session.startTime)}
    </div>
    <div>
      <span className="font-medium">结束时间：</span>
      {formatTime(session.endTime)}
    </div>
    <div>
      <span className="font-medium">创建者：</span>
      {session.creator.slice(0, 6)}...{session.creator.slice(-4)}
    </div>
    <div>
      <span className="font-medium">总投票数：</span>
      {session.totalVotes}
    </div>
  </div>

  {/* 提案列表 */}
  {session.proposals.length > 0 && (
    <div className="mb-4">
      <h4 className="font-medium text-gray-700 mb-2">提案列表：</h4>
      <div className="space-y-2">
        {session.proposals.map((proposal, index) => (
          <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">{proposal.name}</p>
              <p className="text-sm text-gray-500">{proposal.description}</p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-lg font-semibold text-blue-600">
                {proposal.voteCount} 票
              </span>
              {session.status === VoteStatus.Active && (
                <button
                  onClick={() => handleVote(session.id, index)}
                  disabled={isLoading}
                  className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  投票
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )}

  {/* 操作按钮 */}
  <div className="flex gap-2">
    {session.status === VoteStatus.NotStarted &&
      session.creator.toLowerCase() === account.toLowerCase() && (
        <button
          onClick={() => handleStartVoting(session.id)}
          disabled={isLoading}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          开始投票
        </button>
      )}
    {session.status === VoteStatus.Active &&
      session.creator.toLowerCase() === account.toLowerCase() && (
        <button
          onClick={() => handleEndVoting(session.id)}
          disabled={isLoading}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
        >
          结束投票
        </button>
      )}
  </div>
</div>
```

## 3.3 部署实现

### 3.3.1 部署脚本

```typescript
// scripts/deploy.ts
import { ethers } from "hardhat";

async function main() {
  console.log("开始部署 Voting 合约...");

  const VotingFactory = await ethers.getContractFactory("Voting");
  const voting = await VotingFactory.deploy();

  await voting.waitForDeployment();

  const address = await voting.getAddress();
  console.log("Voting 合约已部署到:", address);

  // 更新前端配置
  console.log("\n请将以下地址更新到前端配置文件中:");
  console.log(`NEXT_PUBLIC_VOTING_CONTRACT_ADDRESS=${address}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

### 3.3.2 部署流程

1. **启动本地区块链**
   ```bash
   npx hardhat node
   ```

2. **部署合约**
   ```bash
   npx hardhat run scripts/deploy.ts --network localhost
   ```

3. **更新前端配置**
   将合约地址更新到 `frontend/.env.local` 文件中。

4. **启动前端**
   ```bash
   cd frontend
   npm run dev
   ```

## 3.4 测试实现

### 3.4.1 测试结构

```typescript
// test/Voting.test.ts
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
      // 测试代码
    });

    it("应该拒绝无效的时间参数", async function () {
      // 测试代码
    });
  });

  // 更多测试...
});
```

### 3.4.2 测试用例

1. **创建投票活动测试**
   - 成功创建投票活动
   - 拒绝无效的时间参数

2. **添加提案测试**
   - 成功添加提案
   - 拒绝非创建者添加提案

3. **投票功能测试**
   - 成功投票
   - 拒绝重复投票
   - 正确计票

4. **结束投票测试**
   - 成功结束投票
   - 拒绝在投票结束后投票

5. **查询功能测试**
   - 正确返回投票活动详情
   - 正确返回提案详情
   - 正确返回用户的投票选择

## 3.5 错误处理

### 3.5.1 智能合约错误

使用 `require` 进行输入验证，并提供友好的错误信息：

```solidity
require(_startTime < _endTime, "开始时间必须早于结束时间");
require(_startTime >= block.timestamp, "开始时间不能早于当前时间");
require(_proposalIndex < session.proposals.length, "提案不存在");
require(!session.hasVoted[msg.sender], "您已经投过票了");
```

### 3.5.2 前端错误

捕获并处理异常，显示友好的错误信息：

```typescript
try {
  const tx = await contract.createVoteSession(...);
  const receipt = await tx.wait();
  // 处理成功
} catch (err: any) {
  setError(err.message || "创建投票活动失败");
  throw err;
} finally {
  setIsLoading(false);
}
```

## 3.6 性能优化

### 3.6.1 智能合约优化

1. **存储优化**
   - 使用 `mapping` 替代数组
   - 打包存储变量

2. **计算优化**
   - 减少循环次数
   - 使用事件替代存储

3. **Gas 优化**
   - 使用 `calldata` 替代 `memory`
   - 批量操作

### 3.6.2 前端优化

1. **数据缓存**
   - 缓存投票活动数据
   - 避免重复请求

2. **懒加载**
   - 按需加载组件
   - 延迟加载数据

3. **错误边界**
   - 捕获组件错误
   - 显示降级 UI
