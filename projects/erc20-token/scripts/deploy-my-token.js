/**
 * Deployment script for MyToken (OpenZeppelin-based ERC20)
 *
 * Usage:
 *   npx hardhat run scripts/deploy-my-token.js
 *   npx hardhat run scripts/deploy-my-token.js --network sepolia
 */
import hre from "hardhat";

async function main() {
  console.log("Deploying MyToken...");

  // ⭐ In Hardhat 3, ethers is on the network connection
  const conn = await hre.network.getOrCreate();
  const { ethers } = conn;

  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  const MyToken = await ethers.getContractFactory("MyToken");
  const token = await MyToken.deploy(1000000); // 1 million tokens

  await token.waitForDeployment();
  const address = await token.getAddress();

  console.log("MyToken deployed to:", address);
  console.log("Token name:", await token.name());
  console.log("Token symbol:", await token.symbol());
  console.log("Total supply:", ethers.formatEther(await token.totalSupply()), "MTK");
  console.log("Owner:", await token.owner());

  // Verify on Etherscan (if on a public network)
  if (conn.networkName !== "default" && conn.networkName !== "hardhat" && conn.networkName !== "localhost") {
    console.log("Waiting for block confirmations...");
    await token.deploymentTransaction().wait(5);

    try {
      await hre.run("verify:verify", {
        address: address,
        constructorArguments: [1000000],
      });
      console.log("Contract verified on Etherscan!");
    } catch (error) {
      console.log("Verification failed:", error.message);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
