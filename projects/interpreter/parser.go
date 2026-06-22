package main

import (
	"fmt"
	"strconv"
)

// Parser transforms a sequence of tokens into an AST.
// It uses a recursive descent approach with operator precedence climbing.
type Parser struct {
	lexer   *Lexer
	curTok  Token
	peekTok Token
	errors  []string
}

// precedence levels for operator precedence parsing.
const (
	_ int = iota
	LOWEST
	OR_PREC    // or
	AND_PREC   // and
	EQUALS     // == !=
	LESSGREATER// < > <= >=
	SUM        // + -
	PRODUCT    // * / %
	PREFIX     // -X or !X
	CALL       // myFunction(X)
)

// precedences maps token types to their precedence levels.
var precedences = map[TokenType]int{
	OR:     OR_PREC,
	AND:    AND_PREC,
	EQ:     EQUALS,
	NEQ:    EQUALS,
	LT:     LESSGREATER,
	GT:     LESSGREATER,
	LTE:    LESSGREATER,
	GTE:    LESSGREATER,
	PLUS:   SUM,
	MINUS:  SUM,
	STAR:   PRODUCT,
	SLASH:  PRODUCT,
	PERCENT: PRODUCT,
	LPAREN: CALL,
}

// NewParser creates a new Parser for the given input.
func NewParser(input string) *Parser {
	lexer := NewLexer(input)
	p := &Parser{lexer: lexer}
	// Read two tokens to set curTok and peekTok
	p.nextToken()
	p.nextToken()
	return p
}

// nextToken advances both curTok and peekTok.
func (p *Parser) nextToken() {
	p.curTok = p.peekTok
	p.peekTok = p.lexer.NextToken()
}

// Errors returns the parser errors.
func (p *Parser) Errors() []string {
	return p.errors
}

// Parse parses the input and returns the AST.
func (p *Parser) Parse() *Program {
	program := &Program{}

	for p.curTok.Type != EOF {
		stmt := p.parseStatement()
		if stmt != nil {
			program.Statements = append(program.Statements, stmt)
		}
		p.nextToken()
	}

	return program
}

// parseStatement parses a single statement.
func (p *Parser) parseStatement() Statement {
	switch p.curTok.Type {
	case LET:
		return p.parseLetStatement()
	case RETURN:
		return p.parseReturnStatement()
	case PRINT:
		return p.parsePrintStatement()
	case FN:
		return p.parseFunctionStatement()
	case IF:
		return p.parseIfStatement()
	case WHILE:
		return p.parseWhileStatement()
	case IDENT:
		// Could be assignment or expression statement
		if p.peekTok.Type == ASSIGN {
			return p.parseAssignStatement()
		}
		return p.parseExpressionStatement()
	default:
		return p.parseExpressionStatement()
	}
}

// parseLetStatement parses: let <name> = <expression>;
func (p *Parser) parseLetStatement() *LetStatement {
	stmt := &LetStatement{Token: p.curTok}

	if !p.expectPeek(IDENT) {
		return nil
	}

	stmt.Name = &Identifier{Token: p.curTok, Value: p.curTok.Literal}

	if !p.expectPeek(ASSIGN) {
		return nil
	}

	p.nextToken()
	stmt.Value = p.parseExpression(LOWEST)

	if p.peekTok.Type == SEMICOL {
		p.nextToken()
	}

	return stmt
}

// parseAssignStatement parses: <name> = <expression>;
func (p *Parser) parseAssignStatement() *AssignStatement {
	stmt := &AssignStatement{Token: p.curTok}
	stmt.Name = &Identifier{Token: p.curTok, Value: p.curTok.Literal}

	if !p.expectPeek(ASSIGN) {
		return nil
	}

	p.nextToken()
	stmt.Value = p.parseExpression(LOWEST)

	if p.peekTok.Type == SEMICOL {
		p.nextToken()
	}

	return stmt
}

// parseReturnStatement parses: return <expression>;
func (p *Parser) parseReturnStatement() *ReturnStatement {
	stmt := &ReturnStatement{Token: p.curTok}

	p.nextToken()
	stmt.ReturnValue = p.parseExpression(LOWEST)

	if p.peekTok.Type == SEMICOL {
		p.nextToken()
	}

	return stmt
}

