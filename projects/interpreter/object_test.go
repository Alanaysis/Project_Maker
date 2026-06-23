package main

import "testing"

func TestNumberObject(t *testing.T) {
	n := &Number{Value: 42.0}
	if n.Type() != NUMBER_OBJ {
		t.Errorf("expected type %s, got %s", NUMBER_OBJ, n.Type())
	}
	if n.Inspect() != "42" {
		t.Errorf("expected inspect %q, got %q", "42", n.Inspect())
	}
}

func TestNumberObjectFloat(t *testing.T) {
	n := &Number{Value: 3.14}
	if n.Inspect() != "3.14" {
		t.Errorf("expected inspect %q, got %q", "3.14", n.Inspect())
	}
}

func TestNumberObjectNegative(t *testing.T) {
	n := &Number{Value: -5.0}
	if n.Inspect() != "-5" {
		t.Errorf("expected inspect %q, got %q", "-5", n.Inspect())
	}
}

func TestNumberObjectZero(t *testing.T) {
	n := &Number{Value: 0}
	if n.Inspect() != "0" {
		t.Errorf("expected inspect %q, got %q", "0", n.Inspect())
	}
}

func TestStringObject(t *testing.T) {
	s := &Str{Value: "hello"}
	if s.Type() != STRING_OBJ {
		t.Errorf("expected type %s, got %s", STRING_OBJ, s.Type())
	}
	if s.Inspect() != "hello" {
		t.Errorf("expected inspect %q, got %q", "hello", s.Inspect())
	}
}

func TestStringObjectEmpty(t *testing.T) {
	s := &Str{Value: ""}
	if s.Inspect() != "" {
		t.Errorf("expected empty inspect, got %q", s.Inspect())
	}
}

func TestBooleanObject(t *testing.T) {
	tests := []struct {
		value    bool
		expected string
	}{
		{true, "true"},
		{false, "false"},
	}

	for _, tt := range tests {
		b := &Boolean{Value: tt.value}
		if b.Type() != BOOLEAN_OBJ {
			t.Errorf("expected type %s, got %s", BOOLEAN_OBJ, b.Type())
		}
		if b.Inspect() != tt.expected {
			t.Errorf("Boolean(%t).Inspect() = %q, expected %q", tt.value, b.Inspect(), tt.expected)
		}
	}
}

func TestNullObject(t *testing.T) {
	n := &Null{}
	if n.Type() != NULL_OBJ {
		t.Errorf("expected type %s, got %s", NULL_OBJ, n.Type())
	}
	if n.Inspect() != "null" {
		t.Errorf("expected inspect %q, got %q", "null", n.Inspect())
	}
}

func TestReturnValue(t *testing.T) {
	inner := &Number{Value: 42}
	rv := &ReturnValue{Value: inner}

	if rv.Type() != RETURN_OBJ {
		t.Errorf("expected type %s, got %s", RETURN_OBJ, rv.Type())
	}
	if rv.Inspect() != "42" {
		t.Errorf("expected inspect %q, got %q", "42", rv.Inspect())
	}
}

func TestReturnValueString(t *testing.T) {
	inner := &Str{Value: "hello"}
	rv := &ReturnValue{Value: inner}

	if rv.Inspect() != "hello" {
		t.Errorf("expected inspect %q, got %q", "hello", rv.Inspect())
	}
}

func TestFunctionObject(t *testing.T) {
	params := []*Identifier{
		{Value: "a"},
		{Value: "b"},
	}
	body := &BlockStatement{}
	env := NewEnvironment()

	fn := &Function{Params: params, Body: body, Env: env}

	if fn.Type() != FUNCTION_OBJ {
		t.Errorf("expected type %s, got %s", FUNCTION_OBJ, fn.Type())
	}

	expected := "fn(a, b) { ... }"
	if fn.Inspect() != expected {
		t.Errorf("expected inspect %q, got %q", expected, fn.Inspect())
	}
}

func TestFunctionObjectNoParams(t *testing.T) {
	fn := &Function{
		Params: []*Identifier{},
		Body:   &BlockStatement{},
		Env:    NewEnvironment(),
	}

	expected := "fn() { ... }"
	if fn.Inspect() != expected {
		t.Errorf("expected inspect %q, got %q", expected, fn.Inspect())
	}
}

func TestBuiltinFunctionObject(t *testing.T) {
	bf := &BuiltinFunction{
		Name: "len",
		Fn:   builtinLen,
	}

	if bf.Type() != BUILTIN_OBJ {
		t.Errorf("expected type %s, got %s", BUILTIN_OBJ, bf.Type())
	}

	expected := "builtin function: len"
	if bf.Inspect() != expected {
		t.Errorf("expected inspect %q, got %q", expected, bf.Inspect())
	}
}

func TestErrorObject(t *testing.T) {
	e := &Error{Message: "something went wrong"}

	if e.Type() != "ERROR" {
		t.Errorf("expected type %q, got %q", "ERROR", e.Type())
	}

	expected := "ERROR: something went wrong"
	if e.Inspect() != expected {
		t.Errorf("expected inspect %q, got %q", expected, e.Inspect())
	}
}
