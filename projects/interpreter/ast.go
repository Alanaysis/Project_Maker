package main

// ---------- AST Node Interfaces ----------

// Node is the base interface for all AST nodes.
type Node interface {
	TokenLiteral() string
	String() string
}

// Statement is a node that represents a statement.
type Statement interface {
	Node
	statementNode()
}

// Expression is a node that represents an expression.
type Expression interface {
	Node
	expressionNode()
}

// ---------- Program ----------

// Program is the root node of every AST.
type Program struct {
	Statements []Statement
}

func (p *Program) TokenLiteral() string {
	if len(p.Statements) > 0 {
		return p.Statements[0].TokenLiteral()
	}
	return ""
}

func (p *Program) String() string {
	result := ""
	for _, s := range p.Statements {
		result += s.String() + "\n"
	}
	return result
}

// ---------- Statements ----------

// LetStatement represents a variable declaration: let x = expr;
type LetStatement struct {
	Token Token // the LET token
	Name  *Identifier
	Value Expression
}

func (ls *LetStatement) statementNode()       {}
func (ls *LetStatement) TokenLiteral() string { return ls.Token.Literal }
func (ls *LetStatement) String() string {
	return "let " + ls.Name.String() + " = " + ls.Value.String() + ";"
}

// AssignStatement represents a variable assignment: x = expr;
type AssignStatement struct {
	Token Token // the IDENT token
	Name  *Identifier
	Value Expression
}

func (as *AssignStatement) statementNode()       {}
func (as *AssignStatement) TokenLiteral() string { return as.Token.Literal }
func (as *AssignStatement) String() string {
	return as.Name.String() + " = " + as.Value.String() + ";"
}

// ReturnStatement represents a return statement: return expr;
type ReturnStatement struct {
	Token       Token // the RETURN token
	ReturnValue Expression
}

func (rs *ReturnStatement) statementNode()       {}
func (rs *ReturnStatement) TokenLiteral() string { return rs.Token.Literal }
func (rs *ReturnStatement) String() string {
	if rs.ReturnValue != nil {
		return "return " + rs.ReturnValue.String() + ";"
	}
	return "return;"
}

// ExpressionStatement represents an expression used as a statement.
type ExpressionStatement struct {
	Token      Token
	Expression Expression
}

func (es *ExpressionStatement) statementNode()       {}
func (es *ExpressionStatement) TokenLiteral() string { return es.Token.Literal }
func (es *ExpressionStatement) String() string {
	if es.Expression != nil {
		return es.Expression.String()
	}
	return ""
}

// PrintStatement represents a print statement: print expr;
type PrintStatement struct {
	Token Token // the PRINT token
	Value Expression
}

func (ps *PrintStatement) statementNode()       {}
func (ps *PrintStatement) TokenLiteral() string { return ps.Token.Literal }
func (ps *PrintStatement) String() string {
	return "print " + ps.Value.String() + ";"
}

// BlockStatement represents a block of statements enclosed in braces.
type BlockStatement struct {
	Token      Token // the { token
	Statements []Statement
}

func (bs *BlockStatement) statementNode()       {}
func (bs *BlockStatement) TokenLiteral() string { return bs.Token.Literal }
func (bs *BlockStatement) String() string {
	result := "{\n"
	for _, s := range bs.Statements {
		result += "  " + s.String() + "\n"
	}
	result += "}"
	return result
}

// IfStatement represents an if-else statement.
type IfStatement struct {
	Token       Token // the IF token
	Condition   Expression
	Consequence *BlockStatement
	Alternative *BlockStatement
}

func (is *IfStatement) statementNode()       {}
func (is *IfStatement) TokenLiteral() string { return is.Token.Literal }
func (is *IfStatement) String() string {
	result := "if " + is.Condition.String() + " " + is.Consequence.String()
	if is.Alternative != nil {
		result += " else " + is.Alternative.String()
	}
	return result
}

// WhileStatement represents a while loop.
type WhileStatement struct {
	Token     Token // the WHILE token
	Condition Expression
	Body      *BlockStatement
}

func (ws *WhileStatement) statementNode()       {}
func (ws *WhileStatement) TokenLiteral() string { return ws.Token.Literal }
func (ws *WhileStatement) String() string {
	return "while " + ws.Condition.String() + " " + ws.Body.String()
}

// FunctionStatement represents a function declaration: fn name(params) { body }
type FunctionStatement struct {
	Token  Token // the FN token
	Name   *Identifier
	Params []*Identifier
	Body   *BlockStatement
}

func (fs *FunctionStatement) statementNode()       {}
func (fs *FunctionStatement) TokenLiteral() string { return fs.Token.Literal }
func (fs *FunctionStatement) String() string {
	params := ""
	for i, p := range fs.Params {
		if i > 0 {
			params += ", "
		}
		params += p.String()
	}
	return "fn " + fs.Name.String() + "(" + params + ") " + fs.Body.String()
}

// ---------- Expressions ----------

// Identifier represents a variable or function name.
type Identifier struct {
	Token Token // the IDENT token
	Value string
}

func (i *Identifier) expressionNode()      {}
func (i *Identifier) TokenLiteral() string { return i.Token.Literal }
func (i *Identifier) String() string       { return i.Value }

// NumberLiteral represents a numeric literal.
type NumberLiteral struct {
	Token Token
	Value float64
}

func (nl *NumberLiteral) expressionNode()      {}
func (nl *NumberLiteral) TokenLiteral() string { return nl.Token.Literal }
func (nl *NumberLiteral) String() string       { return nl.Token.Literal }

// StringLiteral represents a string literal.
type StringLiteral struct {
	Token Token
	Value string
}

func (sl *StringLiteral) expressionNode()      {}
func (sl *StringLiteral) TokenLiteral() string { return sl.Token.Literal }
func (sl *StringLiteral) String() string       { return "\"" + sl.Value + "\"" }

// BooleanLiteral represents a boolean literal.
type BooleanLiteral struct {
	Token Token
	Value bool
}

func (bl *BooleanLiteral) expressionNode()      {}
func (bl *BooleanLiteral) TokenLiteral() string { return bl.Token.Literal }
func (bl *BooleanLiteral) String() string       { return bl.Token.Literal }

// PrefixExpression represents a prefix expression: !expr or -expr
type PrefixExpression struct {
	Token    Token // the prefix token
	Operator string
	Right    Expression
}

func (pe *PrefixExpression) expressionNode()      {}
func (pe *PrefixExpression) TokenLiteral() string { return pe.Token.Literal }
func (pe *PrefixExpression) String() string {
	return "(" + pe.Operator + pe.Right.String() + ")"
}

// InfixExpression represents an infix expression: expr op expr
type InfixExpression struct {
	Token    Token // the operator token
	Left     Expression
	Operator string
	Right    Expression
}

func (ie *InfixExpression) expressionNode()      {}
func (ie *InfixExpression) TokenLiteral() string { return ie.Token.Literal }
func (ie *InfixExpression) String() string {
	return "(" + ie.Left.String() + " " + ie.Operator + " " + ie.Right.String() + ")"
}

// CallExpression represents a function call: fn(arg1, arg2)
type CallExpression struct {
	Token    Token // the ( token
	Function Expression
	Args     []Expression
}

func (ce *CallExpression) expressionNode()      {}
func (ce *CallExpression) TokenLiteral() string { return ce.Token.Literal }
func (ce *CallExpression) String() string {
	args := ""
	for i, a := range ce.Args {
		if i > 0 {
			args += ", "
		}
		args += a.String()
	}
	return ce.Function.String() + "(" + args + ")"
}
