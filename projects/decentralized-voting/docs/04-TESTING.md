# 04 - 测试说明

## 4.1 测试策略

### 4.1.1 测试层次

1. **单元测试**: 测试单个函数的功能
2. **集成测试**: 测试多个组件的协作
3. **端到端测试**: 测试完整的用户流程

### 4.1.2 测试工具

- **Hardhat**: 智能合约测试框架
- **Chai**: 断言库
- **ethers.js**: 区块链交互库

## 4.2 智能合约测试

### 4.2.1 测试文件位置

```
test/
└── Voting.test.ts
```

### 4.2.2 测试用例

#### 创建投票活动测试

```typescript
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
```

#### 添加提案测试

```typescript
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
```

#### 投票功能测试

```typescript
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
```

#### 结束投票测试

```typescript
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
```

#### 查询功能测试

```typescript
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
```

## 4.3 运行测试

### 4.3.1 运行所有测试

```bash
npx hardhat test
```

### 4.3.2 运行特定测试文件

```bash
npx hardhat test test/Voting.test.ts
```

### 4.3.3 运行带覆盖率的测试

```bash
npx hardhat coverage
```

### 4.3.4 运行带 Gas 报告的测试

```bash
REPORT_GAS=true npx hardhat test
```

## 4.4 测试覆盖率

### 4.4.1 覆盖率目标

- 语句覆盖率: > 90%
- 分支覆盖率: > 80%
- 函数覆盖率: > 95%
- 行覆盖率: > 90%

### 4.4.2 覆盖率报告

运行覆盖率测试后，会在 `coverage/` 目录下生成 HTML 报告。

## 4.5 测试最佳实践

### 4.5.1 测试命名

使用描述性的测试名称：

```typescript
it("应该成功创建投票活动", async function () { ... });
it("应该拒绝无效的时间参数", async function () { ... });
it("应该拒绝非创建者添加提案", async function () { ... });
```

### 4.5.2 测试隔离

每个测试用例应该独立运行，不依赖其他测试的状态：

```typescript
beforeEach(async function () {
  // 每个测试前重新部署合约
  const VotingFactory = await ethers.getContractFactory("Voting");
  voting = await VotingFactory.deploy();
  await voting.waitForDeployment();
});
```

### 4.5.3 测试数据

使用有意义的测试数据：

```typescript
const startTime = Math.floor(Date.now() / 1000) + 10;
const endTime = startTime + 3600;

await voting.createVoteSession(
  "测试投票",
  "这是一个测试投票",
  startTime,
  endTime
);
```

### 4.5.4 断言

使用清晰的断言：

```typescript
expect(await voting.voteSessionCount()).to.equal(1);
expect(session.title).to.equal("测试投票");
expect(count1).to.equal(2);
```

## 4.6 测试调试

### 4.6.1 调试测试

使用 `console.log` 调试测试：

```typescript
it("应该成功创建投票活动", async function () {
  const startTime = Math.floor(Date.now() / 1000) + 10;
  const endTime = startTime + 3600;

  console.log("开始时间:", startTime);
  console.log("结束时间:", endTime);

  const tx = await voting.createVoteSession(
    "测试投票",
    "这是一个测试投票",
    startTime,
    endTime
  );

  console.log("交易哈希:", tx.hash);

  const receipt = await tx.wait();
  console.log("交易状态:", receipt.status);

  expect(await voting.voteSessionCount()).to.equal(1);
});
```

### 4.6.2 测试失败分析

当测试失败时，检查以下内容：

1. **错误信息**: 查看 revert 原因
2. **状态检查**: 确认合约状态
3. **参数验证**: 检查输入参数
4. **时间问题**: 确认时间戳正确

## 4.7 持续集成

### 4.7.1 GitHub Actions

配置 GitHub Actions 运行测试：

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npx hardhat test
      - run: npx hardhat coverage
```

### 4.7.2 测试报告

生成测试报告：

```bash
npx hardhat test --reporter json > test-report.json
```

## 4.8 测试工具

### 4.8.1 Hardhat Network Helpers

使用 Hardhat Network Helpers 进行时间控制：

```typescript
import { time } from "@nomicfoundation/hardhat-network-helpers";

// 增加时间
await time.increase(3600); // 增加 1 小时

// 设置时间
await time.setNextBlockTimestamp(timestamp);
```

### 4.8.2 Chai Matchers

使用 Chai Matchers 进行断言：

```typescript
import { expect } from "chai";

// 相等断言
expect(value).to.equal(expected);

// 事件断言
await expect(tx).to.emit(contract, "EventName");

// Revert 断言
await expect(tx).to.be.revertedWith("Error message");
```

## 4.9 测试环境

### 4.9.1 本地测试环境

使用 Hardhat Network 进行本地测试：

```bash
npx hardhat node
npx hardhat test --network localhost
```

### 4.9.2 测试网络

使用测试网络进行集成测试：

```bash
npx hardhat test --network goerli
```

## 4.10 测试维护

### 4.10.1 测试更新

当合约代码更新时，同步更新测试：

1. 更新测试用例
2. 添加新测试
3. 删除过时测试

### 4.10.2 测试文档

为测试用例添加文档说明：

```typescript
/**
 * 测试创建投票活动功能
 * 验证：
 * 1. 成功创建投票活动
 * 2. 拒绝无效的时间参数
 * 3. 正确触发事件
 */
describe("创建投票活动", function () {
  // 测试代码
});
```
