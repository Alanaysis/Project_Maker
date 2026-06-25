# 技术设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Simple Compiler                             │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Lexer   │───▶│  Parser  │───▶│ Semantic │───▶│ IR Gen   │ │
│  │          │    │          │    │ Analyzer │    │          │ │
│  │ Source → │    │ Tokens → │    │ AST →    │    │ AST →    │ │
│  │ Tokens   │    │ AST      │    │ Checked  │    │ IR       │ │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘ │
│                                                        │       │
│                                                        ▼       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Code     │◀───│Optimizer │◀───│    IR    │◀───│  IR      │ │
│  │ Gen      │    │          │    │          │    │          │ │
│  │          │    │ IR →     │    │          │    │          │ │
│  │ IR → ASM │    │ Opt IR   │    │          │    │          │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    Interpreter                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │   Direct    │  │   Stack     │  │  Register   │     │ │
│  │  │ Execution   │  │     VM      │  │     VM      │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| Lexer | 词法分析 | 源代码 | Token 流 |
| Parser | 语法分析 | Token 流 | AST |
| Semantic | 语义分析 | AST | 检查后的 AST |
| IR Gen | IR 生成 | AST | 中间表示 |
| Optimizer | 代码优化 | IR | 优化后的 IR |
| Code Gen | 代码生成 | IR | 汇编代码 |
| Interpreter | 解释执行 | AST/IR | 执行结果 |

## 2. 文件组织

### 2.1 目录结构

```
simple-compiler/
├── CMakeLists.txt              # CMake 配置
├── README.md                   # 项目说明
├── include/                    # 头文件目录
│   ├── token.hpp              # Token 定义
│   ├── lexer.hpp              # 词法分析器接口
│   ├── ast.hpp                # AST 节点定义
│   ├── parser.hpp             # 语法分析器接口
│   ├── semantic.hpp           # 语义分析器接口
│   ├── ir.hpp                 # IR 定义
│   ├── optimizer.hpp          # 优化器接口
│   ├── codegen.hpp            # 代码生成器接口
│   └── interpreter.hpp        # 解释器接口
├── src/                       # 源文件目录
│   ├── lexer.cpp              # 词法分析器实现
│   ├── parser.cpp             # 语法分析器实现
│   ├── semantic.cpp           # 语义分析器实现
│   ├── ir.cpp                 # IR 生成器实现
│   ├── optimizer.cpp          # 优化器实现
│   ├── codegen.cpp            # 代码生成器实现
│   └── interpreter.cpp        # 解释器实现
├── tests/                     # 测试目录
│   ├── test_lexer.cpp         # 词法分析器测试
│   ├── test_parser.cpp        # 语法分析器测试
│   └── test_interpreter.cpp   # 解释器测试
├── examples/                  # 示例目录
│   ├── main.cpp               # 编译器主程序
│   ├── calculator.cpp         # 计算器示例
│   ├── script_interpreter.cpp # 脚本解释器示例
│   └── dsl_example.cpp        # DSL 示例
└── docs/                      # 文档目录
    ├── 01_RESEARCH.md         # 调研文档
    ├── 02_REQUIREMENTS.md     # 需求文档
    ├── 03_DESIGN.md           # 设计文档
    ├── 04_PRODUCT.md          # 产品文档
    └── 05_DEVELOPMENT.md      # 开发文档
```

### 2.2 文件命名规范

- 头文件：`.hpp` 扩展名
- 源文件：`.cpp` 扩展名
- 测试文件：`test_` 前缀
- 示例文件：描述性名称

### 2.3 命名空间

```cpp
namespace compiler {
    // 所有编译器相关的类和函数
}
```

## 3. 核心设计

### 3.1 Token 设计

