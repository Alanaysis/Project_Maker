package main

import (
	"fmt"
	"testing"
)

func TestParserLetStatement(t *testing.T) {
	tests := []struct {
		input         string
		expectedName  string
		expectedValue interface{}
	}{
		{"let x = 5;", "x", 5.0},
		{"let y = true;", "y", true},
		{"let foobar = y;", "foobar", "y"},
	}

	for _, tt := range tests {
		program := parseProgram(t, tt.input)
		if len(program.Statements) != 1 {
			t.Fatalf("expected 1 statement, got %d", len(program.Statements))
		}

		stmt, ok := program.Statements[0].(*LetStatement)
		if !ok {
			t.Fatalf("expected *LetStatement, got %T", program.Statements[0])
		}

		if stmt.Name.Value != tt.expectedName {
			t.Errorf("expected name %q, got %q", tt.expectedName, stmt.Name.Value)
		}
	}
}

func TestReturnStatement(t *testing.T) {
	input := `return 5;`
	program := parseProgram(t, input)

	if len(program.Statements) != 1 {
		t.Fatalf("expected 1 statement, got %d", len(program.Statements))
	}

	_, ok := program.Statements[0].(*ReturnStatement)
	if !ok {
		t.Fatalf("expected *ReturnStatement, got %T", program.Statements[0])
	}
}

func TestPrintStatement(t *testing.T) {
	input := `print "hello";`
	program := parseProgram(t, input)

	if len(program.Statements) != 1 {
		t.Fatalf("expected 1 statement, got %d", len(program.Statements))
	}

	_, ok := program.Statements[0].(*PrintStatement)
	if !ok {
		t.Fatalf("expected *PrintStatement, got %T", program.Statements[0])
	}
}

func TestFunctionStatement(t *testing.T) {
	input := `fn add(x, y) { return x + y; }`
	program := parseProgram(t, input)

	if len(program.Statements) != 1 {
		t.Fatalf("expected 1 statement, got %d", len(program.Statements))
	}

	stmt, ok := program.Statements[0].(*FunctionStatement)
	if !ok {
		t.Fatalf("expected *FunctionStatement, got %T", program.Statements[0])
	}

	if stmt.Name.Value != "add" {
		t.Errorf("expected function name 'add', got %q", stmt.Name.Value)
	}

	if len(stmt.Params) != 2 {
		t.Fatalf("expected 2 parameters, got %d", len(stmt.Params))
	}

	if stmt.Params[0].Value != "x" {
		t.Errorf("expected first param 'x', got %q", stmt.Params[0].Value)
	}
	if stmt.Params[1].Value != "y" {
		t.Errorf("expected second param 'y', got %q", stmt.Params[1].Value)
	}
}

func TestParserIfStatement(t *testing.T) {
	input := `if x > 5 { print "big"; } else { print "small"; }`
	program := parseProgram(t, input)

	if len(program.Statements) != 1 {
		t.Fatalf("expected 1 statement, got %d", len(program.Statements))
	}

	stmt, ok := program.Statements[0].(*IfStatement)
	if !ok {
		t.Fatalf("expected *IfStatement, got %T", program.Statements[0])
	}

	if stmt.Consequence == nil {
		t.Error("expected consequence to not be nil")
	}
	if stmt.Alternative == nil {
		t.Error("expected alternative to not be nil")
	}
}

func TestParserWhileStatement(t *testing.T) {
	input := `while x > 0 { x = x - 1; }`
	program := parseProgram(t, input)

	if len(program.Statements) != 1 {
		t.Fatalf("expected 1 statement, got %d", len(program.Statements))
	}

	_, ok := program.Statements[0].(*WhileStatement)
	if !ok {
		t.Fatalf("expected *WhileStatement, got %T", program.Statements[0])
	}
}

func TestNumberLiteral(t *testing.T) {
	input := `5;`
	program := parseProgram(t, input)

	stmt, ok := program.Statements[0].(*ExpressionStatement)
	if !ok {
		t.Fatalf("expected *ExpressionStatement, got %T", program.Statements[0])
	}

	literal, ok := stmt.Expression.(*NumberLiteral)
	if !ok {
		t.Fatalf("expected *NumberLiteral, got %T", stmt.Expression)
	}

	if literal.Value != 5.0 {
		t.Errorf("expected 5.0, got %f", literal.Value)
	}
}

func TestStringLiteral(t *testing.T) {
	input := `"hello world";`
	program := parseProgram(t, input)

	stmt, ok := program.Statements[0].(*ExpressionStatement)
	if !ok {
		t.Fatalf("expected *ExpressionStatement, got %T", program.Statements[0])
	}

	literal, ok := stmt.Expression.(*StringLiteral)
	if !ok {
		t.Fatalf("expected *StringLiteral, got %T", stmt.Expression)
	}

	if literal.Value != "hello world" {
		t.Errorf("expected 'hello world', got %q", literal.Value)
	}
}

