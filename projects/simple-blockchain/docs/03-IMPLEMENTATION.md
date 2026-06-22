# 03-IMPLEMENTATION.md - 核心功能实现

## 1. 区块结构实现

### 1.1 区块头结构
```go
type BlockHeader struct {
    Version       int32    // 版本号
    PrevBlockHash [32]byte // 前一区块哈希
    MerkleRoot    [32]byte // 默克尔树根
    Timestamp     int64    // 时间戳
    Difficulty    uint32   // 难度目标
    Nonce         uint64   // 随机数
}
```

### 1.2 区块结构
```go
type Block struct {
    Header       BlockHeader
    Transactions []*Transaction
    Hash         [32]byte
}
```

### 1.3 区块方法
- `NewBlock()`: 创建新区块
- `Hash()`: 计算区块哈希
- `Serialize()`: 序列化区块
- `Deserialize()`: 反序列化区块

## 2. 工作量证明实现

### 2.1 PoW 结构
```go
type ProofOfWork struct {
    Block     *Block
    Target    *big.Int
    Difficulty uint32
}
```

### 2.2 挖矿算法
```go
func (pow *ProofOfWork) Run() (uint64, [32]byte) {
    var hash [32]byte
    var nonce uint64 = 0

    for nonce < maxNonce {
        hash = pow.calculateHash(nonce)
        if pow.validateHash(hash) {
            return nonce, hash
        }
        nonce++
    }
    return 0, hash
}
```

### 2.3 难度调整
- 每 2016 个区块调整一次
- 根据出块时间调整难度
- 目标出块时间：10 分钟

## 3. 交易实现

### 3.1 交易结构
```go
type Transaction struct {
    ID        [32]byte
    Inputs    []*TxInput
    Outputs   []*TxOutput
    Timestamp int64
}
```

### 3.2 交易输入/输出
```go
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

### 3.3 交易流程
1. 创建交易
2. 签名交易
3. 验证交易
4. 广播交易

## 4. 钱包实现

### 4.1 钱包结构
```go
type Wallet struct {
    PrivateKey *ecdsa.PrivateKey
    PublicKey  []byte
    Address    string
}
```

### 4.2 地址生成
```go
func (w *Wallet) GenerateAddress() string {
    pubKeyHash := HashPublicKey(w.PublicKey)
    versionedPayload := append([]byte{version}, pubKeyHash...)
    checksum := checksum(versionedPayload)
    fullPayload := append(versionedPayload, checksum...)
    address := Base58Encode(fullPayload)
    return address
}
```

## 5. 网络实现

### 5.1 消息类型
```go
const (
    MsgVersion   = "version"
    MsgVerack    = "verack"
    MsgTx        = "tx"
    MsgBlock     = "block"
    MsgGetBlocks = "getblocks"
    MsgInv       = "inv"
)
```

### 5.2 节点通信
```go
type Node struct {
    Address    string
    Connection net.Conn
    Version    int32
}
```

### 5.3 广播机制
- 新交易广播到所有连接节点
- 新区块广播到所有连接节点
- 避免重复广播

## 6. 存储实现

### 6.1 文件存储
```go
type FileStorage struct {
    dataDir string
}

func (fs *FileStorage) SaveBlock(block *Block) error {
    data, err := block.Serialize()
    if err != nil {
        return err
    }
    filename := fmt.Sprintf("%x.dat", block.Hash)
    return os.WriteFile(filepath.Join(fs.dataDir, filename), data, 0644)
}
```

### 6.2 区块链状态
- 最新区块哈希
- 难度值
- UTXO 集合

## 7. 命令行界面

### 7.1 命令列表
```bash
# 创建钱包
blockchain createwallet

# 查询余额
blockchain getbalance -address <address>

# 发送交易
blockchain send -from <from> -to <to> -amount <amount>

# 挖矿
blockchain mine

# 打印区块链
blockchain printchain

# 启动节点
blockchain startnode -port <port>
```

### 7.2 命令实现
```go
func main() {
    switch os.Args[1] {
    case "createwallet":
        createWallet()
    case "getbalance":
        getBalance(os.Args[2])
    case "send":
        send(os.Args[2], os.Args[3], os.Args[4])
    case "mine":
        mine()
    case "printchain":
        printChain()
    case "startnode":
        startNode(os.Args[2])
    }
}
```
