# 技术设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│                    (SQL Interface)                           │
├─────────────────────────────────────────────────────────────┤
│                      SQL Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Tokenizer│→ │  Parser  │→ │   AST    │→ │ Planner  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                   Optimizer Layer                            │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Rule-based Optimizer (RBO)                │      │
│  │  - Predicate Pushdown  - Constant Folding        │      │
│  │  - Projection Elimination                        │      │
│  └──────────────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                   Execution Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  SeqScan │  │  Insert  │  │  Update  │  │  Delete  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │  Filter  │  │  Project │                                │
│  └──────────┘  └──────────┘                                │
├─────────────────────────────────────────────────────────────┤
│                   Storage Layer                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │              Buffer Pool Manager                  │      │
│  │         (LRU Replacement Policy)                  │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │
│  │ B+ Tree  │  │  Table   │  │   Concurrency        │     │
│  │  Index   │  │  Heap    │  │   Manager            │     │
│  └──────────┘  └──────────┘  └──────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                      Disk Layer                              │
│              ┌──────────────────────┐                       │
│              │    Disk Manager      │                       │
│              │   (File I/O)         │                       │
│              └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 关键类 |
|------|------|--------|
| SQL Layer | 解析 SQL 语句 | Tokenizer, Parser, AST |
| Optimizer | 优化执行计划 | RuleOptimizer |
| Execution | 执行查询计划 | Executor, SeqScanExecutor |
| Storage | 数据存储管理 | BufferPool, BPlusTree |
| Concurrency | 并发控制 | LockManager, Transaction |
| Disk | 磁盘 I/O | DiskManager |

## 2. 核心数据结构

### 2.1 页面布局

```
┌─────────────────────────────────────────────┐
│                Page (4KB)                     │
├─────────────────────────────────────────────┤
│  Header (16 bytes)                           │
│  ┌─────────┬─────────┬─────────┬─────────┐  │
│  │ Page ID │  LSN    │  Type   │  Count  │  │
│  │ (4B)    │  (4B)   │  (2B)   │  (2B)   │  │
│  └─────────┴─────────┴─────────┴─────────┘  │
├─────────────────────────────────────────────┤
│  Free Space                                 │
├─────────────────────────────────────────────┤
│  Slot Directory                             │
│  ┌─────────┬─────────┬─────────┬─────────┐  │
│  │ Slot 0  │ Slot 1  │  ...    │ Slot N  │  │
│  │ Offset  │ Offset  │         │ Offset  │  │
│  └─────────┴─────────┴─────────┴─────────┘  │
└─────────────────────────────────────────────┘
```

### 2.2 B+ 树节点布局

**内部节点**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Internal Node                              │
├─────────────────────────────────────────────────────────────┤
│  Header: [is_leaf=false, key_count, parent_page_id]         │
├─────────────────────────────────────────────────────────────┤
│  Keys:    [key0] [key1] [key2] ... [keyN]                   │
├─────────────────────────────────────────────────────────────┤
│  Children:[page0] [page1] [page2] ... [pageN] [pageN+1]    │
└─────────────────────────────────────────────────────────────┘
```

**叶子节点**:
```
┌─────────────────────────────────────────────────────────────┐
│                     Leaf Node                                │
├─────────────────────────────────────────────────────────────┤
│  Header: [is_leaf=true, key_count, parent_page_id, next]    │
├─────────────────────────────────────────────────────────────┤
│  Keys:    [key0] [key1] [key2] ... [keyN]                   │
├─────────────────────────────────────────────────────────────┤
│  Values:  [val0] [val1] [val2] ... [valN]                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 数据行格式

