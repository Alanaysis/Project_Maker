package main

import (
	"strings"
	"testing"
)

func TestIdentifierString(t *testing.T) {
	ident := &Identifier{Token: Token{Type: IDENT, Literal: "foo"}, Value: "foo"}
	if ident.String() != "foo" {
		t.Errorf("expected %q, got %q", "foo", ident.String())
	}
	if ident.TokenLiteral() != "foo" {
		t.Errorf("expected TokenLiteral %q, got %q", "foo", ident.TokenLiteral())
	}
}

func TestNumberLiteralString(t *testing.T) {
	nl := &NumberLiteral{Token: Token{Type: NUMBER, Literal: "42"}, Value: 42}
	if nl.String() != "42" {
		t.Errorf("expected %q, got %q", "42", nl.String())
	}
}

func TestStringLiteralString(t *testing.T) {
	sl := &StringLiteral{Token: Token{Type: STRING, Literal: "hello"}, Value: "hello"}
	if sl.String() != "\"hello\"" {
		t.Errorf("expected %q, got %q", "\"hello\"", sl.String())
	}
}

func TestBooleanLiteralString(t *testing.T) {
	bl := &BooleanLiteral{Token: Token{Type: TRUE, Literal: "true"}, Value: true}
	if bl.String() != "true" {
		t.Errorf("expected %q, got %q", "true", bl.String())
	}
}

func TestPrefixExpressionString(t *testing.T) {
	pe := &PrefixExpression{
		Token:    Token{Type: MINUS, Literal: "-"},
		Operator: "-",
		Right:    &NumberLiteral{Token: Token{Type: NUMBER, Literal: "5"}, Value: 5},
	}
	if pe.String() != "(-5)" {
		t.Errorf("expected %q, got %q", "(-5)", pe.String())
	}
}

func TestInfixExpressionString(t *testing.T) {
	ie := &InfixExpression{
		Token:    Token{Type: PLUS, Literal: "+"},
		Left:     &NumberLiteral{Token: Token{Type: NUMBER, Literal: "1"}, Value: 1},
		Operator: "+",
		Right:    &NumberLiteral{Token: Token{Type: NUMBER, Literal: "2"}, Value: 2},
	}
	if ie.String() != "(1 + 2)" {
		t.Errorf("expected %q, got %q", "(1 + 2)", ie.String())
	}
}

func TestCallExpressionString(t *testing.T) {
	ce := &CallExpression{
		Token:    Token{Type: LPAREN, Literal: "("},
		Function: &Identifier{Token: Token{Type: IDENT, Literal: "add"}, Value: "add"},
		Args: []Expression{
			&NumberLiteral{Token: Token{Type: NUMBER, Literal: "1"}, Value: 1},
			&NumberLiteral{Token: Token{Type: NUMBER, Literal: "2"}, Value: 2},
		},
	}
	if ce.String() != "add(1, 2)" {
		t.Errorf("expected %q, got %q", "add(1, 2)", ce.String())
	}
}

func TestCallExpressionNoArgs(t *testing.T) {
	ce := &CallExpression{
		Token:    Token{Type: LPAREN, Literal: "("},
		Function: &Identifier{Token: Token{Type: IDENT, Literal: "foo"}, Value: "foo"},
		Args:     []Expression{},
	}
	if ce.String() != "foo()" {
		t.Errorf("expected %q, got %q", "foo()", ce.String())
	}
}

func TestLetStatementString(t *testing.T) {
	ls := &LetStatement{
		Token: Token{Type: LET, Literal: "let"},
		Name:  &Identifier{Token: Token{Type: IDENT, Literal: "x"}, Value: "x"},
		Value: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "5"}, Value: 5},
	}
	expected := "let x = 5;"
	if ls.String() != expected {
		t.Errorf("expected %q, got %q", expected, ls.String())
	}
}

