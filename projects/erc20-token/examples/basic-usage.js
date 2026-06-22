/**
 * Basic usage example - demonstrates the core ERC20 workflow.
 *
 * This example shows:
 *   1. Deploying a token
 *   2. Checking balances and supply
 *   3. Transferring tokens
 *   4. Using the approve/transferFrom pattern
 *
 * Run with:
 *   npx hardhat run examples/basic-usage.js
 */
import hre from "hardhat";

async function main() {
  // ⭐ In Hardhat 3, ethers is on the network connection
  const conn = await hre.network.getOrCreate();
  const { ethers } = conn;

  const [alice, bob, charlie] = await ethers.getSigners();

  console.log("=== Deploying LearningToken ===\n");

  const LearningToken = await ethers.getContractFactory("LearningToken");
  const token = await LearningToken.deploy("Demo Token", "DEMO", 18, 1000000);
  await token.waitForDeployment();

  const address = await token.getAddress();
  console.log("Token deployed at:", address);

  // --- Check initial state ---
  console.log("\n--- Initial State ---");
  console.log("Name:", await token.name());
  console.log("Symbol:", await token.symbol());
  console.log("Total Supply:", ethers.formatEther(await token.totalSupply()));

  const aliceBalance = await token.balanceOf(alice.address);
  console.log("Alice's balance:", ethers.formatEther(aliceBalance));

  // --- Transfer ---
  console.log("\n--- Alice transfers 1000 tokens to Bob ---");
  await (await token.transfer(bob.address, ethers.parseEther("1000"))).wait();

  console.log("Alice:", ethers.formatEther(await token.balanceOf(alice.address)));
  console.log("Bob:", ethers.formatEther(await token.balanceOf(bob.address)));

  // --- Approve + TransferFrom ---
  console.log("\n--- Bob approves Charlie to spend 500 tokens ---");
  await (await token.connect(bob).approve(charlie.address, ethers.parseEther("500"))).wait();

  console.log("Bob -> Charlie allowance:", ethers.formatEther(
    await token.allowance(bob.address, charlie.address)
  ));

  console.log("\n--- Charlie transfers 200 tokens from Bob to himself ---");
  await (await token.connect(charlie).transferFrom(
    bob.address,
    charlie.address,
    ethers.parseEther("200")
  )).wait();

  console.log("Bob:", ethers.formatEther(await token.balanceOf(bob.address)));
  console.log("Charlie:", ethers.formatEther(await token.balanceOf(charlie.address)));
  console.log("Remaining allowance:", ethers.formatEther(
    await token.allowance(bob.address, charlie.address)
  ));

  console.log("\n=== Example complete! ===");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
