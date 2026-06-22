/**
 * Interaction script - demonstrates how to interact with a deployed ERC20 contract.
 *
 * This script shows the core ERC20 operations:
 *   1. Check token info (name, symbol, totalSupply)
 *   2. Check balances
 *   3. Transfer tokens
 *   4. Approve and transferFrom
 *
 * Usage:
 *   # First, deploy the contract and get the address:
 *   npx hardhat run scripts/deploy-learning-token.js
 *
 *   # Then, set the CONTRACT_ADDRESS environment variable and run:
 *   CONTRACT_ADDRESS=0x... npx hardhat run scripts/interact.js
 */
import hre from "hardhat";

async function main() {
  const contractAddress = process.env.CONTRACT_ADDRESS;
  if (!contractAddress) {
    console.error("Please set CONTRACT_ADDRESS environment variable");
    process.exit(1);
  }

  // ⭐ In Hardhat 3, ethers is on the network connection
  const conn = await hre.network.getOrCreate();
  const { ethers } = conn;

  const [owner, addr1, addr2] = await ethers.getSigners();

  // Connect to the deployed contract
  const token = await ethers.getContractAt("LearningToken", contractAddress);

  console.log("=== Token Info ===");
  console.log("Name:", await token.name());
  console.log("Symbol:", await token.symbol());
  console.log("Decimals:", await token.decimals());
  console.log("Total Supply:", ethers.formatEther(await token.totalSupply()));

  console.log("\n=== Balances ===");
  console.log("Owner:", ethers.formatEther(await token.balanceOf(owner.address)));
  console.log("Addr1:", ethers.formatEther(await token.balanceOf(addr1.address)));
  console.log("Addr2:", ethers.formatEther(await token.balanceOf(addr2.address)));

  // Transfer tokens
  console.log("\n=== Transfer: Owner -> Addr1 (100 tokens) ===");
  const tx1 = await token.transfer(addr1.address, ethers.parseEther("100"));
  await tx1.wait();
  console.log("Addr1 balance:", ethers.formatEther(await token.balanceOf(addr1.address)));

  // Approve and TransferFrom
  console.log("\n=== Approve: Addr1 allows Addr2 to spend 50 tokens ===");
  const tx2 = await token.connect(addr1).approve(addr2.address, ethers.parseEther("50"));
  await tx2.wait();
  console.log(
    "Allowance (Addr1 -> Addr2):",
    ethers.formatEther(await token.allowance(addr1.address, addr2.address))
  );

  console.log("\n=== TransferFrom: Addr2 transfers 30 tokens from Addr1 to Addr2 ===");
  const tx3 = await token
    .connect(addr2)
    .transferFrom(addr1.address, addr2.address, ethers.parseEther("30"));
  await tx3.wait();

  console.log("\n=== Final Balances ===");
  console.log("Owner:", ethers.formatEther(await token.balanceOf(owner.address)));
  console.log("Addr1:", ethers.formatEther(await token.balanceOf(addr1.address)));
  console.log("Addr2:", ethers.formatEther(await token.balanceOf(addr2.address)));
  console.log(
    "Remaining Allowance (Addr1 -> Addr2):",
    ethers.formatEther(await token.allowance(addr1.address, addr2.address))
  );

  console.log("\nDone!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
