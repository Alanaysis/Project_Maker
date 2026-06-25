# Simple Blockchain - 简易区块链实现

A complete blockchain implementation in Go, featuring Proof of Work consensus, UTXO transaction model, ECDSA wallets, and P2P networking.

## Features

### Core Blockchain
- **Block Structure**: Version, prev hash, merkle root, timestamp, difficulty, nonce
- **Chain Management**: Genesis block, block validation, longest chain rule
- **Merkle Tree**: Efficient transaction verification
- **Persistence**: Save/load blockchain to disk

### Consensus
- **Proof of Work (PoW)**: SHA-256 based mining
- **Difficulty Adjustment**: Dynamic difficulty based on block time
- **Target Calculation**: Leading zero bits requirement

### Transactions
- **UTXO Model**: Unspent Transaction Output tracking
- **Coinbase Transactions**: Mining rewards
- **Transaction Verification**: Signature validation
- **Transaction Pool**: Mempool for pending transactions

### Wallet
- **ECDSA Keys**: P-256 elliptic curve cryptography
- **Address Generation**: SHA-256 based addresses
- **Digital Signatures**: Transaction signing and verification
- **Wallet Persistence**: Save/load wallets to disk

### P2P Network
- **Node Discovery**: Connect to peer nodes
- **Message Protocol**: Version, Verack, Tx, Block, GetBlocks, Inv
- **Block Broadcasting**: Propagate new blocks
- **Transaction Broadcasting**: Propagate new transactions

### Storage
- **File-based Storage**: Block and transaction persistence
- **Blockchain Serialization**: Custom binary format
- **Data Directory Management**: Organized data storage

## Project Structure

```
simple-blockchain/
├── main.go                 # CLI entry point
├── block.go                # Block structure and operations
├── blockchain.go           # Chain management
├── transaction.go          # Transaction processing
├── mempool.go              # Transaction memory pool
├── pow.go                  # Proof of Work consensus
├── wallet.go               # Wallet and key management
├── network.go              # P2P networking
├── crypto.go               # Cryptographic utilities
├── storage.go              # Storage engine
├── utils.go                # Helper functions
├── *_test.go               # Unit tests (68 tests)
├── tests/
│   └── integration_test.sh # Integration tests
├── examples/
│   ├── explorer.go         # Blockchain explorer
│   └── cryptocurrency.go   # Complete cryptocurrency demo
├── docs/
│   ├── 01-RESEARCH.md      # Technology research
│   ├── 02-ARCHITECTURE.md  # Architecture design
│   ├── 03-IMPLEMENTATION.md # Implementation details
│   ├── 04-TESTING.md       # Testing strategy
│   └── 05-DEVELOPMENT.md   # Development guide
├── go.mod                  # Go module definition
├── README.md               # This file
└── LEARNING_NOTES.md       # Learning notes
```

## Quick Start

### Prerequisites

- Go 1.21+
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd simple-blockchain

# Build the project
go build -o blockchain .
```

### Basic Usage

```bash
# Create a wallet
./blockchain createwallet

# List wallet addresses
./blockchain listaddresses

# Mine a block
./blockchain mine

# Check balance
./blockchain getbalance -address <address>

# Send coins
./blockchain send -from <from> -to <to> -amount <amount>

# Print the blockchain
./blockchain printchain

# Start a P2P node
./blockchain startnode -port 3000
```

### Run Examples

```bash
# Blockchain explorer
go run examples/explorer.go blocks
go run examples/explorer.go block 0
go run examples/explorer.go stats

# Cryptocurrency demo
go run examples/cryptocurrency.go
```

## Core Concepts

### Block Structure

```go
type Block struct {
    Header       BlockHeader
    Transactions []*Transaction
    Hash         [32]byte
}

type BlockHeader struct {
    Version       int32
    PrevBlockHash [32]byte
    MerkleRoot    [32]byte
    Timestamp     int64
    Difficulty    uint32
    Nonce         uint64
}
```

### Transaction Model (UTXO)

```go
type Transaction struct {
    ID        [32]byte
    Inputs    []*TxInput
    Outputs   []*TxOutput
    Timestamp int64
}

