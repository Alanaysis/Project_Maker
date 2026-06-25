# 去中心化投票系统

一个基于区块链的去中心化投票系统，支持 Solidity 智能合约和 Python 实现两种方案。

## 功能特性

- 创建投票活动
- 添加投票提案
- 用户进行投票
- 计票统计
- 结果公示
- 身份验证
- 一人一票保证
- 审计追踪

## 技术栈

### 方案一：Solidity + Next.js（链上投票）

- **智能合约**: Solidity, Hardhat
- **前端**: Next.js, TypeScript, Tailwind CSS
- **区块链交互**: ethers.js
- **开发工具**: Hardhat, OpenZeppelin

### 方案二：Python 实现（本地/教学用途）

- **核心语言**: Python 3.9+
- **区块链**: 自实现简化区块链
- **测试框架**: pytest
- **数据结构**: dataclasses

## 项目结构

```
decentralized-voting/
├── contracts/              # Solidity 智能合约
│   └── Voting.sol         # 投票合约
├── frontend/              # Next.js 前端应用
├── python/                # Python 实现
│   ├── src/              # 源代码
│   │   ├── blockchain.py # 区块链模块
│   │   ├── voting.py     # 投票模块
│   │   ├── identity.py   # 身份模块
│   │   ├── consensus.py  # 规则模块
│   │   └── transparency.py # 透明性模块
│   ├── tests/            # 测试代码
│   ├── examples/         # 示例代码
│   └── docs/             # 文档
├── test/                  # Solidity 测试
├── scripts/               # 部署脚本
└── docs/                  # 项目文档
```

## 快速开始

### 方案一：Solidity + Next.js

#### 1. 安装依赖

```bash
# 安装根目录依赖
npm install

# 安装前端依赖
cd frontend
npm install
```

#### 2. 启动本地区块链

```bash
npx hardhat node
```

#### 3. 部署合约

```bash
npx hardhat run scripts/deploy.ts --network localhost
```

#### 4. 更新前端配置

将部署的合约地址更新到 `frontend/.env.local` 文件中。

#### 5. 启动前端

```bash
cd frontend
npm run dev
```

### 方案二：Python 实现

#### 1. 安装依赖

```bash
cd python
pip install -r requirements.txt
```

#### 2. 运行示例

```bash
# 基本投票示例
python examples/basic_voting.py

# DAO 投票示例
python examples/dao_voting.py

# 社区治理示例
python examples/community_governance.py
```

#### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=src --cov-report=term-missing

# 运行特定模块测试
pytest tests/test_voting.py
```

## 测试

### Solidity 测试

```bash
npx hardhat test
```

### Python 测试

```bash
cd python
pytest --cov=src
```

## 文档

### Solidity 文档

详细文档请参考 `docs/` 目录：

- [01-RESEARCH.md](docs/01-RESEARCH.md) - 市场调研
- [02-ARCHITECTURE.md](docs/02-ARCHITECTURE.md) - 架构设计
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试说明
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发指南

### Python 文档

详细文档请参考 `python/docs/` 目录：

- [01_RESEARCH.md](python/docs/01_RESEARCH.md) - 市场调研
- [02_ARCHITECTURE.md](python/docs/02_ARCHITECTURE.md) - 架构设计
- [03_IMPLEMENTATION.md](python/docs/03_IMPLEMENTATION.md) - 实现细节
- [04_TESTING.md](python/docs/04_TESTING.md) - 测试说明
- [05_DEVELOPMENT.md](python/docs/05_DEVELOPMENT.md) - 开发指南

## 许可证

MIT License
