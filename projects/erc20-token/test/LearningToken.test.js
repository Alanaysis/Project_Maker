import { expect } from "chai";
import hre from "hardhat";
import { parseEther } from "ethers";

describe("LearningToken", function () {
  let token;
  let owner, addr1, addr2;
  let ethers;

  const NAME = "Learning Token";
  const SYMBOL = "LT";
  const DECIMALS = 18;
  const INITIAL_SUPPLY = 1000000; // 1 million tokens

  beforeEach(async function () {
    // ⭐ In Hardhat 3, ethers is on the network connection, not hre directly
    const conn = await hre.network.getOrCreate();
    ethers = conn.ethers;

    [owner, addr1, addr2] = await ethers.getSigners();

    const LearningToken = await ethers.getContractFactory("LearningToken");
    token = await LearningToken.deploy(NAME, SYMBOL, DECIMALS, INITIAL_SUPPLY);
    await token.waitForDeployment();
  });

  // ============================================================
  //                       DEPLOYMENT TESTS
  // ============================================================

  describe("Deployment", function () {
    it("should set the correct name", async function () {
      expect(await token.name()).to.equal(NAME);
    });

    it("should set the correct symbol", async function () {
      expect(await token.symbol()).to.equal(SYMBOL);
    });

    it("should set the correct decimals", async function () {
      expect(await token.decimals()).to.equal(DECIMALS);
    });

    it("should mint the initial supply to the deployer", async function () {
      const expectedSupply = BigInt(INITIAL_SUPPLY) * 10n ** BigInt(DECIMALS);
      expect(await token.totalSupply()).to.equal(expectedSupply);
      expect(await token.balanceOf(owner.address)).to.equal(expectedSupply);
    });

    it("should set the correct totalSupply", async function () {
      const expectedSupply = BigInt(INITIAL_SUPPLY) * 10n ** BigInt(DECIMALS);
      expect(await token.totalSupply()).to.equal(expectedSupply);
    });
  });

  // ============================================================
  //                         TRANSFER TESTS
  // ============================================================

  describe("Transfer", function () {
    const amount = parseEther("100"); // 100 tokens

    it("should transfer tokens between accounts", async function () {
      await token.transfer(addr1.address, amount);
      expect(await token.balanceOf(addr1.address)).to.equal(amount);
    });

    it("should deduct from sender balance", async function () {
      const initialBalance = await token.balanceOf(owner.address);
      await token.transfer(addr1.address, amount);
      expect(await token.balanceOf(owner.address)).to.equal(initialBalance - amount);
    });

    it("should emit a Transfer event", async function () {
      await expect(token.transfer(addr1.address, amount))
        .to.emit(token, "Transfer")
        .withArgs(owner.address, addr1.address, amount);
    });

    it("should revert when sender has insufficient balance", async function () {
      const tooMuch = parseEther("999999999");
      await expect(
        token.connect(addr1).transfer(owner.address, tooMuch)
      ).to.be.revertedWith("LearningToken: insufficient balance");
    });

    it("should revert when transferring to the zero address", async function () {
      await expect(
        token.transfer(ethers.ZeroAddress, amount)
      ).to.be.revertedWith("LearningToken: transfer to the zero address");
    });

    it("should allow transferring zero tokens", async function () {
      const tx = await token.transfer(addr1.address, 0);
      const receipt = await tx.wait();
      expect(receipt.status).to.equal(1);
    });
  });

  // ============================================================
  //                        APPROVAL TESTS
  // ============================================================

  describe("Approval", function () {
    const amount = parseEther("500");

    it("should set the correct allowance", async function () {
      await token.approve(addr1.address, amount);
      expect(await token.allowance(owner.address, addr1.address)).to.equal(amount);
    });

    it("should emit an Approval event", async function () {
      await expect(token.approve(addr1.address, amount))
        .to.emit(token, "Approval")
        .withArgs(owner.address, addr1.address, amount);
    });

    it("should revert when approving the zero address", async function () {
      await expect(
        token.approve(ethers.ZeroAddress, amount)
      ).to.be.revertedWith("LearningToken: approve to the zero address");
    });

    it("should allow setting allowance to zero", async function () {
      await token.approve(addr1.address, amount);
      await token.approve(addr1.address, 0);
      expect(await token.allowance(owner.address, addr1.address)).to.equal(0);
    });

    it("should overwrite previous allowance", async function () {
      await token.approve(addr1.address, amount);
      await token.approve(addr1.address, parseEther("1000"));
      expect(await token.allowance(owner.address, addr1.address)).to.equal(
        parseEther("1000")
      );
    });
  });

  // ============================================================
  //                      TRANSFER_FROM TESTS
  // ============================================================

  describe("TransferFrom", function () {
    const approveAmount = parseEther("500");
    const transferAmount = parseEther("200");

    beforeEach(async function () {
      await token.approve(addr1.address, approveAmount);
    });

    it("should transfer tokens using allowance", async function () {
      await token.connect(addr1).transferFrom(owner.address, addr2.address, transferAmount);
      expect(await token.balanceOf(addr2.address)).to.equal(transferAmount);
    });

    it("should decrease the allowance", async function () {
      await token.connect(addr1).transferFrom(owner.address, addr2.address, transferAmount);
      expect(await token.allowance(owner.address, addr1.address)).to.equal(
        approveAmount - transferAmount
      );
    });

    it("should emit a Transfer event", async function () {
      await expect(
        token.connect(addr1).transferFrom(owner.address, addr2.address, transferAmount)
      )
        .to.emit(token, "Transfer")
        .withArgs(owner.address, addr2.address, transferAmount);
    });

    it("should revert when allowance is insufficient", async function () {
      const tooMuch = parseEther("999");
      await expect(
        token.connect(addr1).transferFrom(owner.address, addr2.address, tooMuch)
      ).to.be.revertedWith("LearningToken: insufficient allowance");
    });

    it("should revert when balance is insufficient", async function () {
      const bigAmount = parseEther("1");
      await token.connect(addr1).approve(addr1.address, bigAmount);
      await expect(
        token.connect(addr1).transferFrom(addr1.address, addr2.address, bigAmount)
      ).to.be.revertedWith("LearningToken: insufficient balance");
    });

    it("should skip allowance check for self-transfer", async function () {
      const selfTransfer = parseEther("100");
      const tx = await token.connect(owner).transferFrom(owner.address, addr2.address, selfTransfer);
      const receipt = await tx.wait();
      expect(receipt.status).to.equal(1);
    });
  });

  // ============================================================
  //                   INCREASE/DECREASE ALLOWANCE
  // ============================================================

  describe("IncreaseAllowance and DecreaseAllowance", function () {
    it("should increase allowance correctly", async function () {
      await token.approve(addr1.address, parseEther("100"));
      await token.increaseAllowance(addr1.address, parseEther("50"));
      expect(await token.allowance(owner.address, addr1.address)).to.equal(
        parseEther("150")
      );
    });

    it("should decrease allowance correctly", async function () {
      await token.approve(addr1.address, parseEther("100"));
      await token.decreaseAllowance(addr1.address, parseEther("30"));
      expect(await token.allowance(owner.address, addr1.address)).to.equal(
        parseEther("70")
      );
    });

    it("should revert decreaseAllowance below zero", async function () {
      await token.approve(addr1.address, parseEther("10"));
      await expect(
        token.decreaseAllowance(addr1.address, parseEther("20"))
      ).to.be.revertedWith("LearningToken: decreased allowance below zero");
    });

    it("should emit Approval event on increaseAllowance", async function () {
      await expect(token.increaseAllowance(addr1.address, parseEther("50")))
        .to.emit(token, "Approval");
    });
  });
});
