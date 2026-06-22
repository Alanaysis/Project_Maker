package main

import (
	"strings"
	"testing"
)

func TestNumberExpressions(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"5", "5"},
		{"10", "10"},
		{"-5", "-5"},
		{"5 + 5", "10"},
		{"5 - 3", "2"},
		{"4 * 3", "12"},
		{"10 / 2", "5"},
		{"2 + 3 * 4", "14"},
		{"(2 + 3) * 4", "20"},
		{"10 - 2 - 3", "5"},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run("print " + tt.input + ";")
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %s, got %s", tt.input, tt.expected, output)
		}
	}
}

func TestBooleanExpressions(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"true", "true"},
		{"false", "false"},
		{"1 < 2", "true"},
		{"1 > 2", "false"},
		{"1 == 1", "true"},
		{"1 != 2", "true"},
		{"true and true", "true"},
		{"true and false", "false"},
		{"true or false", "true"},
		{"not false", "true"},
		{"not true", "false"},
		{"1 <= 1", "true"},
		{"1 >= 2", "false"},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run("print " + tt.input + ";")
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %s, got %s", tt.input, tt.expected, output)
		}
	}
}

func TestStringExpressions(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{`"hello"`, "hello"},
		{`"hello" + " " + "world"`, "hello world"},
		{`"hello" == "hello"`, "true"},
		{`"hello" != "world"`, "true"},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run("print " + tt.input + ";")
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %q, got %q", tt.input, tt.expected, output)
		}
	}
}

func TestLetStatement(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"let x = 5; print x;", "5"},
		{"let x = 5; let y = 10; print x + y;", "15"},
		{`let name = "world"; print "hello " + name;`, "hello world"},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run(tt.input)
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %q, got %q", tt.input, tt.expected, output)
		}
	}
}

func TestAssignStatement(t *testing.T) {
	input := `
		let x = 1;
		x = 2;
		print x;
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "2" {
		t.Errorf("expected '2', got %q", output)
	}
}

func TestIfStatement(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{`if true { print "yes"; }`, "yes"},
		{`if false { print "yes"; } else { print "no"; }`, "no"},
		{`if 1 > 2 { print "yes"; } else { print "no"; }`, "no"},
		{`if 2 > 1 { print "yes"; } else { print "no"; }`, "yes"},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run(tt.input)
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %q, got %q", tt.input, tt.expected, output)
		}
	}
}

func TestWhileStatement(t *testing.T) {
	input := `
		let x = 0;
		let sum = 0;
		while x < 5 {
			x = x + 1;
			sum = sum + x;
		}
		print sum;
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "15" {
		t.Errorf("expected '15', got %q", output)
	}
}

func TestFunction(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{
			`
			fn add(a, b) {
				return a + b;
			}
			print add(1, 2);
			`,
			"3",
		},
		{
			`
			fn greet(name) {
				return "hello " + name;
			}
			print greet("world");
			`,
			"hello world",
		},
		{
			`
			let x = 10;
			fn addX(n) {
				return n + x;
			}
			print addX(5);
			`,
			"15",
		},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run(tt.input)
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %q, got %q", tt.input, tt.expected, output)
		}
	}
}

func TestRecursion(t *testing.T) {
	input := `
		fn factorial(n) {
			if n <= 1 {
				return 1;
			}
			return n * factorial(n - 1);
		}
		print factorial(5);
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "120" {
		t.Errorf("expected '120', got %q", output)
	}
}

func TestFibonacci(t *testing.T) {
	input := `
		fn fib(n) {
			if n <= 1 {
				return n;
			}
			return fib(n - 1) + fib(n - 2);
		}
		print fib(10);
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "55" {
		t.Errorf("expected '55', got %q", output)
	}
}

func TestScope(t *testing.T) {
	input := `
		let x = 10;
		fn test() {
			let x = 20;
			return x;
		}
		print test();
		print x;
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	expected := "20\n10"
	if output != expected {
		t.Errorf("expected %q, got %q", expected, output)
	}
}

func TestClosures(t *testing.T) {
	input := `
		fn makeCounter() {
			let count = 0;
			fn increment() {
				count = count + 1;
				return count;
			}
			return increment;
		}
		let counter = makeCounter();
		print counter();
		print counter();
		print counter();
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	expected := "1\n2\n3"
	if output != expected {
		t.Errorf("expected %q, got %q", expected, output)
	}
}

func TestBuiltins(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{`print len("hello");`, "5"},
		{`print len("");`, "0"},
		{`print str(42);`, "42"},
		{`print abs(-5);`, "5"},
		{`print abs(5);`, "5"},
		{`print sqrt(16);`, "4"},
		{`print floor(3.7);`, "3"},
	}

	for _, tt := range tests {
		interp := NewInterpreter()
		err := interp.Run(tt.input)
		if err != nil {
			t.Errorf("input=%q: %s", tt.input, err)
			continue
		}
		output := strings.TrimSpace(interp.Output())
		if output != tt.expected {
			t.Errorf("input=%q: expected %q, got %q", tt.input, tt.expected, output)
		}
	}
}

func TestComments(t *testing.T) {
	input := `
		// This is a comment
		let x = 5; // inline comment
		print x;
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "5" {
		t.Errorf("expected '5', got %q", output)
	}
}

func TestDivisionByZero(t *testing.T) {
	input := `print 10 / 0;`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err == nil {
		t.Error("expected error for division by zero")
	}
}

func TestUndefinedVariable(t *testing.T) {
	input := `print x;`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err == nil {
		t.Error("expected error for undefined variable")
	}
}

func TestParserError(t *testing.T) {
	input := `let 5 = x;`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err == nil {
		t.Error("expected parser error")
	}
}

func TestMultipleStatements(t *testing.T) {
	input := `
		let a = 1;
		let b = 2;
		let c = 3;
		print a + b + c;
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "6" {
		t.Errorf("expected '6', got %q", output)
	}
}

func TestNestedBlocks(t *testing.T) {
	input := `
		let x = 1;
		if true {
			let y = 2;
			print x + y;
		}
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "3" {
		t.Errorf("expected '3', got %q", output)
	}
}

func TestHigherOrderFunction(t *testing.T) {
	input := `
		fn apply(f, x) {
			return f(x);
		}
		fn double(n) {
			return n * 2;
		}
		print apply(double, 5);
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "10" {
		t.Errorf("expected '10', got %q", output)
	}
}

func TestNestedIf(t *testing.T) {
	input := `
		let x = 10;
		if x > 5 {
			if x > 8 {
				print "big";
			} else {
				print "medium";
			}
		} else {
			print "small";
		}
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	if output != "big" {
		t.Errorf("expected 'big', got %q", output)
	}
}

func TestWhileConditionalBreak(t *testing.T) {
	input := `
		let i = 0;
		let sum = 0;
		while i < 10 {
			i = i + 1;
			sum = sum + i;
		}
		print sum;
	`
	interp := NewInterpreter()
	err := interp.Run(input)
	if err != nil {
		t.Fatal(err)
	}
	output := strings.TrimSpace(interp.Output())
	// Sum of 1 to 10 = 55
	if output != "55" {
		t.Errorf("expected '55', got %q", output)
	}
}
