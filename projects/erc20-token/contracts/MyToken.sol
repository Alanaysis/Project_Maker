// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MyToken
 * @notice A production-ready ERC20 token built on OpenZeppelin.
 * @dev Demonstrates how to use OpenZeppelin's battle-tested contracts.
 *
 * Features:
 *   - Standard ERC20 (transfer, approve, transferFrom)
 *   - Burnable (holders can burn their own tokens)
 *   - Permit (EIP-2612 gasless approvals)
 *   - Ownable (only owner can mint new tokens)
 *
 * Why OpenZeppelin?
 *   - Audited by security professionals
 *   - Follows best practices
 *   - Saves development time
 *   - Reduces attack surface
 */
contract MyToken is ERC20, ERC20Burnable, ERC20Permit, Ownable {

    /**
     * @notice Creates the token and mints the initial supply to the deployer.
     * @param initialSupply The number of whole tokens to mint (will be multiplied by 10^18)
     */
    constructor(uint256 initialSupply)
        ERC20("MyToken", "MTK")
        ERC20Permit("MyToken")
        Ownable(msg.sender)
    {
        _mint(msg.sender, initialSupply * 10 ** decimals());
    }

    /**
     * @notice Mints new tokens. Only callable by the owner.
     * @param to     The address to mint tokens to
     * @param amount The amount to mint
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