// parsePrintStatement parses: print <expression>;
func (p *Parser) parsePrintStatement() *PrintStatement {
	stmt := &PrintStatement{Token: p.curTok}

	p.nextToken()
	stmt.Value = p.parseExpression(LOWEST)

	if p.peekTok.Type == SEMICOL {
		p.nextToken()
	}

	return stmt
}

// parseFunctionStatement parses: fn <name>(<params>) { <body> }
func (p *Parser) parseFunctionStatement() *FunctionStatement {
	stmt := &FunctionStatement{Token: p.curTok}

	if !p.expectPeek(IDENT) {
		return nil
	}

	stmt.Name = &Identifier{Token: p.curTok, Value: p.curTok.Literal}

	if !p.expectPeek(LPAREN) {
		return nil
	}

	stmt.Params = p.parseFunctionParameters()

	if !p.expectPeek(LBRACE) {
		return nil
	}

	stmt.Body = p.parseBlockStatement()

	return stmt
}

// parseFunctionParameters parses the parameter list of a function.
func (p *Parser) parseFunctionParameters() []*Identifier {
	params := []*Identifier{}

	if p.peekTok.Type == RPAREN {
		p.nextToken()
		return params
	}

	p.nextToken()
	params = append(params, &Identifier{Token: p.curTok, Value: p.curTok.Literal})

	for p.peekTok.Type == COMMA {
		p.nextToken() // consume comma
		p.nextToken() // move to next param
		params = append(params, &Identifier{Token: p.curTok, Value: p.curTok.Literal})
	}

	if !p.expectPeek(RPAREN) {
		return nil
	}

	return params
}

// parseIfStatement parses: if <condition> { <consequence> } else { <alternative> }
// Also supports: if ... { } else if ... { } else { }
func (p *Parser) parseIfStatement() *IfStatement {
	stmt := &IfStatement{Token: p.curTok}

	p.nextToken()
	stmt.Condition = p.parseExpression(LOWEST)

	if !p.expectPeek(LBRACE) {
		return nil
	}

	stmt.Consequence = p.parseBlockStatement()

	if p.peekTok.Type == ELSE {
		p.nextToken()

		// Support "else if" by treating it as else containing an if statement
		if p.peekTok.Type == IF {
			p.nextToken() // move to IF
			elseIfStmt := p.parseIfStatement()
			// Wrap the else-if in a block with a single statement
			stmt.Alternative = &BlockStatement{
				Token:      elseIfStmt.Token,
				Statements: []Statement{elseIfStmt},
			}
		} else {
			if !p.expectPeek(LBRACE) {
				return nil
			}
			stmt.Alternative = p.parseBlockStatement()
		}
	}

	return stmt
}

// parseWhileStatement parses: while <condition> { <body> }
func (p *Parser) parseWhileStatement() *WhileStatement {
	stmt := &WhileStatement{Token: p.curTok}

	p.nextToken()
	stmt.Condition = p.parseExpression(LOWEST)

	if !p.expectPeek(LBRACE) {
		return nil
	}

	stmt.Body = p.parseBlockStatement()

	return stmt
}

// parseBlockStatement parses a block of statements enclosed in braces.
func (p *Parser) parseBlockStatement() *BlockStatement {
	block := &BlockStatement{Token: p.curTok}
	block.Statements = []Statement{}

	p.nextToken()

	for p.curTok.Type != RBRACE && p.curTok.Type != EOF {
		stmt := p.parseStatement()
		if stmt != nil {
			block.Statements = append(block.Statements, stmt)
		}
		p.nextToken()
	}

	return block
}

// parseExpressionStatement parses an expression statement.
func (p *Parser) parseExpressionStatement() *ExpressionStatement {
	stmt := &ExpressionStatement{Token: p.curTok}
	stmt.Expression = p.parseExpression(LOWEST)

	if p.peekTok.Type == SEMICOL {
		p.nextToken()
	}

	return stmt
}

