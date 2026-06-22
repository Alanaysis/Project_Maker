// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title LearningToken
 * @notice A custom ERC20 token implementation built from scratch for learning purposes.
 * @dev This contract implements the ERC20 standard without using OpenZeppelin,
 *      so you can understand every line of the implementation.
 *
 * ERC20 Standard: https://eips.ethereum.org/EIPS/eip-20
 *
 * Key concepts demonstrated:
 *   1. State variables for balances and allowances
 *   2. Event emission for indexers and frontends
 *   3. Modifier pattern for access control
 *   4. Safe math (built into Solidity >=0.8.0)
 *   5. Return value convention (bool success)
 */
contract LearningToken {

    // ============================================================
    //                        STATE VARIABLES
    // ============================================================

    string public name;        // Token name, e.g. "Learning Token"
    string public symbol;      // Token symbol, e.g. "LT"
    uint8  public decimals;    // Number of decimal places (typically 18)
    uint256 public totalSupply;// Total supply of tokens

    // ⭐ KEY CONCEPT: Mapping for balances
    // address => amount of tokens held
    mapping(address => uint256) private _balances;

    // ⭐ KEY CONCEPT: Nested mapping for allowances
    // owner => (spender => amount allowed to spend)
    mapping(address => mapping(address => uint256)) private _allowances;

    // ============================================================
    //                            EVENTS
    // ============================================================

    /**
     * @notice Emitted when tokens are transferred.
     * @param from   The address sending tokens
     * @param to     The address receiving tokens
     * @param value  The amount of tokens transferred
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @notice Emitted when an approval is set.
     * @param owner    The address that owns the tokens
     * @param spender  The address approved to spend
     * @param value    The approved amount
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);

    // ============================================================
    //                          CONSTRUCTOR
    // ============================================================

    /**
     * @notice Creates the token and mints the initial supply to the deployer.
     * @param _name       The name of the token
     * @param _symbol     The symbol of the token
     * @param _decimals_  The number of decimals
     * @param _initialSupply The initial supply (in whole tokens, will be multiplied by 10^decimals)
     */
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _decimals_,
        uint256 _initialSupply
    ) {
        name = _name;
        symbol = _symbol;
        decimals = _decimals_;

        uint256 supply = _initialSupply * 10 ** uint256(_decimals_);
        totalSupply = supply;
        _balances[msg.sender] = supply;

        emit Transfer(address(0), msg.sender, supply);
    }

    // ============================================================
    //                     ERC20 CORE FUNCTIONS
    // ============================================================

    /**
     * @notice Returns the balance of the given address.
     * @param account The address to query
     * @return The token balance
     */
    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }

    /**
     * @notice Transfers `amount` tokens from the caller to `to`.
     * @dev This is the primary transfer function.
     *
     * ⭐ IMPORTANT: The function MUST:
     *   1. Check that the sender has enough balance
     *   2. Check for overflow (automatic in Solidity >=0.8.0)
     *   3. Check that `to` is not the zero address
     *   4. Emit a Transfer event
     *   5. Return true on success
     *
     * @param to     The recipient address
     * @param amount The amount to transfer
     * @return success True if the transfer succeeded
     */
    function transfer(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "LearningToken: transfer to the zero address");
        require(_balances[msg.sender] >= amount, "LearningToken: insufficient balance");

        // ⭐ Solidity 0.8+ reverts on overflow/underflow automatically,
        //    so we don't need SafeMath library.
        _balances[msg.sender] -= amount;
        _balances[to] += amount;

        emit Transfer(msg.sender, to, amount);
        return true;
    }

    /**
     * @notice Returns the remaining number of tokens that `spender` is allowed
     *         to spend on behalf of `owner`.
     * @param owner   The token owner
     * @param spender The approved spender
     * @return The remaining allowance
     */
    function allowance(address owner, address spender) public view returns (uint256) {
        return _allowances[owner][spender];
    }

    /**
     * @notice Approves `spender` to spend up to `amount` on behalf of the caller.
     *
     * ⭐ WHY APPROVALS? This enables the "approve + transferFrom" pattern:
     *   1. Owner calls approve(spender, amount)
     *   2. Spender calls transferFrom(owner, to, amount)
     *   This is essential for DEXes, payment channels, etc.
     *
     * @param spender The address authorized to spend
     * @param amount  The maximum amount they can spend
     * @return success True if the approval succeeded
     */
    function approve(address spender, uint256 amount) public returns (bool) {
        require(spender != address(0), "LearningToken: approve to the zero address");

        _allowances[msg.sender][spender] = amount;

        emit Approval(msg.sender, spender, amount);
        return true;
    }

    /**
     * @notice Transfers `amount` tokens from `from` to `to` using the allowance mechanism.
     *
     * ⭐ IMPORTANT: This function MUST:
     *   1. Check that `from` has enough balance
     *   2. Check that the caller has enough allowance
     *   3. Decrease the allowance
     *   4. Update balances
     *   5. Emit a Transfer event
     *
     * @param from   The address to transfer from
     * @param to     The recipient address
     * @param amount The amount to transfer
     * @return success True if the transfer succeeded
     */
    function transferFrom(address from, address to, uint256 amount) public returns (bool) {
        require(to != address(0), "LearningToken: transfer to the zero address");
        require(_balances[from] >= amount, "LearningToken: insufficient balance");

        // ⭐ Check and update allowance BEFORE the transfer.
        //    If msg.sender == from, skip the allowance check (self-transfer).
        if (msg.sender != from) {
            uint256 currentAllowance = _allowances[from][msg.sender];
            require(currentAllowance >= amount, "LearningToken: insufficient allowance");
            _allowances[from][msg.sender] = currentAllowance - amount;
        }

        _balances[from] -= amount;
        _balances[to] += amount;

        emit Transfer(from, to, amount);
        return true;
    }

    // ============================================================
    //                      ADDITIONAL FUNCTIONS
    // ============================================================

    /**
     * @notice Atomically increases the allowance granted to `spender` by `addedValue`.
     * @dev This is safer than calling approve directly because it avoids the
     *      "front-running" attack vector where a spender uses old allowance
     *      before a new approval is mined.
     *
     * @param spender     The address to increase allowance for
     * @param addedValue  The amount to increase the allowance by
     * @return success True if the increase succeeded
     */
    function increaseAllowance(address spender, uint256 addedValue) public returns (bool) {
        require(spender != address(0), "LearningToken: approve to the zero address");

        _allowances[msg.sender][spender] += addedValue;

        emit Approval(msg.sender, spender, _allowances[msg.sender][spender]);
        return true;
    }

    /**
     * @notice Atomically decreases the allowance granted to `spender` by `subtractedValue`.
     * @param spender        The address to decrease allowance for
     * @param subtractedValue The amount to decrease the allowance by
     * @return success True if the decrease succeeded
     */
    function decreaseAllowance(address spender, uint256 subtractedValue) public returns (bool) {
        require(spender != address(0), "LearningToken: approve to the zero address");

        uint256 currentAllowance = _allowances[msg.sender][spender];
        require(currentAllowance >= subtractedValue, "LearningToken: decreased allowance below zero");

        _allowances[msg.sender][spender] = currentAllowance - subtractedValue;

        emit Approval(msg.sender, spender, _allowances[msg.sender][spender]);
        return true;
    }
}
