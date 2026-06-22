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
