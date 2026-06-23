package parser

import (
	"fmt"
	"query-parser/internal/ast"
	"query-parser/internal/lexer"
)

// Parser parses tokens into an AST
type Parser struct {
	tokens []lexer.Token
	pos    int
}

// New creates a new Parser
func New(tokens []lexer.Token) *Parser {
	return &Parser{
		tokens: tokens,
		pos:    0,
	}
}

// Parse parses the tokens into an AST
func (p *Parser) Parse() (*ast.Node, error) {
	if p.currentToken().Type == lexer.TokenEOF {
		return nil, fmt.Errorf("empty query")
	}

	node, err := p.parseOr()
	if err != nil {
		return nil, err
	}

	if p.currentToken().Type != lexer.TokenEOF {
		return nil, fmt.Errorf("unexpected token: %s", p.currentToken().Literal)
	}

	return node, nil
}

// parseOr handles OR expressions (lowest precedence)
func (p *Parser) parseOr() (*ast.Node, error) {
	left, err := p.parseAnd()
	if err != nil {
		return nil, err
	}

	for p.currentToken().Type == lexer.TokenOr {
		p.nextToken() // consume OR
		right, err := p.parseAnd()
		if err != nil {
			return nil, err
		}
		left = ast.NewOr(left, right)
	}

	return left, nil
}

// parseAnd handles AND expressions
func (p *Parser) parseAnd() (*ast.Node, error) {
	left, err := p.parseNot()
	if err != nil {
		return nil, err
	}

	for p.currentToken().Type == lexer.TokenAnd {
		p.nextToken() // consume AND
		right, err := p.parseNot()
		if err != nil {
			return nil, err
		}
		left = ast.NewAnd(left, right)
	}

	// Implicit AND: if next token is a term/phrase/NOT, treat as AND
	for p.currentToken().Type == lexer.TokenTerm ||
		p.currentToken().Type == lexer.TokenPhrase ||
		p.currentToken().Type == lexer.TokenLParen {
		right, err := p.parseNot()
		if err != nil {
			return nil, err
		}
		left = ast.NewAnd(left, right)
	}

	return left, nil
}

// parseNot handles NOT expressions
func (p *Parser) parseNot() (*ast.Node, error) {
	if p.currentToken().Type == lexer.TokenNot {
		p.nextToken() // consume NOT
		child, err := p.parsePrimary()
		if err != nil {
			return nil, err
		}
		return ast.NewNot(child), nil
	}

	return p.parsePrimary()
}

// parsePrimary handles primary expressions (terms, phrases, parentheses)
func (p *Parser) parsePrimary() (*ast.Node, error) {
	token := p.currentToken()

	switch token.Type {
	case lexer.TokenTerm:
		p.nextToken()
		return ast.NewTerm(token.Literal), nil

	case lexer.TokenPhrase:
		p.nextToken()
		return ast.NewPhrase(token.Literal), nil

	case lexer.TokenLParen:
		p.nextToken() // consume (
		node, err := p.parseOr()
		if err != nil {
			return nil, err
		}
		if p.currentToken().Type != lexer.TokenRParen {
			return nil, fmt.Errorf("expected ')', got %s", p.currentToken().Literal)
		}
		p.nextToken() // consume )
		return node, nil

	case lexer.TokenNot:
		// NOT is handled in parseNot, but just in case
		p.nextToken()
		child, err := p.parsePrimary()
		if err != nil {
			return nil, err
		}
		return ast.NewNot(child), nil

	default:
		return nil, fmt.Errorf("unexpected token: %s (type: %s)", token.Literal, token.Type)
	}
}

func (p *Parser) currentToken() lexer.Token {
	if p.pos >= len(p.tokens) {
		return lexer.Token{Type: lexer.TokenEOF}
	}
	return p.tokens[p.pos]
}

func (p *Parser) nextToken() {
	if p.pos < len(p.tokens) {
		p.pos++
	}
}