```
┌─────────────────────────────────────────────────────────────┐
│                      Row Format                              │
├─────────────────────────────────────────────────────────────┤
│  Header (4 bytes)                                            │
│  ┌─────────────────────────────────────┐                    │
│  │ Null Bitmap (1B) │ Row Size (3B)    │                    │
│  └─────────────────────────────────────┘                    │
├─────────────────────────────────────────────────────────────┤
│  Data                                                        │
│  ┌─────────┬─────────┬─────────┬─────────┐                  │
│  │ Col 0   │ Col 1   │ Col 2   │ Col N   │                  │
│  │ (fixed) │ (var)   │ (fixed) │ (var)   │                  │
│  └─────────┴─────────┴─────────┴─────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 3. 核心接口设计

### 3.1 SQL 解析器

```cpp
// Token 类型
enum class TokenType {
    // 字面量
    INTEGER, FLOAT, STRING, IDENTIFIER,
    // 关键字
    SELECT, FROM, WHERE, INSERT, INTO, VALUES,
    CREATE, TABLE, UPDATE, SET, DELETE,
    INT_TYPE, VARCHAR_TYPE, FLOAT_TYPE,
    // 运算符
    PLUS, MINUS, MULTIPLY, DIVIDE,
    EQUAL, NOT_EQUAL, LESS, GREATER,
    LESS_EQUAL, GREATER_EQUAL,
    // 分隔符
    COMMA, SEMICOLON, LPAREN, RPAREN,
    // 特殊
    STAR, EOF_TOKEN, INVALID
};

// Token
struct Token {
    TokenType type;
    std::string value;
    int line;
    int column;
};

// 词法分析器
class Tokenizer {
public:
    explicit Tokenizer(const std::string& sql);
    std::vector<Token> tokenize();
    Token nextToken();
    bool hasNext() const;
private:
    std::string sql_;
    size_t pos_;
    int line_;
    int column_;
};

// AST 节点类型
enum class StatementType {
    CREATE_TABLE,
    INSERT,
    SELECT,
    UPDATE,
    DELETE
};

// AST 基类
class Statement {
public:
    virtual ~Statement() = default;
    virtual StatementType type() const = 0;
};

// SELECT 语句 AST
class SelectStatement : public Statement {
public:
    StatementType type() const override { return StatementType::SELECT; }

    std::vector<std::string> columns;  // * 表示所有列
    std::string table_name;
    std::unique_ptr<Expression> where_clause;
    std::vector<std::string> order_by;
    int limit = -1;
};

// 语法分析器
class Parser {
public:
    explicit Parser(const std::vector<Token>& tokens);
    std::unique_ptr<Statement> parse();
private:
    std::unique_ptr<Statement> parseCreateTable();
    std::unique_ptr<Statement> parseInsert();
    std::unique_ptr<Statement> parseSelect();
    std::unique_ptr<Statement> parseUpdate();
    std::unique_ptr<Statement> parseDelete();
    std::unique_ptr<Expression> parseExpression();
};
```

### 3.2 存储引擎

```cpp
// 页面 ID
using page_id_t = int32_t;
constexpr page_id_t INVALID_PAGE_ID = -1;

// 磁盘管理器
class DiskManager {
public:
    explicit DiskManager(const std::string& db_file);
    ~DiskManager();

    void readPage(page_id_t page_id, char* page_data);
    void writePage(page_id_t page_id, const char* page_data);
    page_id_t allocatePage();
    void deallocatePage(page_id_t page_id);

private:
    std::fstream db_io_;
    std::string db_file_;
    std::atomic<page_id_t> next_page_id_{0};
};

// 缓冲池管理器
class BufferPoolManager {
public:
    BufferPoolManager(size_t pool_size, DiskManager* disk_manager);

    Page* fetchPage(page_id_t page_id);
    bool unpinPage(page_id_t page_id, bool is_dirty);
    bool flushPage(page_id_t page_id);
    Page* newPage(page_id_t* page_id);
    bool deletePage(page_id_t page_id);

private:
    size_t pool_size_;
    std::vector<Page> pages_;
    std::unordered_map<page_id_t, size_t> page_table_;
    std::list<page_id_t> free_list_;
    std::unique_ptr<Replacer> replacer_;
    std::mutex latch_;
    DiskManager* disk_manager_;
};

// B+ 树
class BPlusTree {
public:
    BPlusTree(BufferPoolManager* bpm, const std::string& name,
              const KeyComparator& comparator);