func TestBooleanLiteral(t *testing.T) {
	tests := []struct {
		input    string
		expected bool
	}{
		{"true;", true},
		{"false;", false},
	}

	for _, tt := range tests {
		program := parseProgram(t, tt.input)
		stmt, ok := program.Statements[0].(*ExpressionStatement)
		if !ok {
			t.Fatalf("expected *ExpressionStatement, got %T", program.Statements[0])
		}

		boolean, ok := stmt.Expression.(*BooleanLiteral)
		if !ok {
			t.Fatalf("expected *BooleanLiteral, got %T", stmt.Expression)
		}

		if boolean.Value != tt.expected {
			t.Errorf("expected %t, got %t", tt.expected, boolean.Value)
		}
	}
}

func TestPrefixExpression(t *testing.T) {
	tests := []struct {
		input    string
		operator string
		value    float64
	}{
		{"-5;", "-", 5.0},
		{"not true;", "not", 0},
	}

	for _, tt := range tests {
		program := parseProgram(t, tt.input)
		stmt, ok := program.Statements[0].(*ExpressionStatement)
		if !ok {
			t.Fatalf("expected *ExpressionStatement, got %T", program.Statements[0])
		}

		exp, ok := stmt.Expression.(*PrefixExpression)
		if !ok {
			t.Fatalf("expected *PrefixExpression, got %T", stmt.Expression)
		}

		if exp.Operator != tt.operator {
			t.Errorf("expected operator %q, got %q", tt.operator, exp.Operator)
		}
	}
}

func TestInfixExpression(t *testing.T) {
	tests := []struct {
		input    string
		left     float64
		operator string
		right    float64
	}{
		{"5 + 5;", 5.0, "+", 5.0},
		{"5 - 5;", 5.0, "-", 5.0},
		{"5 * 5;", 5.0, "*", 5.0},
		{"5 / 5;", 5.0, "/", 5.0},
		{"5 > 5;", 5.0, ">", 5.0},
		{"5 < 5;", 5.0, "<", 5.0},
		{"5 == 5;", 5.0, "==", 5.0},
		{"5 != 5;", 5.0, "!=", 5.0},
	}

	for _, tt := range tests {
		program := parseProgram(t, tt.input)
		stmt, ok := program.Statements[0].(*ExpressionStatement)
		if !ok {
			t.Fatalf("expected *ExpressionStatement, got %T", program.Statements[0])
		}

		exp, ok := stmt.Expression.(*InfixExpression)
		if !ok {
			t.Fatalf("expected *InfixExpression, got %T", stmt.Expression)
		}

		if exp.Operator != tt.operator {
			t.Errorf("expected operator %q, got %q", tt.operator, exp.Operator)
		}
	}
}

func TestOperatorPrecedence(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"-a * b", "((-a) * b)"},
		{"a + b + c", "((a + b) + c)"},
		{"a + b * c", "(a + (b * c))"},
		{"a * b + c", "((a * b) + c)"},
		{"a + b * c + d / e - f", "(((a + (b * c)) + (d / e)) - f)"},
		{"3 + 4; -5 * 5", "(3 + 4)\n((-5) * 5)"},
		{"5 > 4 == 3 < 4", "((5 > 4) == (3 < 4))"},
		{"5 < 4 != 3 > 4", "((5 < 4) != (3 > 4))"},
		{"3 + 4 * 5 == 3 * 1 + 4 * 5", "((3 + (4 * 5)) == ((3 * 1) + (4 * 5)))"},
		{"true", "true"},
		{"false", "false"},
		{"3 > 5 == false", "((3 > 5) == false)"},
		{"3 < 5 == true", "((3 < 5) == true)"},
	}

	for _, tt := range tests {
		program := parseProgram(t, tt.input)
		actual := program.String()
		// Trim trailing newline for comparison
		if actual != "" && actual[len(actual)-1] == '\n' {
			actual = actual[:len(actual)-1]
		}
		if actual != tt.expected {
			t.Errorf("input=%q\nexpected=%q\ngot=%q", tt.input, tt.expected, actual)
		}
	}
}

func TestCallExpression(t *testing.T) {
	input := `add(1, 2 * 3, 4 + 5);`
	program := parseProgram(t, input)

	stmt, ok := program.Statements[0].(*ExpressionStatement)
	if !ok {
		t.Fatalf("expected *ExpressionStatement, got %T", program.Statements[0])
	}

	exp, ok := stmt.Expression.(*CallExpression)
	if !ok {
		t.Fatalf("expected *CallExpression, got %T", stmt.Expression)
	}

	ident, ok := exp.Function.(*Identifier)
	if !ok {
		t.Fatalf("expected *Identifier, got %T", exp.Function)
	}

	if ident.Value != "add" {
		t.Errorf("expected function name 'add', got %q", ident.Value)
	}

	if len(exp.Args) != 3 {
		t.Fatalf("expected 3 arguments, got %d", len(exp.Args))
	}
}

func TestParserErrors(t *testing.T) {
	input := `let x 5;`
	p := NewParser(input)
	p.Parse()

	if len(p.Errors()) == 0 {
		t.Error("expected parser errors, got none")
	}
}

func parseProgram(t *testing.T, input string) *Program {
	t.Helper()
	p := NewParser(input)
	program := p.Parse()

	if len(p.Errors()) > 0 {
		for _, msg := range p.Errors() {
			fmt.Printf("parser error: %s\n", msg)
		}
		t.Fatalf("parser had %d errors", len(p.Errors()))
	}

	return program
}
