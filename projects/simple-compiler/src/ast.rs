/// Abstract Syntax Tree definitions
///
/// The AST is a tree representation of the source code structure.
/// Each node represents a construct in the language (expressions, statements, etc.).
///
/// A complete program is a list of statements
#[derive(Debug, Clone, PartialEq)]
pub struct Program {
    pub statements: Vec<Statement>,
}

/// Statement types
#[derive(Debug, Clone, PartialEq)]
pub enum Statement {
    /// `let name: Type = expr;`
    Let {
        name: String,
        type_ann: Option<TypeExpr>,
        value: Expression,
    },
    /// `name = expr;`
    Assign {
        name: String,
        value: Expression,
    },
    /// `print(expr, ...);`
    Print {
        args: Vec<Expression>,
    },
    /// `if expr { ... } else { ... }`
    If {
        condition: Expression,
        then_block: Vec<Statement>,
        else_block: Option<Vec<Statement>>,
    },
    /// `while expr { ... }`
    While {
        condition: Expression,
        body: Vec<Statement>,
    },
    /// `fn name(params) -> RetType { ... }`
    FunctionDef {
        name: String,
        params: Vec<Param>,
        return_type: Option<TypeExpr>,
        body: Vec<Statement>,
    },
    /// `return expr;`
    Return {
        value: Option<Expression>,
    },
    /// `expr;` (expression used as statement)
    Expression {
        expr: Expression,
    },
}

/// Function parameter
#[derive(Debug, Clone, PartialEq)]
pub struct Param {
    pub name: String,
    pub type_ann: Option<TypeExpr>,
}

/// Type expressions (simple for now)
#[derive(Debug, Clone, PartialEq)]
pub enum TypeExpr {
    Int,
    Float,
    Bool,
    String,
}

/// Expression types
#[derive(Debug, Clone, PartialEq)]
pub enum Expression {
    /// Integer literal: `42`
    IntegerLiteral(i64),
    /// Float literal: `3.14`
    FloatLiteral(f64),
    /// String literal: `"hello"`
    StringLiteral(String),
    /// Boolean literal: `true` / `false`
    BoolLiteral(bool),
    /// Variable reference: `x`
    Identifier(String),
    /// Binary operation: `a + b`
    BinaryOp {
        op: BinaryOp,
        left: Box<Expression>,
        right: Box<Expression>,
    },
    /// Unary operation: `-x`, `!x`
    UnaryOp {
        op: UnaryOp,
        operand: Box<Expression>,
    },
    /// Function call: `foo(1, 2)`
    Call {
        name: String,
        args: Vec<Expression>,
    },
}

/// Binary operators
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum BinaryOp {
    Add,      // +
    Sub,      // -
    Mul,      // *
    Div,      // /
    Mod,      // %
    Eq,       // ==
    NotEq,    // !=
    Lt,       // <
    LtEq,     // <=
    Gt,       // >
    GtEq,     // >=
    And,      // &&
    Or,       // ||
}

/// Unary operators
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum UnaryOp {
    Neg,  // -
    Not,  // !
}
