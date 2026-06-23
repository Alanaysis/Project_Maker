use crate::ast::*;

/// Bytecode instructions for a simple stack-based virtual machine
///
/// The code generator translates the AST into a linear sequence of
/// bytecode instructions. This is an intermediate representation
/// that can be efficiently executed by a virtual machine.
#[derive(Debug, Clone, PartialEq)]
pub enum Instruction {
    // Stack operations
    PushInt(i64),
    PushFloat(f64),
    PushBool(bool),
    PushStr(String),
    Pop,
    Dup,

    // Local variables
    LoadLocal(String),
    StoreLocal(String),

    // Arithmetic
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Neg,

    // Comparison
    Eq,
    NotEq,
    Lt,
    LtEq,
    Gt,
    GtEq,

    // Logical
    And,
    Or,
    Not,

    // Control flow
    Jump(usize),         // unconditional jump
    JumpIfFalse(usize),  // jump if top of stack is false
    JumpIfTrue(usize),   // jump if top of stack is true

    // Functions
    Call(String, usize), // call function with N arguments
    Return,

    // I/O
    Print(usize),        // print N values

    // Labels (for backpatching, removed in final output)
    Label(String),
}

/// Function metadata
#[derive(Debug, Clone)]
pub struct FunctionInfo {
    pub name: String,
    pub params: Vec<String>,
    pub start_addr: usize,
}

/// Code generator - translates AST to bytecode
///
/// Walks the AST and emits bytecode instructions. Uses a stack-based
/// approach where expressions push values onto a stack and operators
/// pop their operands and push results.
pub struct CodeGenerator {
    instructions: Vec<Instruction>,
    functions: Vec<FunctionInfo>,
}

impl CodeGenerator {
    pub fn new() -> Self {
        Self {
            instructions: Vec::new(),
            functions: Vec::new(),
        }
    }

    /// Generate bytecode from a program
    pub fn generate(&mut self, program: &Program) -> Result<Vec<Instruction>, String> {
        for stmt in &program.statements {
            self.gen_statement(stmt)?;
        }
        Ok(self.instructions.clone())
    }

    /// Get function metadata collected during code generation
    pub fn get_functions(&self) -> &[FunctionInfo] {
        &self.functions
    }

    fn emit(&mut self, instruction: Instruction) {
        self.instructions.push(instruction);
    }

    fn current_addr(&self) -> usize {
        self.instructions.len()
    }

    fn gen_statement(&mut self, stmt: &Statement) -> Result<(), String> {
        match stmt {
            Statement::Let { name, value, .. } => {
                self.gen_expression(value)?;
                self.emit(Instruction::StoreLocal(name.clone()));
            }
            Statement::Assign { name, value } => {
                self.gen_expression(value)?;
                self.emit(Instruction::StoreLocal(name.clone()));
            }
            Statement::Print { args } => {
                let count = args.len();
                for arg in args {
                    self.gen_expression(arg)?;
                }
                self.emit(Instruction::Print(count));
            }
            Statement::If {
                condition,
                then_block,
                else_block,
            } => {
                self.gen_expression(condition)?;

                let jump_to_else = self.current_addr();
                self.emit(Instruction::JumpIfFalse(0)); // placeholder

                // Then block
                for stmt in then_block {
                    self.gen_statement(stmt)?;
                }

                if let Some(else_block) = else_block {
                    let jump_to_end = self.current_addr();
                    self.emit(Instruction::Jump(0)); // placeholder

                    // Patch the jump-to-else
                    let else_addr = self.current_addr();
                    self.instructions[jump_to_else] = Instruction::JumpIfFalse(else_addr);

                    // Else block
                    for stmt in else_block {
                        self.gen_statement(stmt)?;
                    }

                    // Patch the jump-to-end
                    let end_addr = self.current_addr();
                    self.instructions[jump_to_end] = Instruction::Jump(end_addr);
                } else {
                    // No else: patch jump-to-end
                    let end_addr = self.current_addr();
                    self.instructions[jump_to_else] = Instruction::JumpIfFalse(end_addr);
                }
            }
            Statement::While { condition, body } => {
                let loop_start = self.current_addr();

                self.gen_expression(condition)?;

                let jump_to_end = self.current_addr();
                self.emit(Instruction::JumpIfFalse(0)); // placeholder

                for stmt in body {
                    self.gen_statement(stmt)?;
                }

                self.emit(Instruction::Jump(loop_start));

                let loop_end = self.current_addr();
                self.instructions[jump_to_end] = Instruction::JumpIfFalse(loop_end);
            }
            Statement::FunctionDef {
                name,
                params,
                body,
                ..
            } => {
                // Jump over function body
                let jump_over = self.current_addr();
                self.emit(Instruction::Jump(0)); // placeholder

                let func_start = self.current_addr();

                let param_names: Vec<String> = params.iter().map(|p| p.name.clone()).collect();

                // Store function info
                self.functions.push(FunctionInfo {
                    name: name.clone(),
                    params: param_names.clone(),
                    start_addr: func_start,
                });

                // Generate function body
                for stmt in body {
                    self.gen_statement(stmt)?;
                }

                // Implicit return if not already returned
                let needs_implicit_return = !matches!(body.last(), Some(Statement::Return { .. }));
                if needs_implicit_return {
                    self.emit(Instruction::PushInt(0)); // default return value for void functions
                    self.emit(Instruction::Return);
                }

                let func_end = self.current_addr();
                self.instructions[jump_over] = Instruction::Jump(func_end);
            }
            Statement::Return { value } => {
                if let Some(expr) = value {
                    self.gen_expression(expr)?;
                }
                self.emit(Instruction::Return);
            }
            Statement::Expression { expr } => {
                self.gen_expression(expr)?;
                self.emit(Instruction::Pop); // discard result
            }
        }

        Ok(())
    }

