package main

import (
	"fmt"
	"math"
	"os"
	"strings"
)

// Interpreter walks the AST and executes the program.
type Interpreter struct {
	env      *Environment
	output   *strings.Builder
	builtins map[string]*BuiltinFunction
}

// NewInterpreter creates a new Interpreter with default builtins.
func NewInterpreter() *Interpreter {
	interp := &Interpreter{
		env:    NewEnvironment(),
		output: &strings.Builder{},
	}
	interp.builtins = map[string]*BuiltinFunction{
		"len":    {Name: "len", Fn: builtinLen},
		"str":    {Name: "str", Fn: builtinStr},
		"number": {Name: "number", Fn: builtinNumber},
		"input":  {Name: "input", Fn: builtinInput},
		"abs":    {Name: "abs", Fn: builtinAbs},
		"sqrt":   {Name: "sqrt", Fn: builtinSqrt},
		"floor":  {Name: "floor", Fn: builtinFloor},
	}
	return interp
}

// Run parses and executes the given source code.
func (interp *Interpreter) Run(source string) error {
	parser := NewParser(source)
	program := parser.Parse()

	if len(parser.Errors()) > 0 {
		return fmt.Errorf("parse errors:\n%s", strings.Join(parser.Errors(), "\n"))
	}

	result := interp.Eval(program)
	if errObj, ok := result.(*Error); ok {
		return fmt.Errorf("runtime error: %s", errObj.Message)
	}

	return nil
}

// Output returns the captured output from print statements.
func (interp *Interpreter) Output() string {
	return interp.output.String()
}

// Eval evaluates a node and returns the result.
func (interp *Interpreter) Eval(node Node) Object {
	switch n := node.(type) {
	// Statements
	case *Program:
		return interp.evalProgram(n)
	case *BlockStatement:
		return interp.evalBlockStatement(n)
	case *LetStatement:
		return interp.evalLetStatement(n)
	case *AssignStatement:
		return interp.evalAssignStatement(n)
	case *ReturnStatement:
		return interp.evalReturnStatement(n)
	case *PrintStatement:
		return interp.evalPrintStatement(n)
	case *ExpressionStatement:
		return interp.Eval(n.Expression)
	case *IfStatement:
		return interp.evalIfStatement(n)
	case *WhileStatement:
		return interp.evalWhileStatement(n)
	case *FunctionStatement:
		return interp.evalFunctionStatement(n)

	// Expressions
	case *NumberLiteral:
		return &Number{Value: n.Value}
	case *StringLiteral:
		return &Str{Value: n.Value}
	case *BooleanLiteral:
		return &Boolean{Value: n.Value}
	case *Identifier:
		return interp.evalIdentifier(n)
	case *PrefixExpression:
		return interp.evalPrefixExpression(n)
	case *InfixExpression:
		return interp.evalInfixExpression(n)
	case *CallExpression:
		return interp.evalCallExpression(n)

	default:
		return &Error{Message: fmt.Sprintf("unknown node type: %T", node)}
	}
}

// Error represents a runtime error.
type Error struct {
	Message string
}

func (e *Error) Type() ObjectType { return "ERROR" }
func (e *Error) Inspect() string  { return "ERROR: " + e.Message }

// evalProgram evaluates all statements in a program.
func (interp *Interpreter) evalProgram(program *Program) Object {
	var result Object

	for _, statement := range program.Statements {
		result = interp.Eval(statement)

		switch r := result.(type) {
		case *ReturnValue:
			return r.Value
		case *Error:
			return r
		}
	}

	return result
}

// evalBlockStatement evaluates all statements in a block.
func (interp *Interpreter) evalBlockStatement(block *BlockStatement) Object {
	var result Object

	for _, statement := range block.Statements {
		result = interp.Eval(statement)

		if result != nil {
			rt := result.Type()
			if rt == RETURN_OBJ || rt == "ERROR" {
				return result
			}
		}
	}

	return result
}

// evalLetStatement evaluates a let statement.
func (interp *Interpreter) evalLetStatement(stmt *LetStatement) Object {
	val := interp.Eval(stmt.Value)
	if isError(val) {
		return val
	}

	interp.env.Set(stmt.Name.Value, val)
	return val
}

// evalAssignStatement evaluates an assignment statement.
func (interp *Interpreter) evalAssignStatement(stmt *AssignStatement) Object {
	_, ok := interp.env.Get(stmt.Name.Value)
	if !ok {
		return &Error{Message: fmt.Sprintf("undefined variable: %s", stmt.Name.Value)}
	}

	val := interp.Eval(stmt.Value)
	if isError(val) {
		return val
	}

	// Update the variable in the scope where it was originally defined
	if !interp.env.Update(stmt.Name.Value, val) {
		return &Error{Message: fmt.Sprintf("undefined variable: %s", stmt.Name.Value)}
	}
	return val
}

