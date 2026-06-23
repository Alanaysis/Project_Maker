use std::collections::HashMap;
use crate::codegen::{FunctionInfo, Instruction};

/// Runtime values
#[derive(Debug, Clone)]
pub enum Value {
    Int(i64),
    Float(f64),
    Bool(bool),
    Str(String),
}

impl std::fmt::Display for Value {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Value::Int(n) => write!(f, "{}", n),
            Value::Float(v) => write!(f, "{}", v),
            Value::Bool(b) => write!(f, "{}", b),
            Value::Str(s) => write!(f, "{}", s),
        }
    }
}

impl PartialEq for Value {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => a == b,
            (Value::Bool(a), Value::Bool(b)) => a == b,
            (Value::Str(a), Value::Str(b)) => a == b,
            (Value::Int(a), Value::Float(b)) => (*a as f64) == *b,
            (Value::Float(a), Value::Int(b)) => *a == (*b as f64),
            _ => false,
        }
    }
}

/// Stack frame for function calls
struct Frame {
    locals: HashMap<String, Value>,
    return_addr: usize,
    param_names: Vec<String>,
}

/// Stack-based virtual machine
///
/// Executes bytecode instructions. The VM maintains:
/// - A value stack for expression evaluation
/// - Local variable storage per function frame
/// - A call stack for function calls
pub struct VM {
    instructions: Vec<Instruction>,
    functions: HashMap<String, FunctionInfo>,
    stack: Vec<Value>,
    call_stack: Vec<Frame>,
    globals: HashMap<String, Value>,
    pc: usize, // program counter
    output: Vec<String>,
}

impl VM {
    pub fn new(instructions: Vec<Instruction>, functions: Vec<FunctionInfo>) -> Self {
        let func_map: HashMap<String, FunctionInfo> =
            functions.into_iter().map(|f| (f.name.clone(), f)).collect();

        Self {
            instructions,
            functions: func_map,
            stack: Vec::new(),
            call_stack: Vec::new(),
            globals: HashMap::new(),
            pc: 0,
            output: Vec::new(),
        }
    }

    /// Run the bytecode to completion
    pub fn run(&mut self) -> Result<Vec<String>, String> {
        while self.pc < self.instructions.len() {
            let inst = self.instructions[self.pc].clone();
            self.pc += 1;
            self.execute(inst)?;
        }
        Ok(self.output.clone())
    }