func TestAssignStatementString(t *testing.T) {
	as := &AssignStatement{
		Token: Token{Type: IDENT, Literal: "x"},
		Name:  &Identifier{Token: Token{Type: IDENT, Literal: "x"}, Value: "x"},
		Value: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "10"}, Value: 10},
	}
	expected := "x = 10;"
	if as.String() != expected {
		t.Errorf("expected %q, got %q", expected, as.String())
	}
}

func TestReturnStatementString(t *testing.T) {
	rs := &ReturnStatement{
		Token:       Token{Type: RETURN, Literal: "return"},
		ReturnValue: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "5"}, Value: 5},
	}
	expected := "return 5;"
	if rs.String() != expected {
		t.Errorf("expected %q, got %q", expected, rs.String())
	}
}

func TestReturnStatementNilValue(t *testing.T) {
	rs := &ReturnStatement{
		Token:       Token{Type: RETURN, Literal: "return"},
		ReturnValue: nil,
	}
	expected := "return;"
	if rs.String() != expected {
		t.Errorf("expected %q, got %q", expected, rs.String())
	}
}

func TestPrintStatementString(t *testing.T) {
	ps := &PrintStatement{
		Token: Token{Type: PRINT, Literal: "print"},
		Value: &StringLiteral{Token: Token{Type: STRING, Literal: "hello"}, Value: "hello"},
	}
	expected := "print \"hello\";"
	if ps.String() != expected {
		t.Errorf("expected %q, got %q", expected, ps.String())
	}
}

func TestExpressionStatementString(t *testing.T) {
	es := &ExpressionStatement{
		Token:      Token{Type: NUMBER, Literal: "5"},
		Expression: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "5"}, Value: 5},
	}
	if es.String() != "5" {
		t.Errorf("expected %q, got %q", "5", es.String())
	}
}

func TestExpressionStatementNilExpression(t *testing.T) {
	es := &ExpressionStatement{
		Token:      Token{Type: EOF, Literal: ""},
		Expression: nil,
	}
	if es.String() != "" {
		t.Errorf("expected empty string, got %q", es.String())
	}
}

func TestBlockStatementString(t *testing.T) {
	block := &BlockStatement{
		Token: Token{Type: LBRACE, Literal: "{"},
		Statements: []Statement{
			&LetStatement{
				Token: Token{Type: LET, Literal: "let"},
				Name:  &Identifier{Token: Token{Type: IDENT, Literal: "x"}, Value: "x"},
				Value: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "1"}, Value: 1},
			},
		},
	}
	expected := "{\n  let x = 1;\n}"
	if block.String() != expected {
		t.Errorf("expected %q, got %q", expected, block.String())
	}
}

func TestIfStatementString(t *testing.T) {
	ifStmt := &IfStatement{
		Token:     Token{Type: IF, Literal: "if"},
		Condition: &BooleanLiteral{Token: Token{Type: TRUE, Literal: "true"}, Value: true},
		Consequence: &BlockStatement{
			Token: Token{Type: LBRACE, Literal: "{"},
			Statements: []Statement{
				&PrintStatement{
					Token: Token{Type: PRINT, Literal: "print"},
					Value: &StringLiteral{Token: Token{Type: STRING, Literal: "yes"}, Value: "yes"},
				},
			},
		},
		Alternative: &BlockStatement{
			Token: Token{Type: LBRACE, Literal: "{"},
			Statements: []Statement{
				&PrintStatement{
					Token: Token{Type: PRINT, Literal: "print"},
					Value: &StringLiteral{Token: Token{Type: STRING, Literal: "no"}, Value: "no"},
				},
			},
		},
	}

	result := ifStmt.String()
	if result == "" {
		t.Error("expected non-empty string for if statement")
	}
	// Should contain "if" and "else"
	if !strings.Contains(result, "if") || !strings.Contains(result, "else") {
		t.Errorf("expected string to contain 'if' and 'else', got %q", result)
	}
}