// evalReturnStatement evaluates a return statement.
func (interp *Interpreter) evalReturnStatement(stmt *ReturnStatement) Object {
	val := interp.Eval(stmt.ReturnValue)
	if isError(val) {
		return val
	}
	return &ReturnValue{Value: val}
}

// evalPrintStatement evaluates a print statement.
func (interp *Interpreter) evalPrintStatement(stmt *PrintStatement) Object {
	val := interp.Eval(stmt.Value)
	if isError(val) {
		return val
	}

	interp.output.WriteString(val.Inspect() + "\n")
	return val
}

// evalIfStatement evaluates an if-else statement.
func (interp *Interpreter) evalIfStatement(stmt *IfStatement) Object {
	condition := interp.Eval(stmt.Condition)
	if isError(condition) {
		return condition
	}

	if isTruthy(condition) {
		return interp.Eval(stmt.Consequence)
	} else if stmt.Alternative != nil {
		return interp.Eval(stmt.Alternative)
	}

	return &Null{}
}

// evalWhileStatement evaluates a while loop.
func (interp *Interpreter) evalWhileStatement(stmt *WhileStatement) Object {
	var result Object

	for {
		condition := interp.Eval(stmt.Condition)
		if isError(condition) {
			return condition
		}

		if !isTruthy(condition) {
			break
		}

		result = interp.Eval(stmt.Body)
		if result != nil {
			rt := result.Type()
			if rt == RETURN_OBJ || rt == "ERROR" {
				return result
			}
		}
	}

	if result == nil {
		return &Null{}
	}
	return result
}

// evalFunctionStatement evaluates a function declaration.
func (interp *Interpreter) evalFunctionStatement(stmt *FunctionStatement) Object {
	fn := &Function{
		Params: stmt.Params,
		Body:   stmt.Body,
		Env:    interp.env,
	}
	interp.env.Set(stmt.Name.Value, fn)
	return fn
}

// evalIdentifier evaluates an identifier.
func (interp *Interpreter) evalIdentifier(node *Identifier) Object {
	if val, ok := interp.env.Get(node.Value); ok {
		return val
	}

	if builtin, ok := interp.builtins[node.Value]; ok {
		return builtin
	}

	return &Error{Message: fmt.Sprintf("undefined variable: %s", node.Value)}
}

// evalPrefixExpression evaluates a prefix expression.
func (interp *Interpreter) evalPrefixExpression(expr *PrefixExpression) Object {
	right := interp.Eval(expr.Right)
	if isError(right) {
		return right
	}

	switch expr.Operator {
	case "-":
		return evalMinusPrefix(right)
	case "not":
		return evalNotPrefix(right)
	default:
		return &Error{Message: fmt.Sprintf("unknown operator: %s%s", expr.Operator, right.Type())}
	}
}

// evalMinusPrefix evaluates negation.
func evalMinusPrefix(right Object) Object {
	if right.Type() != NUMBER_OBJ {
		return &Error{Message: fmt.Sprintf("unknown operator: -%s", right.Type())}
	}
	return &Number{Value: -right.(*Number).Value}
}

// evalNotPrefix evaluates logical not.
func evalNotPrefix(right Object) Object {
	switch r := right.(type) {
	case *Boolean:
		return &Boolean{Value: !r.Value}
	case *Null:
		return &Boolean{Value: true}
	default:
		return &Boolean{Value: false}
	}
}

// evalInfixExpression evaluates an infix expression.
func (interp *Interpreter) evalInfixExpression(expr *InfixExpression) Object {
	left := interp.Eval(expr.Left)
	if isError(left) {
		return left
	}

	right := interp.Eval(expr.Right)
	if isError(right) {
		return right
	}

	// String concatenation
	if left.Type() == STRING_OBJ && right.Type() == STRING_OBJ {
		return evalStringInfix(expr.Operator, left.(*Str), right.(*Str))
	}

	// String concatenation with number
	if left.Type() == STRING_OBJ && right.Type() == NUMBER_OBJ {
		if expr.Operator == "+" {
			return &Str{Value: left.(*Str).Value + right.(*Number).Inspect()}
		}
	}

	if left.Type() == NUMBER_OBJ && right.Type() == STRING_OBJ {
		if expr.Operator == "+" {
			return &Str{Value: left.(*Number).Inspect() + right.(*Str).Value}
		}
	}

	// Numeric operations
	if left.Type() == NUMBER_OBJ && right.Type() == NUMBER_OBJ {
		return evalNumberInfix(expr.Operator, left.(*Number), right.(*Number))
	}

	// Boolean operations
	if left.Type() == BOOLEAN_OBJ && right.Type() == BOOLEAN_OBJ {
		return evalBooleanInfix(expr.Operator, left.(*Boolean), right.(*Boolean))
	}

	// Equality for different types
	if expr.Operator == "==" {
		return &Boolean{Value: left.Type() == right.Type() && left.Inspect() == right.Inspect()}
	}
	if expr.Operator == "!=" {
		return &Boolean{Value: !(left.Type() == right.Type() && left.Inspect() == right.Inspect())}
	}

	return &Error{Message: fmt.Sprintf("type mismatch: %s %s %s", left.Type(), expr.Operator, right.Type())}
}