    fn gen_expression(&mut self, expr: &Expression) -> Result<(), String> {
        match expr {
            Expression::IntegerLiteral(n) => {
                self.emit(Instruction::PushInt(*n));
            }
            Expression::FloatLiteral(f) => {
                self.emit(Instruction::PushFloat(*f));
            }
            Expression::BoolLiteral(b) => {
                self.emit(Instruction::PushBool(*b));
            }
            Expression::StringLiteral(s) => {
                self.emit(Instruction::PushStr(s.clone()));
            }
            Expression::Identifier(name) => {
                self.emit(Instruction::LoadLocal(name.clone()));
            }
            Expression::BinaryOp { op, left, right } => {
                // Short-circuit for logical operators
                match op {
                    BinaryOp::And => {
                        // a && b:
                        // If a is false, result is a (false)
                        // If a is true, result is b
                        self.gen_expression(left)?;
                        self.emit(Instruction::Dup); // duplicate for potential result
                        let jump_addr = self.current_addr();
                        self.emit(Instruction::JumpIfFalse(0)); // pops dup, jumps if false
                        self.emit(Instruction::Pop); // pop original left (true case)
                        self.gen_expression(right)?;
                        let end_addr = self.current_addr();
                        self.instructions[jump_addr] = Instruction::JumpIfFalse(end_addr);
                        return Ok(());
                    }
                    BinaryOp::Or => {
                        // a || b:
                        // If a is true, result is a (true)
                        // If a is false, result is b
                        self.gen_expression(left)?;
                        self.emit(Instruction::Dup); // duplicate for potential result
                        let jump_addr = self.current_addr();
                        self.emit(Instruction::JumpIfTrue(0)); // pops dup, jumps if true
                        self.emit(Instruction::Pop); // pop original left (false case)
                        self.gen_expression(right)?;
                        let end_addr = self.current_addr();
                        self.instructions[jump_addr] = Instruction::JumpIfTrue(end_addr);
                        return Ok(());
                    }
                    _ => {}
                }

                self.gen_expression(left)?;
                self.gen_expression(right)?;

                match op {
                    BinaryOp::Add => self.emit(Instruction::Add),
                    BinaryOp::Sub => self.emit(Instruction::Sub),
                    BinaryOp::Mul => self.emit(Instruction::Mul),
                    BinaryOp::Div => self.emit(Instruction::Div),
                    BinaryOp::Mod => self.emit(Instruction::Mod),
                    BinaryOp::Eq => self.emit(Instruction::Eq),
                    BinaryOp::NotEq => self.emit(Instruction::NotEq),
                    BinaryOp::Lt => self.emit(Instruction::Lt),
                    BinaryOp::LtEq => self.emit(Instruction::LtEq),
                    BinaryOp::Gt => self.emit(Instruction::Gt),
                    BinaryOp::GtEq => self.emit(Instruction::GtEq),
                    BinaryOp::And | BinaryOp::Or => unreachable!(),
                };
            }
            Expression::UnaryOp { op, operand } => {
                self.gen_expression(operand)?;
                match op {
                    UnaryOp::Neg => self.emit(Instruction::Neg),
                    UnaryOp::Not => self.emit(Instruction::Not),
                };
            }
            Expression::Call { name, args } => {
                let arg_count = args.len();
                for arg in args {
                    self.gen_expression(arg)?;
                }
                self.emit(Instruction::Call(name.clone(), arg_count));
            }
        }

        Ok(())
    }
}

impl Default for CodeGenerator {
    fn default() -> Self {
        Self::new()
    }
}

