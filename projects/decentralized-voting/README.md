# 去中心化投票系统

一个基于区块链的去中心化投票系统，使用 Solidity 智能合约和 Next.js 前端实现。

## 功能特性

- 创建投票活动
- 添加投票提案
- 用户进行投票
- 计票统计
- 结果公示

## 技术栈

- **智能合约**: Solidity, Hardhat
- **前端**: Next.js, TypeScript, Tailwind CSS
- **区块链交互**: ethers.js
- **开发工具**: Hardhat, OpenZeppelin

## 项目结构

```
decentralized-voting/
├── contracts/          # 智能合约
│   └── Voting.sol     # 投票合约
├── frontend/          # 前端应用
│   ├── src/
│   │   ├── app/      # Next.js 页面
│   │   ├── components/ # React 组件
│   │   ├── hooks/    # 自定义 Hooks
│   │   └── lib/      # 工具函数
│   └── ...
├── test/              # 测试文件
├── scripts/           # 部署脚本
└── docs/              # 项目文档
```

## 快速开始

### 1. 安装依赖

```bash
# 安装根目录依赖
npm install

# 安装前端依赖
cd frontend
npm install
```

### 2. 启动本地区块链

```bash
npx hardhat node
```

### 3. 部署合约

```bash
npx hardhat run scripts/deploy.ts --network localhost
```

### 4. 更新前端配置

将部署的合约地址更新到 `frontend/.env.local` 文件中。

### 5. 启动前端

```bash
cd frontend
npm run dev
```

## 测试

```bash
npx hardhat test
```

## 文档

详细文档请参考 `docs/` 目录：

- [01-RESEARCH.md](docs/01-RESEARCH.md) - 市场调研
- [02-ARCHITECTURE.md](docs/02-ARCHITECTURE.md) - 架构设计
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试说明
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发指南

## 许可证

MIT License
