use std::env;
use std::fs;
use std::io::{self, Write};
use std::process;

use simple_compiler::codegen::{CodeGenerator, disassemble};
use simple_compiler::lexer::Lexer;
use simple_compiler::parser::Parser;
use simple_compiler::vm::VM;

fn main() {
    let args: Vec<String> = env::args().collect();

    match args.get(1).map(|s| s.as_str()) {
        Some("run") => {
            if let Some(path) = args.get(2) {
                run_file(path);
            } else {
                eprintln!("Usage: sc run <file>");
                process::exit(1);
            }
        }
        Some("compile") => {
            if let Some(path) = args.get(2) {
                compile_file(path);
            } else {
                eprintln!("Usage: sc compile <file>");
                process::exit(1);
            }
        }
        Some("repl") | None => {
            run_repl();
        }
        Some("help") | Some("--help") | Some("-h") => {
            print_help();
        }
        Some(cmd) => {
            eprintln!("Unknown command: {}", cmd);
            print_help();
            process::exit(1);
        }
    }
}

fn print_help() {
    println!("Simple Compiler - A learning compiler project");
    println!();
    println!("USAGE:");
    println!("  sc                 Start the REPL (interactive mode)");
    println!("  sc repl            Start the REPL");
    println!("  sc run <file>      Compile and run a file");
    println!("  sc compile <file>  Compile a file and show bytecode");
    println!("  sc help            Show this help message");
    println!();
    println!("LANGUAGE SYNTAX:");
    println!("  let x = 42;              Variable declaration");
    println!("  x = x + 1;               Assignment");
    println!("  print(x, y);             Print values");
    println!("  if x > 0 {{ ... }}       Conditional");
    println!("  while x > 0 {{ ... }}    Loop");
    println!("  fn add(x, y) {{ ... }}   Function definition");
    println!("  return x + y;            Return from function");
}

fn run_file(path: &str) {
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Error reading file '{}': {}", path, e);
            process::exit(1);
        }
    };

    match compile_and_run(&source) {
        Ok(_) => {}
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}

fn compile_file(path: &str) {
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Error reading file '{}': {}", path, e);
            process::exit(1);
        }
    };

    match compile_and_show(&source) {
        Ok(_) => {}
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}

fn compile_and_run(source: &str) -> Result<(), String> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize()?;
    let mut parser = Parser::new(tokens);
    let program = parser.parse()?;

    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program)?;
    let functions = codegen.get_functions().to_vec();

    let mut vm = VM::new(instructions, functions);
    let output = vm.run()?;

    for line in output {
        println!("{}", line);
    }

    Ok(())
}

fn compile_and_show(source: &str) -> Result<(), String> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize()?;

    println!("=== Tokens ===");
    for token in &tokens {
        println!("  {:?}", token);
    }
    println!();

    let mut parser = Parser::new(tokens);
    let program = parser.parse()?;

    println!("=== AST ===");
    println!("  {:#?}", program);
    println!();

    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program)?;

    println!("=== Bytecode ===");
    print!("{}", disassemble(&instructions));

    if !codegen.get_functions().is_empty() {
        println!("=== Functions ===");
        for func in codegen.get_functions() {
            println!("  {} (params: {:?}, addr: {})", func.name, func.params, func.start_addr);
        }
    }

    Ok(())
}

fn run_repl() {
    println!("Simple Compiler REPL");
    println!("Type 'exit' or 'quit' to exit, 'help' for help");
    println!();

    let mut buffer = String::new();

    loop {
        print!("> ");
        io::stdout().flush().unwrap();

        let mut line = String::new();
        match io::stdin().read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => {}
            Err(e) => {
                eprintln!("Error reading input: {}", e);
                continue;
            }
        }

        let line = line.trim();

        if line == "exit" || line == "quit" {
            println!("Goodbye!");
            break;
        }

        if line == "help" {
            println!("Commands:");
            println!("  exit/quit  - Exit the REPL");
            println!("  help       - Show this help");
            println!("  tokens <expr> - Show tokens");
            println!("  ast <expr>    - Show AST");
            println!("  <code>        - Execute code");
            continue;
        }

        if let Some(expr) = line.strip_prefix("tokens ") {
            match Lexer::new(expr).tokenize() {
                Ok(tokens) => {
                    for token in &tokens {
                        println!("  {:?}", token);
                    }
                }
                Err(e) => eprintln!("Lexer error: {}", e),
            }
            continue;
        }

        if let Some(expr) = line.strip_prefix("ast ") {
            match compile_to_ast(expr) {
                Ok(ast) => println!("  {:#?}", ast),
                Err(e) => eprintln!("Error: {}", e),
            }
            continue;
        }

        buffer.push_str(line);
        buffer.push('\n');

        // Try to compile and run what we have so far
        match compile_and_run(&buffer) {
            Ok(_) => {}
            Err(e) => {
                // Don't clear buffer on error - user might be in the middle of typing
                if !buffer.trim().is_empty() {
                    // Only show error if we have a complete statement (ends with ; or })
                    if line.ends_with(';') || line.ends_with('}') {
                        eprintln!("Error: {}", e);
                        buffer.clear();
                    }
                    // Otherwise keep accumulating
                }
            }
        }

        // Clear buffer after successful execution
        if line.ends_with(';') || line.ends_with('}') {
            buffer.clear();
        }
    }
}

fn compile_to_ast(source: &str) -> Result<simple_compiler::ast::Program, String> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize()?;
    let mut parser = Parser::new(tokens);
    parser.parse()
}