/// Pretty-print bytecode instructions
pub fn disassemble(instructions: &[Instruction]) -> String {
    let mut output = String::new();
    for (i, inst) in instructions.iter().enumerate() {
        output.push_str(&format!("{:04}  {:?}\n", i, inst));
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;
    use crate::parser::Parser;

    fn compile(source: &str) -> Vec<Instruction> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let program = parser.parse().unwrap();
        let mut codegen = CodeGenerator::new();
        codegen.generate(&program).unwrap()
    }

    #[test]
    fn test_simple_assignment() {
        let instructions = compile("let x = 42;");
        assert_eq!(instructions[0], Instruction::PushInt(42));
        assert_eq!(instructions[1], Instruction::StoreLocal("x".to_string()));
    }

    #[test]
    fn test_arithmetic() {
        let instructions = compile("let x = 1 + 2;");
        assert_eq!(instructions[0], Instruction::PushInt(1));
        assert_eq!(instructions[1], Instruction::PushInt(2));
        assert_eq!(instructions[2], Instruction::Add);
        assert_eq!(instructions[3], Instruction::StoreLocal("x".to_string()));
    }

    #[test]
    fn test_operator_precedence() {
        let instructions = compile("let x = 1 + 2 * 3;");
        // Should be: 1 2 3 * +
        assert_eq!(instructions[0], Instruction::PushInt(1));
        assert_eq!(instructions[1], Instruction::PushInt(2));
        assert_eq!(instructions[2], Instruction::PushInt(3));
        assert_eq!(instructions[3], Instruction::Mul);
        assert_eq!(instructions[4], Instruction::Add);
    }

    #[test]
    fn test_print() {
        let instructions = compile("print(42);");
        assert_eq!(instructions[0], Instruction::PushInt(42));
        assert_eq!(instructions[1], Instruction::Print(1));
    }

    #[test]
    fn test_if_else() {
        let instructions = compile("if true { print(1); } else { print(2); }");
        // 0: PushBool(true)
        // 1: JumpIfFalse(5)  -- jump to else (pops condition)
        // 2: PushInt(1)
        // 3: Print(1)
        // 4: Jump(7)          -- skip else
        // 5: PushInt(2)
        // 6: Print(1)
        assert_eq!(instructions[0], Instruction::PushBool(true));
        assert_eq!(instructions[1], Instruction::JumpIfFalse(5));
        assert_eq!(instructions[2], Instruction::PushInt(1));
        assert_eq!(instructions[3], Instruction::Print(1));
        assert_eq!(instructions[4], Instruction::Jump(7));
        assert_eq!(instructions[5], Instruction::PushInt(2));
        assert_eq!(instructions[6], Instruction::Print(1));
    }

    #[test]
    fn test_while_loop() {
        let instructions = compile("while true { print(1); }");
        // 0: PushBool(true)
        // 1: JumpIfFalse(5)  -- exit loop (pops condition)
        // 2: PushInt(1)
        // 3: Print(1)
        // 4: Jump(0)
        assert_eq!(instructions[0], Instruction::PushBool(true));
        assert_eq!(instructions[1], Instruction::JumpIfFalse(5));
        assert_eq!(instructions[2], Instruction::PushInt(1));
        assert_eq!(instructions[3], Instruction::Print(1));
        assert_eq!(instructions[4], Instruction::Jump(0));
    }

    #[test]
    fn test_function_def() {
        let instructions = compile("fn add(x, y) { return x + y; }");
        // Jump(5), LoadLocal(x), LoadLocal(y), Add, Return
        assert_eq!(instructions[0], Instruction::Jump(5));
        assert_eq!(instructions[1], Instruction::LoadLocal("x".to_string()));
        assert_eq!(instructions[2], Instruction::LoadLocal("y".to_string()));
        assert_eq!(instructions[3], Instruction::Add);
        assert_eq!(instructions[4], Instruction::Return);
    }

    #[test]
    fn test_function_call() {
        let instructions = compile("print(add(1, 2));");
        assert_eq!(instructions[0], Instruction::PushInt(1));
        assert_eq!(instructions[1], Instruction::PushInt(2));
        assert_eq!(instructions[2], Instruction::Call("add".to_string(), 2));
        assert_eq!(instructions[3], Instruction::Print(1));
    }

    #[test]
    fn test_comparison() {
        let instructions = compile("let x = 1 < 2;");
        assert_eq!(instructions[0], Instruction::PushInt(1));
        assert_eq!(instructions[1], Instruction::PushInt(2));
        assert_eq!(instructions[2], Instruction::Lt);
    }

    #[test]
    fn test_unary_negation() {
        let instructions = compile("let x = -42;");
        assert_eq!(instructions[0], Instruction::PushInt(42));
        assert_eq!(instructions[1], Instruction::Neg);
    }

    #[test]
    fn test_unary_not() {
        let instructions = compile("let x = !true;");
        assert_eq!(instructions[0], Instruction::PushBool(true));
        assert_eq!(instructions[1], Instruction::Not);
    }

    #[test]
    fn test_disassemble() {
        let instructions = compile("let x = 42;");
        let output = disassemble(&instructions);
        assert!(output.contains("0000"));
        assert!(output.contains("PushInt(42)"));
        assert!(output.contains("StoreLocal"));
    }

    #[test]
    fn test_logical_and_short_circuit() {
        let instructions = compile("let x = true && false;");
        // Should use Dup + JumpIfFalse for short-circuit
        assert!(instructions.iter().any(|i| matches!(i, Instruction::JumpIfFalse(_))));
        assert!(instructions.contains(&Instruction::Dup));
    }

    #[test]
    fn test_logical_or_short_circuit() {
        let instructions = compile("let x = false || true;");
        // Should use Dup + JumpIfTrue for short-circuit
        assert!(instructions.iter().any(|i| matches!(i, Instruction::JumpIfTrue(_))));
        assert!(instructions.contains(&Instruction::Dup));
    }
}