// parseExpression parses an expression using precedence climbing.
func (p *Parser) parseExpression(precedence int) Expression {
	// Prefix parsing
	var leftExp Expression
	switch p.curTok.Type {
	case IDENT:
		leftExp = &Identifier{Token: p.curTok, Value: p.curTok.Literal}
	case NUMBER:
		value, err := strconv.ParseFloat(p.curTok.Literal, 64)
		if err != nil {
			p.errors = append(p.errors, fmt.Sprintf("line %d:%d: could not parse %q as number", p.curTok.Line, p.curTok.Col, p.curTok.Literal))
			return nil
		}
		leftExp = &NumberLiteral{Token: p.curTok, Value: value}
	case STRING:
		leftExp = &StringLiteral{Token: p.curTok, Value: p.curTok.Literal}
	case TRUE:
		leftExp = &BooleanLiteral{Token: p.curTok, Value: true}
	case FALSE:
		leftExp = &BooleanLiteral{Token: p.curTok, Value: false}
	case MINUS, NOT:
		leftExp = p.parsePrefixExpression()
	case LPAREN:
		leftExp = p.parseGroupedExpression()
	default:
		p.errors = append(p.errors, fmt.Sprintf("line %d:%d: unexpected token %s (%s)", p.curTok.Line, p.curTok.Col, p.curTok.Type, p.curTok.Literal))
		return nil
	}

	// Infix parsing
	for p.peekTok.Type != SEMICOL && p.peekTok.Type != EOF && precedence < p.peekPrecedence() {
		switch p.peekTok.Type {
		case PLUS, MINUS, STAR, SLASH, PERCENT, EQ, NEQ, LT, GT, LTE, GTE, AND, OR:
			p.nextToken()
			leftExp = p.parseInfixExpression(leftExp)
		case LPAREN:
			p.nextToken()
			leftExp = p.parseCallExpression(leftExp)
		default:
			return leftExp
		}
	}

	return leftExp
}

// parsePrefixExpression parses a prefix expression.
func (p *Parser) parsePrefixExpression() *PrefixExpression {
	expr := &PrefixExpression{
		Token:    p.curTok,
		Operator: p.curTok.Literal,
	}

	p.nextToken()
	expr.Right = p.parseExpression(PREFIX)

	return expr
}

// parseInfixExpression parses an infix expression.
func (p *Parser) parseInfixExpression(left Expression) *InfixExpression {
	expr := &InfixExpression{
		Token:    p.curTok,
		Left:     left,
		Operator: p.curTok.Literal,
	}

	precedence := p.curPrecedence()
	p.nextToken()
	expr.Right = p.parseExpression(precedence)

	return expr
}

// parseGroupedExpression parses an expression in parentheses.
func (p *Parser) parseGroupedExpression() Expression {
	p.nextToken()

	exp := p.parseExpression(LOWEST)

	if !p.expectPeek(RPAREN) {
		return nil
	}

	return exp
}

// parseCallExpression parses a function call expression.
func (p *Parser) parseCallExpression(fn Expression) *CallExpression {
	expr := &CallExpression{Token: p.curTok, Function: fn}
	expr.Args = p.parseExpressionList()
	return expr
}

// parseExpressionList parses a comma-separated list of expressions.
func (p *Parser) parseExpressionList() []Expression {
	args := []Expression{}

	if p.peekTok.Type == RPAREN {
		p.nextToken()
		return args
	}

	p.nextToken()
	args = append(args, p.parseExpression(LOWEST))

	for p.peekTok.Type == COMMA {
		p.nextToken()
		p.nextToken()
		args = append(args, p.parseExpression(LOWEST))
	}

	if !p.expectPeek(RPAREN) {
		return nil
	}

	return args
}

// expectPeek checks the peek token type and advances if it matches.
func (p *Parser) expectPeek(t TokenType) bool {
	if p.peekTok.Type == t {
		p.nextToken()
		return true
	}
	p.peekError(t)
	return false
}

// peekError adds an error for an unexpected peek token.
func (p *Parser) peekError(t TokenType) {
	msg := fmt.Sprintf("line %d:%d: expected next token to be %s, got %s instead",
		p.peekTok.Line, p.peekTok.Col, t, p.peekTok.Type)
	p.errors = append(p.errors, msg)
}

// curPrecedence returns the precedence of the current token.
func (p *Parser) curPrecedence() int {
	if p, ok := precedences[p.curTok.Type]; ok {
		return p
	}
	return LOWEST
}

// peekPrecedence returns the precedence of the peek token.
func (p *Parser) peekPrecedence() int {
	if p, ok := precedences[p.peekTok.Type]; ok {
		return p
	}
	return LOWEST
}