```cpp
enum class TokenType {
    // 字面量
    INTEGER, FLOAT, STRING, BOOL,
    
    // 标识符和关键字
    IDENTIFIER, LET, VAR, CONST, IF, ELSE, WHILE, FOR, FN, RETURN, CLASS,
    
    // 运算符
    PLUS, MINUS, MULTIPLY, DIVIDE, MODULO,
    EQUAL, NOT_EQUAL, LESS, GREATER, LESS_EQUAL, GREATER_EQUAL,
    AND, OR, NOT,
    
    // 分隔符
    LEFT_PAREN, RIGHT_PAREN, LEFT_BRACE, RIGHT_BRACE,
    COMMA, SEMICOLON, COLON,
    
    // 特殊
    EOF_TOKEN, NEWLINE, ERROR
};

struct Token {
    TokenType type;
    std::string lexeme;
    TokenValue value;  // variant<int64_t, double, std::string, bool>
    int line;
    int column;
};
```

### 3.2 AST 设计

```cpp
// 基类
struct ASTNode {
    int line;
    int column;
    virtual ~ASTNode() = default;
};

// 表达式节点
struct Expr : public ASTNode {
    ExprType exprType;
    TypePtr type;  // 语义分析后填充
};

// 语句节点
struct Stmt : public ASTNode {
    StmtType stmtType;
};

// 具体节点
struct BinaryExpr : public Expr {
    ExprPtr left;
    Token op;
    ExprPtr right;
};

struct FunctionStmt : public Stmt {
    std::string name;
    std::vector<Parameter> params;
    TypePtr returnType;
    StmtPtr body;
};
```

### 3.3 类型系统设计

```cpp
enum class TypeKind {
    INT, FLOAT, STRING, BOOL, VOID,
    ARRAY, FUNCTION, CLASS, AUTO
};

struct Type {
    TypeKind kind;
    virtual ~Type() = default;
};

struct ArrayType : public Type {
    TypePtr elementType;
    size_t size;
};

struct FunctionType : public Type {
    std::vector<TypePtr> paramTypes;
    TypePtr returnType;
};
```

### 3.4 IR 设计

```cpp
enum class IROpcode {
    // 算术
    ADD, SUB, MUL, DIV, MOD, NEG,
    // 比较
    CMP_EQ, CMP_NE, CMP_LT, CMP_GT,
    // 控制
    JUMP, BRANCH, CALL, RETURN,
    // 内存
    LOAD, STORE, ALLOCA,
    // 特殊
    LABEL, PHI, PRINT
};

struct IRValue {
    std::string name;
    IRValueType type;
    bool isConstant;
    bool isTemporary;
    union { int64_t intValue; double floatValue; bool boolValue; } constant;
};

struct IRInstruction {
    IROpcode opcode;
    IRValue result;
    std::vector<IRValue> operands;
};

struct BasicBlock {
    int id;
    std::string label;
    std::vector<IRInstruction> instructions;
    std::vector<int> predecessors;
    std::vector<int> successors;
};

struct IRFunction {
    std::string name;
    std::vector<IRValue> parameters;
    IRValueType returnType;
    std::vector<BasicBlock> basicBlocks;
};
```

## 4. 词法分析器设计

### 4.1 工作流程

```
源代码 → 扫描字符 → 识别 Token → 输出 Token 流
```

### 4.2 核心算法

```cpp
Token Lexer::nextToken() {
    skipWhitespace();
    
    if (isAtEnd()) return makeToken(EOF_TOKEN);
    
    char c = advance();
    
    if (isAlpha(c)) return identifier();
    if (isDigit(c)) return number();
    if (c == '"') return string();
    
    return operatorToken();
}
```

### 4.3 关键字识别

```cpp
const std::unordered_map<std::string, TokenType> keywords = {
    {"let", TokenType::LET},
    {"var", TokenType::VAR},
    {"if", TokenType::IF},
    // ...
};

Token Lexer::identifier() {
    while (isAlphaNumeric(peek())) advance();
    
    std::string text = source.substr(start, current - start);
    
    auto it = keywords.find(text);
    if (it != keywords.end()) {
        return Token(it->second, text);
    }
    
    return Token(IDENTIFIER, text);
}
```