    bool insert(const KeyType& key, const ValueType& value);
    bool remove(const KeyType& key);
    bool search(const KeyType& key, ValueType* result);
    std::vector<ValueType> rangeQuery(const KeyType& start, const KeyType& end);

private:
    Page* findLeafPage(const KeyType& key);
    void splitLeaf(Page* leaf_page);
    void splitInternal(Page* internal_page);

    BufferPoolManager* bpm_;
    std::string name_;
    page_id_t root_page_id_;
    KeyComparator comparator_;
    std::mutex root_latch_;
};
```

### 3.3 查询执行器

```cpp
// 执行器上下文
class ExecutorContext {
public:
    ExecutorContext(BufferPoolManager* bpm, Catalog* catalog,
                   Transaction* txn);

    BufferPoolManager* getBufferPoolManager();
    Catalog* getCatalog();
    Transaction* getTransaction();
};

// 执行器基类 (Volcano 模型)
class AbstractExecutor {
public:
    explicit AbstractExecutor(ExecutorContext* exec_ctx);
    virtual ~AbstractExecutor() = default;

    virtual void init() = 0;
    virtual bool next(Row* row) = 0;

protected:
    ExecutorContext* exec_ctx_;
};

// 顺序扫描执行器
class SeqScanExecutor : public AbstractExecutor {
public:
    SeqScanExecutor(ExecutorContext* ctx, const SeqScanPlan* plan);

    void init() override;
    bool next(Row* row) override;

private:
    const SeqScanPlan* plan_;
    TableIterator* iterator_;
};

// 插入执行器
class InsertExecutor : public AbstractExecutor {
public:
    InsertExecutor(ExecutorContext* ctx, const InsertPlan* plan);

    void init() override;
    bool next(Row* row) override;

private:
    const InsertPlan* plan_;
    bool done_;
};

// 过滤执行器
class FilterExecutor : public AbstractExecutor {
public:
    FilterExecutor(ExecutorContext* ctx, const FilterPlan* plan,
                   std::unique_ptr<AbstractExecutor> child);

    void init() override;
    bool next(Row* row) override;

private:
    const FilterPlan* plan_;
    std::unique_ptr<AbstractExecutor> child_;
};
```

### 3.4 并发控制

```cpp
// 锁模式
enum class LockMode {
    SHARED,
    EXCLUSIVE
};

// 事务状态
enum class TransactionState {
    GROWING,
    SHRINKING,
    COMMITTED,
    ABORTED
};

// 事务
class Transaction {
public:
    Transaction(transaction_id_t txn_id);

    transaction_id_t getTransactionId() const;
    TransactionState getState() const;
    void setState(TransactionState state);

    void addLockedResource(const std::string& resource);

private:
    transaction_id_t txn_id_;
    TransactionState state_;
    std::set<std::string> locked_resources_;
    std::mutex latch_;
};

// 锁管理器
class LockManager {
public:
    LockManager() = default;

    bool lockShared(Transaction* txn, const std::string& resource);
    bool lockExclusive(Transaction* txn, const std::string& resource);
    bool unlock(Transaction* txn, const std::string& resource);

private:
    struct LockRequest {
        transaction_id_t txn_id;
        LockMode mode;
        bool granted;
    };

    struct LockRequestQueue {
        std::list<LockRequest> request_queue;
        bool upgrading = false;
        std::mutex mutex;
        std::condition_variable cv;
    };

    std::unordered_map<std::string, std::shared_ptr<LockRequestQueue>> lock_table_;
    std::mutex lock_table_latch_;
};
```

## 4. 查询处理流程

### 4.1 完整流程

```
SQL Input
    │
    ▼
┌──────────────┐
│  Tokenizer   │  "SELECT * FROM users WHERE id = 1"
└──────┬───────┘
       │ Tokens
       ▼
┌──────────────┐
│    Parser    │  → AST
└──────┬───────┘
       │ AST
       ▼
┌──────────────┐
│   Planner    │  → Logical Plan
└──────┬───────┘
       │ Logical Plan
       ▼
