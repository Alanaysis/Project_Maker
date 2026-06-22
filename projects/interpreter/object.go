package main

import "fmt"

// ObjectType represents the type of a runtime object.
type ObjectType string

const (
	NUMBER_OBJ   ObjectType = "NUMBER"
	STRING_OBJ   ObjectType = "STRING"
	BOOLEAN_OBJ  ObjectType = "BOOLEAN"
	NULL_OBJ     ObjectType = "NULL"
	RETURN_OBJ   ObjectType = "RETURN"
	FUNCTION_OBJ ObjectType = "FUNCTION"
	BUILTIN_OBJ  ObjectType = "BUILTIN"
)

// Object represents a runtime value.
type Object interface {
	Type() ObjectType
	Inspect() string
}

// Number represents a numeric value.
type Number struct {
	Value float64
}

func (n *Number) Type() ObjectType { return NUMBER_OBJ }
func (n *Number) Inspect() string  { return fmt.Sprintf("%g", n.Value) }

// String represents a string value.
type Str struct {
	Value string
}

func (s *Str) Type() ObjectType { return STRING_OBJ }
func (s *Str) Inspect() string  { return s.Value }

// Boolean represents a boolean value.
type Boolean struct {
	Value bool
}

func (b *Boolean) Type() ObjectType { return BOOLEAN_OBJ }
func (b *Boolean) Inspect() string  { return fmt.Sprintf("%t", b.Value) }

// Null represents the absence of a value.
type Null struct{}

func (n *Null) Type() ObjectType { return NULL_OBJ }
func (n *Null) Inspect() string  { return "null" }

// ReturnValue wraps a return value to unwind the call stack.
type ReturnValue struct {
	Value Object
}

func (rv *ReturnValue) Type() ObjectType { return RETURN_OBJ }
func (rv *ReturnValue) Inspect() string  { return rv.Value.Inspect() }

// Function represents a user-defined function.
type Function struct {
	Params []*Identifier
	Body   *BlockStatement
	Env    *Environment
}

func (f *Function) Type() ObjectType { return FUNCTION_OBJ }
func (f *Function) Inspect() string {
	params := ""
	for i, p := range f.Params {
		if i > 0 {
			params += ", "
		}
		params += p.String()
	}
	return "fn(" + params + ") { ... }"
}

// BuiltinFunction is a function built into the interpreter.
type BuiltinFunction struct {
	Name string
	Fn   func(args ...Object) Object
}

func (bf *BuiltinFunction) Type() ObjectType { return BUILTIN_OBJ }
func (bf *BuiltinFunction) Inspect() string  { return "builtin function: " + bf.Name }