## 5. 语法分析器设计

### 5.1 递归下降法

```cpp
ExprPtr Parser::expression() {
    return assignment();
}

ExprPtr Parser::assignment() {
    ExprPtr expr = logicOr();
    
    if (match({ASSIGN})) {
        ExprPtr value = assignment();  // 右结合
        return makeAssign(expr, value);
    }
    
    return expr;
}

ExprPtr Parser::logicOr() {
    ExprPtr expr = logicAnd();
    
    while (match({OR})) {
        Token op = previous();
        ExprPtr right = logicAnd();
        expr = makeBinary(expr, op, right);
    }
    
    return expr;
}

// ... 更多优先级层次
```

### 5.2 优先级处理

```
优先级从低到高：
1. 赋值 (=, +=, -=, etc.)
2. 逻辑或 (||)
3. 逻辑与 (&&)
4. 相等 (==, !=)
5. 比较 (<, >, <=, >=)
6. 加减 (+, -)
7. 乘除 (*, /, %)
8. 一元 (!, -, ++, --)
9. 后缀 ((), [], .)
10. 基本 (字面量, 标识符, 括号)
```

### 5.3 错误恢复

```cpp
void Parser::synchronize() {
    panicMode = false;
    
    while (!isAtEnd()) {
        if (previous().type == SEMICOLON) return;
        
        switch (peek().type) {
            case LET: case VAR: case IF: case WHILE:
            case FOR: case FN: case RETURN:
                return;
        }
        
        advance();
    }
}
```

## 6. 语义分析器设计

### 6.1 作用域管理

```cpp
class Scope {
    std::unordered_map<std::string, Symbol> symbols;
    std::shared_ptr<Scope> parent;
    int level;
    
    bool define(const std::string& name, const Symbol& symbol);
    Symbol* resolve(const std::string& name);
};
```

### 6.2 类型检查

```cpp
TypePtr SemanticAnalyzer::analyzeBinary(BinaryExpr& expr) {
    TypePtr leftType = analyzeExpr(expr.left);
    TypePtr rightType = analyzeExpr(expr.right);
    
    // 检查类型兼容性
    if (!isCompatible(leftType, rightType)) {
        error("Type mismatch");
    }
    
    // 确定结果类型
    if (isComparison(expr.op)) {
        return BOOL_TYPE;
    }
    
    return leftType;
}
```

## 7. 优化器设计

### 7.1 Pass 管理

```cpp
class Optimizer {
    std::vector<std::unique_ptr<OptimizationPass>> passes;
    
    void optimize(IRModule& module) {
        bool changed = true;
        while (changed) {
            changed = false;
            for (auto& pass : passes) {
                if (pass->run(module)) {
                    changed = true;
                }
            }
        }
    }
};
```

### 7.2 常量折叠

```cpp
bool ConstantFoldingPass::processInstruction(IRInstruction& instr) {
    if (instr.operands[0].isConstant && instr.operands[1].isConstant) {
        IRValue result = foldConstants(instr.opcode, 
                                       instr.operands[0], 
                                       instr.operands[1]);
        instr.result = result;
        instr.opcode = LOAD;
        return true;
    }
    return false;
}
```

## 8. 代码生成器设计

### 8.1 寄存器分配

```cpp
class RegisterAllocator {
    std::unordered_map<int, Register> allocate(const IRFunction& func) {
        auto intervals = computeLiveIntervals(func);
        return linearScan(intervals);
    }
};
```

### 8.2 汇编生成