// evalNumberInfix evaluates an infix expression on two numbers.
func evalNumberInfix(op string, left, right *Number) Object {
	switch op {
	case "+":
		return &Number{Value: left.Value + right.Value}
	case "-":
		return &Number{Value: left.Value - right.Value}
	case "*":
		return &Number{Value: left.Value * right.Value}
	case "/":
		if right.Value == 0 {
			return &Error{Message: "division by zero"}
		}
		return &Number{Value: left.Value / right.Value}
	case "%":
		return &Number{Value: math.Mod(left.Value, right.Value)}
	case "<":
		return &Boolean{Value: left.Value < right.Value}
	case ">":
		return &Boolean{Value: left.Value > right.Value}
	case "<=":
		return &Boolean{Value: left.Value <= right.Value}
	case ">=":
		return &Boolean{Value: left.Value >= right.Value}
	case "==":
		return &Boolean{Value: left.Value == right.Value}
	case "!=":
		return &Boolean{Value: left.Value != right.Value}
	case "and":
		return &Number{Value: left.Value} // truthy
	case "or":
		return &Number{Value: left.Value}
	default:
		return &Error{Message: fmt.Sprintf("unknown operator: NUMBER %s NUMBER", op)}
	}
}

// evalStringInfix evaluates an infix expression on two strings.
func evalStringInfix(op string, left, right *Str) Object {
	switch op {
	case "+":
		return &Str{Value: left.Value + right.Value}
	case "==":
		return &Boolean{Value: left.Value == right.Value}
	case "!=":
		return &Boolean{Value: left.Value != right.Value}
	case "<":
		return &Boolean{Value: left.Value < right.Value}
	case ">":
		return &Boolean{Value: left.Value > right.Value}
	default:
		return &Error{Message: fmt.Sprintf("unknown operator: STRING %s STRING", op)}
	}
}

// evalBooleanInfix evaluates an infix expression on two booleans.
func evalBooleanInfix(op string, left, right *Boolean) Object {
	switch op {
	case "==":
		return &Boolean{Value: left.Value == right.Value}
	case "!=":
		return &Boolean{Value: left.Value != right.Value}
	case "and":
		return &Boolean{Value: left.Value && right.Value}
	case "or":
		return &Boolean{Value: left.Value || right.Value}
	default:
		return &Error{Message: fmt.Sprintf("unknown operator: BOOLEAN %s BOOLEAN", op)}
	}
}

// evalCallExpression evaluates a function call.
func (interp *Interpreter) evalCallExpression(expr *CallExpression) Object {
	fn := interp.Eval(expr.Function)
	if isError(fn) {
		return fn
	}

	args := evalExpressions(expr.Args, interp)
	if len(args) == 1 && isError(args[0]) {
		return args[0]
	}

	switch fn := fn.(type) {
	case *Function:
		return applyFunction(fn, args)
	case *BuiltinFunction:
		return fn.Fn(args...)
	default:
		return &Error{Message: fmt.Sprintf("not a function: %s", fn.Type())}
	}
}

// evalExpressions evaluates a list of expressions.
func evalExpressions(exps []Expression, interp *Interpreter) []Object {
	var result []Object

	for _, e := range exps {
		evaluated := interp.Eval(e)
		if isError(evaluated) {
			return []Object{evaluated}
		}
		result = append(result, evaluated)
	}

	return result
}

