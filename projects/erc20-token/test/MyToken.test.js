import { expect } from "chai";
import hre from "hardhat";
import { parseEther } from "ethers";

describe("MyToken", function () {
  let token;
  let owner, addr1, addr2;
  let ethers;

  const INITIAL_SUPPLY = 1000000; // 1 million tokens

  beforeEach(async function () {
    // ⭐ In Hardhat 3, ethers is on the network connection, not hre directly
    const conn = await hre.network.getOrCreate();
    ethers = conn.ethers;

    [owner, addr1, addr2] = await ethers.getSigners();

    const MyToken = await ethers.getContractFactory("MyToken");
    token = await MyToken.deploy(INITIAL_SUPPLY);
    await token.waitForDeployment();
  });

  // ============================================================
  //                       DEPLOYMENT TESTS
  // ============================================================

  describe("Deployment", function () {
    it("should set the correct name", async function () {
      expect(await token.name()).to.equal("MyToken");
    });

    it("should set the correct symbol", async function () {
      expect(await token.symbol()).to.equal("MTK");
    });

    it("should mint the initial supply to the deployer", async function () {
      const expectedSupply = BigInt(INITIAL_SUPPLY) * 10n ** 18n;
      expect(await token.totalSupply()).to.equal(expectedSupply);
      expect(await token.balanceOf(owner.address)).to.equal(expectedSupply);
    });

    it("should set the deployer as owner", async function () {
      expect(await token.owner()).to.equal(owner.address);
    });
  });

  // ============================================================
  //                         BASIC ERC20
  // ============================================================

  describe("ERC20 Basics", function () {
    const amount = parseEther("100");

    it("should transfer tokens", async function () {
      await token.transfer(addr1.address, amount);
      expect(await token.balanceOf(addr1.address)).to.equal(amount);
    });

    it("should approve and transferFrom", async function () {
      await token.approve(addr1.address, amount);
      await token.connect(addr1).transferFrom(owner.address, addr2.address, amount);
      expect(await token.balanceOf(addr2.address)).to.equal(amount);
    });
  });

  // ============================================================
  //                           MINT
  // ============================================================

  describe("Mint", function () {
    it("should allow owner to mint", async function () {
      const mintAmount = parseEther("500");
      await token.mint(addr1.address, mintAmount);
      expect(await token.balanceOf(addr1.address)).to.equal(mintAmount);
    });

    it("should increase total supply on mint", async function () {
      const mintAmount = parseEther("500");
      const supplyBefore = await token.totalSupply();
      await token.mint(addr1.address, mintAmount);
      expect(await token.totalSupply()).to.equal(supplyBefore + mintAmount);
    });

    it("should revert if non-owner tries to mint", async function () {
      const mintAmount = parseEther("500");
      await expect(
        token.connect(addr1).mint(addr1.address, mintAmount)
      ).to.be.revertedWithCustomError(token, "OwnableUnauthorizedAccount");
    });
  });

  // ============================================================
  //                           BURN
  // ============================================================

  describe("Burn", function () {
    const burnAmount = parseEther("100");

    it("should allow holder to burn their tokens", async function () {
      const supplyBefore = await token.totalSupply();
      await token.burn(burnAmount);
      expect(await token.totalSupply()).to.equal(supplyBefore - burnAmount);
    });

    it("should decrease the burner's balance", async function () {
      const balanceBefore = await token.balanceOf(owner.address);
      await token.burn(burnAmount);
      expect(await token.balanceOf(owner.address)).to.equal(balanceBefore - burnAmount);
    });

    it("should revert if burning more than balance", async function () {
      const tooMuch = parseEther("999999999");
      await expect(
        token.connect(addr1).burn(tooMuch)
      ).to.be.revertedWithCustomError(token, "ERC20InsufficientBalance");
    });
  });
});