type TxInput struct {
    TxID      [32]byte
    OutIndex  int
    Signature []byte
    PubKey    []byte
}

type TxOutput struct {
    Value      float64
    PubKeyHash []byte
}
```

### Proof of Work

```go
type ProofOfWork struct {
    Block      *Block
    Target     *big.Int
    Difficulty uint32
}
```

The mining process finds a nonce such that:
```
SHA256(block_header + nonce) < target
```

### Wallet

```go
type Wallet struct {
    PrivateKey *ecdsa.PrivateKey
    PublicKey  []byte
    Address    string
}
```

Address generation:
1. Generate ECDSA key pair
2. Hash public key with SHA-256
3. Take first 20 bytes as address

## Testing

### Run All Tests

```bash
go test -v ./...
```

### Run Specific Tests

```bash
# Test block operations
go test -run TestBlock ./...

# Test blockchain
go test -run TestBlockchain ./...

# Test transactions
go test -run TestTransaction ./...

# Test Proof of Work
go test -run TestProofOfWork ./...

# Test wallet
go test -run TestWallet ./...
```

### Integration Tests

```bash
bash tests/integration_test.sh
```

### Test Coverage

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
├─────────────────────────────────────────────────────────────┤
│                      Business Logic                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Wallet  │  │   Tx     │  │  Block   │  │ Network  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                      Core Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Crypto  │  │   PoW    │  │ Storage  │  │   P2P    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                      Infrastructure                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Config  │  │   Log    │  │  Utils   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Transaction Flow
```
User creates transaction
    ↓
Wallet signs transaction
    ↓
Transaction verified
    ↓
Added to mempool
    ↓
Broadcast to network
    ↓
Miner picks from mempool
    ↓
Included in new block
    ↓
Block broadcast to network
    ↓
Nodes validate and add block
```

### Mining Flow
```
Get pending transactions
    ↓
Create block header
    ↓
Calculate merkle root
    ↓
Set timestamp and difficulty
    ↓
Loop: try different nonces
    ↓
Find valid hash (meets target)
    ↓
Create complete block
    ↓
Broadcast block
```

## Security Features

- **Hash Integrity**: SHA-256 for all hashing
- **Digital Signatures**: ECDSA for transaction signing
- **Chain Validation**: Verify entire blockchain integrity
- **Double-Spend Prevention**: UTXO model prevents spending same coins twice
- **Proof of Work**: Computational cost prevents spam and attacks

## API Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| `createwallet` | Create a new wallet |
| `listaddresses` | List all wallet addresses |
| `getbalance -address <addr>` | Get balance of an address |
| `send -from <addr> -to <addr> -amount <amt>` | Send coins |
| `mine` | Mine a new block |
| `printchain` | Print the blockchain |
| `startnode -port <port>` | Start a P2P node |
| `reindexutxo` | Reindex UTXO set |

### Explorer Commands

| Command | Description |
|---------|-------------|
| `blocks` | List all blocks |
| `block <height>` | Show block at height |
| `tx <id>` | Show transaction by ID |
| `stats` | Show chain statistics |
| `search <query>` | Search blocks or transactions |

## Development

### Build

```bash
go build -o blockchain .
```

### Run Tests

```bash
go test -v ./...
```

### Code Quality

```bash
go vet ./...
gofmt -w .
```

## Learning Resources

- [Bitcoin Wiki](https://en.bitcoin.it/wiki/Main_Page)
- [Mastering Bitcoin](https://github.com/bitcoinbook/bitcoinbook)
- [Go Documentation](https://go.dev/doc/)
- [Cryptography Standards](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)

## References

- [go-ethereum](https://github.com/ethereum/go-ethereum)
- [bitcoinbook](https://github.com/bitcoinbook/bitcoinbook)
- [blockchain-tutorial](https://github.com/liuchengxu/blockchain-tutorial)

## Documentation

- [Technology Research](docs/01-RESEARCH.md)
- [Architecture Design](docs/02-ARCHITECTURE.md)
- [Implementation Details](docs/03-IMPLEMENTATION.md)
- [Testing Strategy](docs/04-TESTING.md)
- [Development Guide](docs/05-DEVELOPMENT.md)
- [Learning Notes](LEARNING_NOTES.md)

## License

MIT License