func TestIfStatementStringNoElse(t *testing.T) {
	ifStmt := &IfStatement{
		Token:     Token{Type: IF, Literal: "if"},
		Condition: &BooleanLiteral{Token: Token{Type: TRUE, Literal: "true"}, Value: true},
		Consequence: &BlockStatement{
			Token:      Token{Type: LBRACE, Literal: "{"},
			Statements: []Statement{},
		},
		Alternative: nil,
	}

	result := ifStmt.String()
	if !strings.Contains(result, "if") {
		t.Errorf("expected string to contain 'if', got %q", result)
	}
	if strings.Contains(result, "else") {
		t.Errorf("expected string to not contain 'else', got %q", result)
	}
}

func TestWhileStatementString(t *testing.T) {
	ws := &WhileStatement{
		Token:     Token{Type: WHILE, Literal: "while"},
		Condition: &BooleanLiteral{Token: Token{Type: TRUE, Literal: "true"}, Value: true},
		Body: &BlockStatement{
			Token:      Token{Type: LBRACE, Literal: "{"},
			Statements: []Statement{},
		},
	}

	result := ws.String()
	if !strings.Contains(result, "while") {
		t.Errorf("expected string to contain 'while', got %q", result)
	}
}

func TestFunctionStatementString(t *testing.T) {
	fs := &FunctionStatement{
		Token: Token{Type: FN, Literal: "fn"},
		Name:  &Identifier{Token: Token{Type: IDENT, Literal: "add"}, Value: "add"},
		Params: []*Identifier{
			{Token: Token{Type: IDENT, Literal: "a"}, Value: "a"},
			{Token: Token{Type: IDENT, Literal: "b"}, Value: "b"},
		},
		Body: &BlockStatement{
			Token:      Token{Type: LBRACE, Literal: "{"},
			Statements: []Statement{},
		},
	}

	result := fs.String()
	if !strings.Contains(result, "fn") || !strings.Contains(result, "add") || !strings.Contains(result, "a, b") {
		t.Errorf("expected string to contain 'fn add(a, b)', got %q", result)
	}
}

func TestFunctionStatementNoParams(t *testing.T) {
	fs := &FunctionStatement{
		Token:  Token{Type: FN, Literal: "fn"},
		Name:   &Identifier{Token: Token{Type: IDENT, Literal: "noop"}, Value: "noop"},
		Params: []*Identifier{},
		Body: &BlockStatement{
			Token:      Token{Type: LBRACE, Literal: "{"},
			Statements: []Statement{},
		},
	}

	result := fs.String()
	if !strings.Contains(result, "fn noop()") {
		t.Errorf("expected string to contain 'fn noop()', got %q", result)
	}
}

func TestProgramString(t *testing.T) {
	prog := &Program{
		Statements: []Statement{
			&LetStatement{
				Token: Token{Type: LET, Literal: "let"},
				Name:  &Identifier{Token: Token{Type: IDENT, Literal: "x"}, Value: "x"},
				Value: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "5"}, Value: 5},
			},
			&PrintStatement{
				Token: Token{Type: PRINT, Literal: "print"},
				Value: &Identifier{Token: Token{Type: IDENT, Literal: "x"}, Value: "x"},
			},
		},
	}

	result := prog.String()
	if !strings.Contains(result, "let x = 5;") || !strings.Contains(result, "print x;") {
		t.Errorf("expected program string to contain both statements, got %q", result)
	}
}

func TestProgramTokenLiteral(t *testing.T) {
	// Empty program
	empty := &Program{}
	if empty.TokenLiteral() != "" {
		t.Errorf("expected empty TokenLiteral, got %q", empty.TokenLiteral())
	}

	// Non-empty program
	prog := &Program{
		Statements: []Statement{
			&LetStatement{
				Token: Token{Type: LET, Literal: "let"},
				Name:  &Identifier{Token: Token{Type: IDENT, Literal: "x"}, Value: "x"},
				Value: &NumberLiteral{Token: Token{Type: NUMBER, Literal: "1"}, Value: 1},
			},
		},
	}
	if prog.TokenLiteral() != "let" {
		t.Errorf("expected TokenLiteral %q, got %q", "let", prog.TokenLiteral())
	}
}