// applyFunction applies a user-defined function to arguments.
func applyFunction(fn *Function, args []Object) Object {
	if len(args) != len(fn.Params) {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected %d, got %d", len(fn.Params), len(args))}
	}

	// Create a new enclosed environment for the function scope
	extendedEnv := NewEnclosedEnvironment(fn.Env)

	// Bind parameters to arguments
	for i, param := range fn.Params {
		extendedEnv.Set(param.Value, args[i])
	}

	// Evaluate the function body
	result := interpEvalBlock(fn.Body, extendedEnv)

	// Unwrap return values
	if retVal, ok := result.(*ReturnValue); ok {
		return retVal.Value
	}

	return result
}

// interpEvalBlock evaluates a block in a given environment.
func interpEvalBlock(block *BlockStatement, env *Environment) Object {
	interp := &Interpreter{env: env, output: &strings.Builder{}}
	// Copy builtins reference
	interp.builtins = map[string]*BuiltinFunction{
		"len":    {Name: "len", Fn: builtinLen},
		"str":    {Name: "str", Fn: builtinStr},
		"number": {Name: "number", Fn: builtinNumber},
		"input":  {Name: "input", Fn: builtinInput},
		"abs":    {Name: "abs", Fn: builtinAbs},
		"sqrt":   {Name: "sqrt", Fn: builtinSqrt},
		"floor":  {Name: "floor", Fn: builtinFloor},
	}

	var result Object
	for _, statement := range block.Statements {
		result = interp.Eval(statement)
		if result != nil {
			rt := result.Type()
			if rt == RETURN_OBJ || rt == "ERROR" {
				return result
			}
		}
	}
	return result
}

// isTruthy determines if a value is truthy.
func isTruthy(obj Object) bool {
	switch o := obj.(type) {
	case *Boolean:
		return o.Value
	case *Null:
		return false
	case *Number:
		return o.Value != 0
	case *Str:
		return o.Value != ""
	default:
		return true
	}
}

// isError checks if an object is an error.
func isError(obj Object) bool {
	if obj != nil {
		return obj.Type() == "ERROR"
	}
	return false
}

// ---------- Built-in Functions ----------

func builtinLen(args ...Object) Object {
	if len(args) != 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
	}
	switch arg := args[0].(type) {
	case *Str:
		return &Number{Value: float64(len(arg.Value))}
	default:
		return &Error{Message: fmt.Sprintf("argument to `len` not supported, got %s", arg.Type())}
	}
}

func builtinStr(args ...Object) Object {
	if len(args) != 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
	}
	return &Str{Value: args[0].Inspect()}
}

func builtinNumber(args ...Object) Object {
	if len(args) != 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
	}
	switch arg := args[0].(type) {
	case *Str:
		var val float64
		_, err := fmt.Sscanf(arg.Value, "%f", &val)
		if err != nil {
			return &Error{Message: fmt.Sprintf("cannot convert %q to number", arg.Value)}
		}
		return &Number{Value: val}
	case *Number:
		return arg
	case *Boolean:
		if arg.Value {
			return &Number{Value: 1}
		}
		return &Number{Value: 0}
	default:
		return &Error{Message: fmt.Sprintf("argument to `number` not supported, got %s", arg.Type())}
	}
}

func builtinInput(args ...Object) Object {
	if len(args) > 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 0 or 1, got %d", len(args))}
	}
	if len(args) == 1 {
		if prompt, ok := args[0].(*Str); ok {
			fmt.Print(prompt.Value)
		}
	}
	var input string
	fmt.Scanln(&input)
	return &Str{Value: input}
}

func builtinAbs(args ...Object) Object {
	if len(args) != 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
	}
	if num, ok := args[0].(*Number); ok {
		return &Number{Value: math.Abs(num.Value)}
	}
	return &Error{Message: fmt.Sprintf("argument to `abs` not supported, got %s", args[0].Type())}
}

func builtinSqrt(args ...Object) Object {
	if len(args) != 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
	}
	if num, ok := args[0].(*Number); ok {
		if num.Value < 0 {
			return &Error{Message: "cannot compute square root of negative number"}
		}
		return &Number{Value: math.Sqrt(num.Value)}
	}
	return &Error{Message: fmt.Sprintf("argument to `sqrt` not supported, got %s", args[0].Type())}
}

func builtinFloor(args ...Object) Object {
	if len(args) != 1 {
		return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
	}
	if num, ok := args[0].(*Number); ok {
		return &Number{Value: math.Floor(num.Value)}
	}
	return &Error{Message: fmt.Sprintf("argument to `floor` not supported, got %s", args[0].Type())}
}

// RunFile executes a script file.
func RunFile(filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("could not read file: %w", err)
	}

	interp := NewInterpreter()
	err = interp.Run(string(data))
	if err != nil {
		return err
	}

	output := interp.Output()
	if output != "" {
		fmt.Print(output)
	}

	return nil
}