    fn execute(&mut self, inst: Instruction) -> Result<(), String> {
        match inst {
            // Stack operations
            Instruction::PushInt(n) => self.stack.push(Value::Int(n)),
            Instruction::PushFloat(f) => self.stack.push(Value::Float(f)),
            Instruction::PushBool(b) => self.stack.push(Value::Bool(b)),
            Instruction::PushStr(s) => self.stack.push(Value::Str(s)),
            Instruction::Pop => {
                self.stack.pop().ok_or("Stack underflow on Pop")?;
            }
            Instruction::Dup => {
                let val = self.stack.last().ok_or("Stack underflow on Dup")?.clone();
                self.stack.push(val);
            }

            // Local variables
            Instruction::LoadLocal(name) => {
                let value = self.resolve_variable(&name)?;
                self.stack.push(value);
            }
            Instruction::StoreLocal(name) => {
                let value = self.stack.pop().ok_or("Stack underflow on StoreLocal")?;
                self.set_variable(name, value);
            }

            // Arithmetic
            Instruction::Add => self.binary_op(|a, b| match (a, b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Int(a + b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a + b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Float(a as f64 + b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Float(a + b as f64)),
                (Value::Str(a), Value::Str(b)) => Ok(Value::Str(format!("{}{}", a, b))),
                (a, b) => Err(format!("Cannot add {:?} and {:?}", a, b)),
            })?,
            Instruction::Sub => self.binary_op(|a, b| match (a, b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Int(a - b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a - b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Float(a as f64 - b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Float(a - b as f64)),
                (a, b) => Err(format!("Cannot subtract {:?} and {:?}", a, b)),
            })?,
            Instruction::Mul => self.binary_op(|a, b| match (a, b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Int(a * b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a * b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Float(a as f64 * b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Float(a * b as f64)),
                (a, b) => Err(format!("Cannot multiply {:?} and {:?}", a, b)),
            })?,
            Instruction::Div => self.binary_op(|a, b| match (a, b) {
                (Value::Int(a), Value::Int(b)) => {
                    if b == 0 {
                        Err("Division by zero".to_string())
                    } else {
                        Ok(Value::Int(a / b))
                    }
                }
                (Value::Float(a), Value::Float(b)) => {
                    if b == 0.0 {
                        Err("Division by zero".to_string())
                    } else {
                        Ok(Value::Float(a / b))
                    }
                }
                (Value::Int(a), Value::Float(b)) => {
                    if b == 0.0 {
                        Err("Division by zero".to_string())
                    } else {
                        Ok(Value::Float(a as f64 / b))
                    }
                }
                (Value::Float(a), Value::Int(b)) => {
                    if b == 0 {
                        Err("Division by zero".to_string())
                    } else {
                        Ok(Value::Float(a / b as f64))
                    }
                }
                (a, b) => Err(format!("Cannot divide {:?} and {:?}", a, b)),
            })?,
            Instruction::Mod => self.binary_op(|a, b| match (a, b) {
                (Value::Int(a), Value::Int(b)) => {
                    if b == 0 {
                        Err("Division by zero".to_string())
                    } else {
                        Ok(Value::Int(a % b))
                    }
                }
                (a, b) => Err(format!("Cannot modulo {:?} and {:?}", a, b)),
            })?,
            Instruction::Neg => {
                let val = self.stack.pop().ok_or("Stack underflow on Neg")?;
                match val {
                    Value::Int(n) => self.stack.push(Value::Int(-n)),
                    Value::Float(f) => self.stack.push(Value::Float(-f)),
                    _ => return Err(format!("Cannot negate {:?}", val)),
                }
            }

            // Comparison
            Instruction::Eq => self.binary_op(|a, b| Ok(Value::Bool(a == b)))?,
            Instruction::NotEq => self.binary_op(|a, b| Ok(Value::Bool(a != b)))?,
            Instruction::Lt => self.binary_op(|a, b| match (&a, &b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Bool(a < b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Bool(a < b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Bool((*a as f64) < *b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Bool(*a < (*b as f64))),
                _ => Err(format!("Cannot compare {:?} and {:?}", a, b)),
            })?,
            Instruction::LtEq => self.binary_op(|a, b| match (&a, &b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Bool(a <= b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Bool(a <= b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Bool((*a as f64) <= *b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Bool(*a <= (*b as f64))),
                _ => Err(format!("Cannot compare {:?} and {:?}", a, b)),
            })?,
            Instruction::Gt => self.binary_op(|a, b| match (&a, &b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Bool(a > b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Bool(a > b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Bool((*a as f64) > *b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Bool(*a > (*b as f64))),
                _ => Err(format!("Cannot compare {:?} and {:?}", a, b)),
            })?,
            Instruction::GtEq => self.binary_op(|a, b| match (&a, &b) {
                (Value::Int(a), Value::Int(b)) => Ok(Value::Bool(a >= b)),
                (Value::Float(a), Value::Float(b)) => Ok(Value::Bool(a >= b)),
                (Value::Int(a), Value::Float(b)) => Ok(Value::Bool((*a as f64) >= *b)),
                (Value::Float(a), Value::Int(b)) => Ok(Value::Bool(*a >= (*b as f64))),
                _ => Err(format!("Cannot compare {:?} and {:?}", a, b)),
            })?,

            // Logical
            Instruction::And => self.binary_op(|a, b| match (a, b) {
                (Value::Bool(a), Value::Bool(b)) => Ok(Value::Bool(a && b)),
                (a, b) => Err(format!("Cannot AND {:?} and {:?}", a, b)),
            })?,
            Instruction::Or => self.binary_op(|a, b| match (a, b) {
                (Value::Bool(a), Value::Bool(b)) => Ok(Value::Bool(a || b)),
                (a, b) => Err(format!("Cannot OR {:?} and {:?}", a, b)),
            })?,
            Instruction::Not => {
                let val = self.stack.pop().ok_or("Stack underflow on Not")?;
                match val {
                    Value::Bool(b) => self.stack.push(Value::Bool(!b)),
                    _ => return Err(format!("Cannot NOT {:?}", val)),
                }
            }

            // Control flow
            Instruction::Jump(addr) => {
                self.pc = addr;
            }
            Instruction::JumpIfFalse(addr) => {
                let val = self.stack.pop().ok_or("Stack underflow on JumpIfFalse")?;
                match val {
                    Value::Bool(false) => {
                        self.pc = addr;
                    }
                    Value::Bool(true) => {
                        // Don't jump, continue (condition already popped)
                    }
                    _ => return Err("JumpIfFalse requires a boolean value".to_string()),
                }
            }
            Instruction::JumpIfTrue(addr) => {
                let val = self.stack.pop().ok_or("Stack underflow on JumpIfTrue")?;
                match val {
                    Value::Bool(true) => {
                        self.pc = addr;
                    }
                    Value::Bool(false) => {
                        // Don't jump, continue (condition already popped)
                    }
                    _ => return Err("JumpIfTrue requires a boolean value".to_string()),
                }
            }

            // Functions
            Instruction::Call(name, arg_count) => {
                self.call_function(&name, arg_count)?;
            }
            Instruction::Return => {
                if let Some(frame) = self.call_stack.pop() {
                    self.pc = frame.return_addr;
                }
            }

            // I/O
            Instruction::Print(count) => {
                let mut values = Vec::new();
                for _ in 0..count {
                    let val = self.stack.pop().ok_or("Stack underflow on Print")?;
                    values.push(val);
                }
                values.reverse();
                let output: Vec<String> = values.iter().map(|v| v.to_string()).collect();
                self.output.push(output.join(" "));
            }

            // Labels are no-ops (used only during code generation)
            Instruction::Label(_) => {}
        }

        Ok(())
    }

    fn binary_op<F>(&mut self, op: F) -> Result<(), String>
    where
        F: Fn(Value, Value) -> Result<Value, String>,
    {
        let b = self.stack.pop().ok_or("Stack underflow")?;
        let a = self.stack.pop().ok_or("Stack underflow")?;
        let result = op(a, b)?;
        self.stack.push(result);
        Ok(())
    }

    fn resolve_variable(&self, name: &str) -> Result<Value, String> {
        // Check current frame locals first
        if let Some(frame) = self.call_stack.last() {
            // Check if it's a parameter
            if let Some(_pos) = frame.param_names.iter().position(|p| p == name) {
                // Parameters are stored as locals with the same name
                if let Some(val) = frame.locals.get(name) {
                    return Ok(val.clone());
                }
            }
            if let Some(val) = frame.locals.get(name) {
                return Ok(val.clone());
            }
        }
        // Check globals
        if let Some(val) = self.globals.get(name) {
            return Ok(val.clone());
        }
        Err(format!("Undefined variable '{}'", name))
    }

    fn set_variable(&mut self, name: String, value: Value) {
        if let Some(frame) = self.call_stack.last_mut() {
            if let std::collections::hash_map::Entry::Occupied(mut e) = frame.locals.entry(name.clone()) {
                e.insert(value);
                return;
            }
        }
        self.globals.insert(name, value);
    }

    fn call_function(&mut self, name: &str, arg_count: usize) -> Result<(), String> {
        let func = self
            .functions
            .get(name)
            .ok_or(format!("Undefined function '{}'", name))?
            .clone();

        if func.params.len() != arg_count {
            return Err(format!(
                "Function '{}' expects {} arguments, got {}",
                name,
                func.params.len(),
                arg_count
            ));
        }

        // Pop arguments
        let mut args = Vec::new();
        for _ in 0..arg_count {
            args.push(self.stack.pop().ok_or("Stack underflow on Call")?);
        }
        args.reverse();

        // Create new frame
        let mut locals = HashMap::new();
        for (param_name, arg_value) in func.params.iter().zip(args) {
            locals.insert(param_name.clone(), arg_value);
        }

        self.call_stack.push(Frame {
            locals,
            return_addr: self.pc,
            param_names: func.params.clone(),
        });

        // Jump to function
        self.pc = func.start_addr;

        Ok(())
    }
}

/// Convenience function: compile and run a program
pub fn compile_and_run(source: &str) -> Result<Vec<String>, String> {
    use crate::codegen::CodeGenerator;
    use crate::lexer::Lexer;
    use crate::parser::Parser;

    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize()?;
    let mut parser = Parser::new(tokens);
    let program = parser.parse()?;

    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program)?;
    let functions = codegen.get_functions().to_vec();

    let mut vm = VM::new(instructions, functions);
    vm.run()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::codegen::CodeGenerator;
    use crate::lexer::Lexer;
    use crate::parser::Parser;

    fn run_program(source: &str) -> Vec<String> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let program = parser.parse().unwrap();
        let mut codegen = CodeGenerator::new();
        let instructions = codegen.generate(&program).unwrap();
        let functions = codegen.get_functions().to_vec();
        let mut vm = VM::new(instructions, functions);
        vm.run().unwrap()
    }

    #[test]
    fn test_simple_print() {
        let output = run_program("print(42);");
        assert_eq!(output, vec!["42"]);
    }

    #[test]
    fn test_arithmetic() {
        let output = run_program("print(1 + 2 * 3);");
        assert_eq!(output, vec!["7"]);
    }

    #[test]
    fn test_variables() {
        let output = run_program("let x = 10; let y = 20; print(x + y);");
        assert_eq!(output, vec!["30"]);
    }

    #[test]
    fn test_if_true() {
        let output = run_program("if true { print(1); }");
        assert_eq!(output, vec!["1"]);
    }

    #[test]
    fn test_if_false() {
        let output = run_program("if false { print(1); }");
        assert_eq!(output, Vec::<String>::new());
    }

    #[test]
    fn test_if_else() {
        let output = run_program("if false { print(1); } else { print(2); }");
        assert_eq!(output, vec!["2"]);
    }

    #[test]
    fn test_while_loop() {
        let output = run_program(
            "let x = 0; while x < 5 { print(x); x = x + 1; }",
        );
        assert_eq!(output, vec!["0", "1", "2", "3", "4"]);
    }

    #[test]
    fn test_function() {
        let output = run_program(
            "fn add(x, y) { return x + y; } print(add(3, 4));",
        );
        assert_eq!(output, vec!["7"]);
    }

    #[test]
    fn test_function_recursive() {
        let output = run_program(
            r#"
            fn factorial(n) {
                if n <= 1 {
                    return 1;
                }
                return n * factorial(n - 1);
            }
            print(factorial(5));
            "#,
        );
        assert_eq!(output, vec!["120"]);
    }

    #[test]
    fn test_string_print() {
        let output = run_program(r#"print("hello world");"#);
        assert_eq!(output, vec!["hello world"]);
    }

    #[test]
    fn test_multiple_prints() {
        let output = run_program("print(1, 2, 3);");
        assert_eq!(output, vec!["1 2 3"]);
    }

    #[test]
    fn test_comparison() {
        let output = run_program("print(1 < 2);");
        assert_eq!(output, vec!["true"]);
    }

    #[test]
    fn test_logical_operators() {
        let output = run_program("print(true && false);");
        assert_eq!(output, vec!["false"]);
    }

    #[test]
    fn test_fibonacci() {
        let output = run_program(
            r#"
            fn fib(n) {
                if n <= 1 {
                    return n;
                }
                return fib(n - 1) + fib(n - 2);
            }
            print(fib(10));
            "#,
        );
        assert_eq!(output, vec!["55"]);
    }

    #[test]
    fn test_nested_blocks() {
        let output = run_program(
            r#"
            let x = 10;
            if x > 5 {
                if x > 8 {
                    print("big");
                }
            }
            "#,
        );
        assert_eq!(output, vec!["big"]);
    }

    #[test]
    fn test_assignment() {
        let output = run_program(
            "let x = 1; x = 2; print(x);",
        );
        assert_eq!(output, vec!["2"]);
    }

    #[test]
    fn test_compile_and_run() {
        let output = compile_and_run("print(42);").unwrap();
        assert_eq!(output, vec!["42"]);
    }

    #[test]
    fn test_division_by_zero() {
        let result = run_program_safe("print(1 / 0);");
        assert!(result.is_err());
    }

    fn run_program_safe(source: &str) -> Result<Vec<String>, String> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize()?;
        let mut parser = Parser::new(tokens);
        let program = parser.parse()?;
        let mut codegen = CodeGenerator::new();
        let instructions = codegen.generate(&program)?;
        let functions = codegen.get_functions().to_vec();
        let mut vm = VM::new(instructions, functions);
        vm.run()
    }

    #[test]
    fn test_string_concatenation() {
        let output = run_program(r#"print("hello" + " " + "world");"#);
        assert_eq!(output, vec!["hello world"]);
    }

    #[test]
    fn test_nested_function_calls() {
        let output = run_program(
            r#"
            fn double(x) { return x * 2; }
            fn triple(x) { return x * 3; }
            print(double(triple(5)));
            "#,
        );
        assert_eq!(output, vec!["30"]);
    }

    #[test]
    fn test_modulo() {
        let output = run_program("print(10 % 3);");
        assert_eq!(output, vec!["1"]);
    }
}