```cpp
void CodeGenerator::generateInstruction(const IRInstruction& instr) {
    switch (instr.opcode) {
        case ADD:
            emit("mov rax, " + operandToStr(instr.operands[0]));
            emit("add rax, " + operandToStr(instr.operands[1]));
            break;
        case SUB:
            emit("mov rax, " + operandToStr(instr.operands[0]));
            emit("sub rax, " + operandToStr(instr.operands[1]));
            break;
        // ...
    }
}
```

## 9. 解释器设计

### 9.1 直接解释执行

```cpp
RuntimeValue Interpreter::evaluate(Expr& expr) {
    switch (expr.exprType) {
        case BINARY: return evaluateBinary(expr);
        case UNARY: return evaluateUnary(expr);
        case LITERAL: return evaluateLiteral(expr);
        case VARIABLE: return evaluateVariable(expr);
        case CALL: return evaluateCall(expr);
        // ...
    }
}
```

### 9.2 栈式虚拟机

```cpp
bool StackVM::execute(const Bytecode& bytecode) {
    while (pc < bytecode.instructions.size()) {
        auto& instr = bytecode.instructions[pc];
        
        switch (instr.opcode) {
            case LOAD_CONST:
                push(bytecode.constants[instr.operand]);
                break;
            case ADD: {
                auto right = pop();
                auto left = pop();
                push(left + right);
                break;
            }
            case JUMP:
                pc = instr.operand;
                continue;
            // ...
        }
        
        pc++;
    }
}
```

## 10. 数据结构选择

### 10.1 使用 `std::variant` 表示值

```cpp
using RuntimeValue = std::variant<
    std::monostate,     // null
    int64_t,            // 整数
    double,             // 浮点数
    bool,               // 布尔值
    std::string,        // 字符串
    std::vector<RuntimeValue>  // 数组
>;
```

### 10.2 使用智能指针管理 AST

```cpp
using ExprPtr = std::unique_ptr<Expr>;
using StmtPtr = std::unique_ptr<Stmt>;
using TypePtr = std::unique_ptr<Type>;
```

### 10.3 使用 `std::unordered_map` 做符号表

```cpp
std::unordered_map<std::string, Symbol> symbols;
```

## 11. 错误处理策略

### 11.1 错误类型

- 词法错误：非法字符、未闭合字符串
- 语法错误：缺少分号、括号不匹配
- 语义错误：类型不匹配、未定义变量
- 运行时错误：除以零、数组越界

### 11.2 错误报告

```cpp
void error(int line, int column, const std::string& message) {
    std::cerr << "Error at line " << line << ", column " << column
              << ": " << message << std::endl;
    errors.push_back(message);
}
```

### 11.3 错误恢复

- 词法分析：跳过非法字符
- 语法分析：同步到语句边界
- 语义分析：继续分析其他部分
- 运行时：抛出异常

## 12. 性能考虑

### 12.1 内存管理

- 使用智能指针避免内存泄漏
- 使用移动语义减少拷贝
- 使用 `std::string_view` 避免字符串拷贝

### 12.2 数据结构选择

- `std::vector` 用于顺序访问
- `std::unordered_map` 用于快速查找
- `std::variant` 用于类型安全的值表示

### 12.3 算法优化

- 递归下降解析：O(n) 时间复杂度
- 线性扫描寄存器分配：O(n log n)
- 常量折叠：O(n)

## 13. 测试策略

### 13.1 单元测试

- 每个模块独立测试
- 测试正常情况和边界情况
- 测试错误处理

### 13.2 集成测试

- 测试完整编译流程
- 测试示例程序
- 测试错误恢复

### 13.3 回归测试

- 修复 bug 后添加测试
- 确保不引入新问题

## 14. 总结

本设计文档详细描述了简易编译器的：

1. **系统架构**：模块化、可扩展
2. **数据结构**：类型安全、高效
3. **算法设计**：经典、实用
4. **错误处理**：完善、用户友好
5. **性能考虑**：优化、高效

通过这个设计，我们可以构建一个完整、可读、可扩展的编译器实现。

---

[返回首页](../README.md)
