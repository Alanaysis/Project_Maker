# 05 - 开发指南

## 5.1 开发环境准备

### 5.1.1 系统要求

- Node.js >= 18.0.0
- npm >= 9.0.0
- Git

### 5.1.2 工具安装

```bash
# 安装 Node.js (推荐使用 nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# 安装 Git
# macOS
brew install git

# Ubuntu
sudo apt-get install git
```

### 5.1.3 项目克隆

```bash
git clone <repository-url>
cd decentralized-voting
```

## 5.2 项目结构

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
├── docs/              # 项目文档
└── package.json
```

## 5.3 开发流程

### 5.3.1 合约开发

1. **编写合约**
   ```bash
   # 编辑合约文件
   vim contracts/Voting.sol
   ```

2. **编译合约**
   ```bash
   npx hardhat compile
   ```

3. **运行测试**
   ```bash
   npx hardhat test
   ```

4. **部署合约**
   ```bash
   # 启动本地网络
   npx hardhat node

   # 部署合约
   npx hardhat run scripts/deploy.ts --network localhost
   ```

### 5.3.2 前端开发

1. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **配置环境**
   ```bash
   # 编辑环境配置
   vim .env.local
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```

4. **访问应用**
   打开浏览器访问 http://localhost:3000

## 5.4 常用命令

### 5.4.1 Hardhat 命令

```bash
# 编译合约
npx hardhat compile

# 运行测试
npx hardhat test

# 运行特定测试
npx hardhat test test/Voting.test.ts

# 启动本地网络
npx hardhat node

# 部署合约
npx hardhat run scripts/deploy.ts --network localhost

# 清理缓存
npx hardhat clean

# 查看帮助
npx hardhat help
```

### 5.4.2 前端命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start

# 运行 lint
npm run lint
```

## 5.5 开发规范

### 5.5.1 代码风格

- 使用 TypeScript
- 遵循 ESLint 规则
- 使用 Prettier 格式化代码

### 5.5.2 命名规范

- **合约**: PascalCase (如 `Voting`)
- **函数**: camelCase (如 `createVoteSession`)
- **变量**: camelCase (如 `voteSessionCount`)
- **常量**: UPPER_SNAKE_CASE (如 `VOTING_ABI`)
- **组件**: PascalCase (如 `WalletConnect`)

### 5.5.3 注释规范

```solidity
/**
 * @title Voting - 去中心化投票系统
 * @notice 实现投票创建、投票、计票和结果公示功能
 * @dev 使用 OpenZeppelin 的 Ownable 进行权限管理
 */
contract Voting {
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
        // 实现代码
    }
}
```

### 5.5.4 Git 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链更新

示例:
```
feat(voting): 添加投票功能

- 实现投票函数
- 添加防重复投票机制
- 更新测试用例

Closes #123
```

## 5.6 调试技巧

### 5.6.1 合约调试

1. **使用 console.log**
   ```solidity
   import "hardhat/console.sol";

   function createVoteSession(...) external returns (uint256 sessionId) {
       console.log("Creating vote session:", _title);
       // 实现代码
   }
   ```

2. **使用 Hardhat Network**
   ```bash
   # 启动详细日志
   npx hardhat node --verbose
   ```

3. **使用事件**
   ```solidity
   event Debug(string message, uint256 value);

   function vote(...) external {
       emit Debug("Vote count:", session.totalVotes);
       // 实现代码
   }
   ```

### 5.6.2 前端调试

1. **使用浏览器开发者工具**
   - 打开 Chrome DevTools
   - 查看 Console 输出
   - 检查 Network 请求

2. **使用 React DevTools**
   - 安装 React DevTools 扩展
   - 检查组件状态
   - 查看 props 传递

3. **使用 ethers.js 调试**
   ```typescript
   console.log("Provider:", provider);
   console.log("Signer:", signer);
   console.log("Contract:", contract);
   ```

## 5.7 常见问题

### 5.7.1 合约部署失败

**问题**: 合约部署失败，提示 Gas 不足