┌──────────────┐
│  Optimizer   │  → Physical Plan
└──────┬───────┘
       │ Physical Plan
       ▼
┌──────────────┐
│  Executor    │  → Result Set
└──────────────┘
```

### 4.2 执行计划示例

```sql
SELECT name, age FROM users WHERE age > 20 ORDER BY name;
```

**逻辑计划**:
```
Projection(name, age)
    └── Filter(age > 20)
        └── Sort(name)
            └── SeqScan(users)
```

**物理计划**:
```
ProjectionExecutor
    └── FilterExecutor (age > 20)
        └── SortExecutor (name ASC)
            └── SeqScanExecutor (users)
```

## 5. 存储引擎设计

### 5.1 页面管理

```
Page Layout:
┌─────────────────────────────────────────────┐
│  Page Header (16 bytes)                      │
│  ┌─────────┬─────────┬─────────┬──────────┐ │
│  │ page_id │   lsn   │  type   │  count   │ │
│  │  (4B)   │  (4B)   │  (2B)   │  (2B)   │ │
│  ├─────────┴─────────┴─────────┴──────────┤ │
│  │  free_space_offset (2B) │  unused (2B)│ │
│  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│                 Data Area                    │
├─────────────────────────────────────────────┤
│               Slot Directory                 │
│  ┌─────────┬─────────┬─────────┬─────────┐  │
│  │ Slot 0  │ Slot 1  │  ...    │ Slot N  │  │
│  │offset   │offset   │         │offset   │  │
│  │size     │size     │         │size     │  │
│  └─────────┴─────────┴─────────┴─────────┘  │
└─────────────────────────────────────────────┘
```

### 5.2 缓冲池管理

**LRU 替换策略**:
```
Cache Miss
    │
    ▼
┌──────────────┐
│ Free Frame?  │──Yes──→ Load Page
└──────┬───────┘
       │ No
       ▼
┌──────────────┐
│ Evict LRU    │
│ (unpinned)   │
└──────┬───────┘
       │
       ▼
   Load Page
```

### 5.3 B+ 树操作

**插入流程**:
```
Insert(key, value)
    │
    ▼
Find Leaf Node
    │
    ▼
Space in Leaf? ──Yes──→ Insert
    │
    │ No
    ▼
Split Leaf
    │
    ▼
Insert into Parent
    │
    ▼
Parent Full? ──Yes──→ Split Parent (递归)
    │
    │ No
    ▼
Done
```

## 6. 并发控制设计

### 6.1 锁协议

**简化 2PL (Two-Phase Locking)**:
- Growing Phase: 获取锁
- Shrinking Phase: 释放锁
- 事务结束时释放所有锁

### 6.2 锁兼容矩阵

| | S | X |
|---|---|---|
| **S** | ✓ | ✗ |
| **X** | ✗ | ✗ |

### 6.3 死锁预防

使用 Wait-Die 策略:
- 年轻事务等待年长事务 → 等待
- 年长事务等待年轻事务 → 回滚（die）

## 7. 错误处理

```cpp
enum class ErrorCode {
    SUCCESS = 0,
    SYNTAX_ERROR,
    TABLE_NOT_FOUND,
    COLUMN_NOT_FOUND,
    DUPLICATE_KEY,
    KEY_NOT_FOUND,
    PAGE_FULL,
    BUFFER_FULL,
    DEADLOCK,
    IO_ERROR,
    UNKNOWN
};

class Status {
public:
    Status() : code_(ErrorCode::SUCCESS) {}
    Status(ErrorCode code, const std::string& message)
        : code_(code), message_(message) {}

    bool ok() const { return code_ == ErrorCode::SUCCESS; }
    ErrorCode code() const { return code_; }
    std::string message() const { return message_; }

private:
    ErrorCode code_;
    std::string message_;
};
```

## 8. 测试策略

### 8.1 单元测试
- 每个模块独立测试
- 使用 Google Test 框架
- Mock 外部依赖

### 8.2 集成测试
- 端到端 SQL 执行测试
- 并发场景测试

### 8.3 性能测试
- 基准测试框架
- 关键路径性能监控