**解决方案**:
```bash
# 增加 Gas Limit
npx hardhat run scripts/deploy.ts --network localhost --gas-limit 10000000
```

### 5.7.2 前端连接钱包失败

**问题**: 前端无法连接 MetaMask 钱包

**解决方案**:
1. 确保 MetaMask 已安装
2. 确保 MetaMask 已解锁
3. 确保网络配置正确
4. 检查控制台错误信息

### 5.7.3 交易失败

**问题**: 交易失败，提示 revert

**解决方案**:
1. 检查交易参数
2. 检查合约状态
3. 检查用户权限
4. 查看错误信息

### 5.7.4 测试失败

**问题**: 测试用例失败

**解决方案**:
1. 检查测试数据
2. 检查时间控制
3. 检查断言逻辑
4. 查看错误堆栈

## 5.8 性能优化

### 5.8.1 合约优化

1. **存储优化**
   - 使用 `mapping` 替代数组
   - 打包存储变量

2. **计算优化**
   - 减少循环次数
   - 使用事件替代存储

3. **Gas 优化**
   - 使用 `calldata` 替代 `memory`
   - 批量操作

### 5.8.2 前端优化

1. **数据缓存**
   - 缓存投票活动数据
   - 避免重复请求

2. **懒加载**
   - 按需加载组件
   - 延迟加载数据

3. **错误边界**
   - 捕获组件错误
   - 显示降级 UI

## 5.9 安全考虑

### 5.9.1 合约安全

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

### 5.9.2 前端安全

1. **输入消毒**
   - 过滤特殊字符
   - 验证数据格式

2. **错误处理**
   - 捕获并处理异常
   - 显示友好错误信息

3. **状态验证**
   - 验证用户操作权限
   - 验证数据一致性

## 5.10 部署指南

### 5.10.1 本地部署

```bash
# 启动本地网络
npx hardhat node

# 部署合约
npx hardhat run scripts/deploy.ts --network localhost

# 更新前端配置
vim frontend/.env.local

# 启动前端
cd frontend
npm run dev
```

### 5.10.2 测试网络部署

```bash
# 配置网络
vim hardhat.config.ts

# 获取测试 ETH
# 访问水龙头网站

# 部署合约
npx hardhat run scripts/deploy.ts --network goerli

# 更新前端配置
vim frontend/.env.local

# 构建前端
cd frontend
npm run build

# 部署前端
# 使用 Vercel, Netlify 或其他服务
```

### 5.10.3 主网部署

```bash
# 配置主网网络
vim hardhat.config.ts

# 部署合约
npx hardhat run scripts/deploy.ts --network mainnet

# 更新前端配置
vim frontend/.env.local

# 构建前端
cd frontend
npm run build

# 部署前端
# 使用 Vercel, Netlify 或其他服务
```

## 5.11 维护指南

### 5.11.1 代码更新

1. **合约更新**
   - 修改合约代码
   - 运行测试
   - 部署新版本

2. **前端更新**
   - 修改前端代码
   - 运行测试
   - 构建并部署

### 5.11.2 依赖更新

```bash
# 更新根目录依赖
npm update

# 更新前端依赖
cd frontend
npm update
```

### 5.11.3 安全更新

1. **监控安全公告**
   - 关注 OpenZeppelin 安全公告
   - 关注 Hardhat 安全公告

2. **及时更新**
   - 更新依赖版本
   - 修复安全漏洞

## 5.12 社区资源

### 5.12.1 官方文档

- [Hardhat Documentation](https://hardhat.org/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [ethers.js Documentation](https://docs.ethers.org/)
- [OpenZeppelin Documentation](https://docs.openzeppelin.com/)

### 5.12.2 学习资源

- [Ethereum Development Documentation](https://ethereum.org/en/developers/docs/)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Web3.js Documentation](https://web3js.readthedocs.io/)

### 5.12.3 社区支持

- [Hardhat Discord](https://discord.gg/hardhat)
- [Next.js GitHub](https://github.com/vercel/next.js)
- [ethers.js GitHub](https://github.com/ethers-io/ethers.js)
