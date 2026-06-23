use simple_compiler::codegen::CodeGenerator;
use simple_compiler::lexer::Lexer;
use simple_compiler::parser::Parser;
use simple_compiler::vm::VM;

/// Helper: compile and run source code, return output lines
fn run(source: &str) -> Vec<String> {
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

// ==================== Basic Output ====================

#[test]
fn test_hello_world() {
    let output = run(r#"print("Hello, World!");"#);
    assert_eq!(output, vec!["Hello, World!"]);
}

#[test]
fn test_multiple_prints() {
    let output = run("print(1); print(2); print(3);");
    assert_eq!(output, vec!["1", "2", "3"]);
}

#[test]
fn test_print_expressions() {
    let output = run("print(1 + 2);");
    assert_eq!(output, vec!["3"]);
}

// ==================== Variables ====================

#[test]
fn test_variable_declaration() {
    let output = run("let x = 42; print(x);");
    assert_eq!(output, vec!["42"]);
}

#[test]
fn test_variable_reassignment() {
    let output = run("let x = 1; x = 2; print(x);");
    assert_eq!(output, vec!["2"]);
}

#[test]
fn test_multiple_variables() {
    let output = run("let a = 10; let b = 20; print(a + b);");
    assert_eq!(output, vec!["30"]);
}

// ==================== Arithmetic ====================

#[test]
fn test_addition() {
    let output = run("print(1 + 2);");
    assert_eq!(output, vec!["3"]);
}

#[test]
fn test_subtraction() {
    let output = run("print(5 - 3);");
    assert_eq!(output, vec!["2"]);
}

#[test]
fn test_multiplication() {
    let output = run("print(3 * 4);");
    assert_eq!(output, vec!["12"]);
}

#[test]
fn test_division() {
    let output = run("print(10 / 2);");
    assert_eq!(output, vec!["5"]);
}

#[test]
fn test_modulo() {
    let output = run("print(10 % 3);");
    assert_eq!(output, vec!["1"]);
}

#[test]
fn test_operator_precedence() {
    let output = run("print(2 + 3 * 4);");
    assert_eq!(output, vec!["14"]);
}

#[test]
fn test_parenthesized_expression() {
    let output = run("print((2 + 3) * 4);");
    assert_eq!(output, vec!["20"]);
}

#[test]
fn test_unary_negation() {
    let output = run("let x = 5; print(-x);");
    assert_eq!(output, vec!["-5"]);
}

#[test]
fn test_complex_arithmetic() {
    let output = run("print((10 + 2) * (5 - 3) / 4);");
    assert_eq!(output, vec!["6"]);
}

// ==================== Comparison ====================

#[test]
fn test_equal() {
    let output = run("print(1 == 1);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_not_equal() {
    let output = run("print(1 != 2);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_less_than() {
    let output = run("print(1 < 2);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_greater_than() {
    let output = run("print(3 > 2);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_less_equal() {
    let output = run("print(2 <= 2);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_greater_equal() {
    let output = run("print(3 >= 2);");
    assert_eq!(output, vec!["true"]);
}

// ==================== Logical Operators ====================

#[test]
fn test_logical_and() {
    let output = run("print(true && true);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_logical_or() {
    let output = run("print(false || true);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_logical_not() {
    let output = run("print(!false);");
    assert_eq!(output, vec!["true"]);
}

#[test]
fn test_short_circuit_and() {
    // If first operand is false, second should not be evaluated
    let output = run("print(false && (1 / 0 == 0));");
    assert_eq!(output, vec!["false"]);
}

#[test]
fn test_short_circuit_or() {
    // If first operand is true, second should not be evaluated
    let output = run("print(true || (1 / 0 == 0));");
    assert_eq!(output, vec!["true"]);
}

// ==================== Control Flow ====================

#[test]
fn test_if_true() {
    let output = run("if true { print(1); }");
    assert_eq!(output, vec!["1"]);
}

#[test]
fn test_if_false() {
    let output = run("if false { print(1); }");
    assert_eq!(output, Vec::<String>::new());
}

#[test]
fn test_if_else() {
    let output = run("if false { print(1); } else { print(2); }");
    assert_eq!(output, vec!["2"]);
}

#[test]
fn test_if_elif_else() {
    let output = run(
        r#"
        let x = 2;
        if x == 1 {
            print("one");
        } else if x == 2 {
            print("two");
        } else {
            print("other");
        }
        "#,
    );
    assert_eq!(output, vec!["two"]);
}

#[test]
fn test_nested_if() {
    let output = run(
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
fn test_while_loop() {
    let output = run(
        r#"
        let i = 0;
        while i < 5 {
            print(i);
            i = i + 1;
        }
        "#,
    );
    assert_eq!(output, vec!["0", "1", "2", "3", "4"]);
}

#[test]
fn test_while_not_executed() {
    let output = run("while false { print(1); }");
    assert_eq!(output, Vec::<String>::new());
}

#[test]
fn test_nested_while() {
    let output = run(
        r#"
        let i = 0;
        while i < 3 {
            let j = 0;
            while j < 2 {
                print(i * 10 + j);
                j = j + 1;
            }
            i = i + 1;
        }
        "#,
    );
    assert_eq!(output, vec!["0", "1", "10", "11", "20", "21"]);
}

// ==================== Functions ====================

#[test]
fn test_simple_function() {
    let output = run(
        r#"
        fn add(x, y) {
            return x + y;
        }
        print(add(3, 4));
        "#,
    );
    assert_eq!(output, vec!["7"]);
}

#[test]
fn test_function_no_args() {
    let output = run(
        r#"
        fn get_value() {
            return 42;
        }
        print(get_value());
        "#,
    );
    assert_eq!(output, vec!["42"]);
}

#[test]
fn test_function_no_return() {
    let output = run(
        r#"
        fn greet(name) {
            print("Hello, " + name);
        }
        greet("World");
        "#,
    );
    assert_eq!(output, vec!["Hello, World"]);
}

#[test]
fn test_recursive_factorial() {
    let output = run(
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
fn test_recursive_fibonacci() {
    let output = run(
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
fn test_nested_function_calls() {
    let output = run(
        r#"
        fn double(x) { return x * 2; }
        fn triple(x) { return x * 3; }
        print(double(triple(5)));
        "#,
    );
    assert_eq!(output, vec!["30"]);
}

// ==================== Strings ====================

#[test]
fn test_string_literal() {
    let output = run(r#"print("hello");"#);
    assert_eq!(output, vec!["hello"]);
}

#[test]
fn test_string_concatenation() {
    let output = run(r#"print("hello" + " " + "world");"#);
    assert_eq!(output, vec!["hello world"]);
}

#[test]
fn test_string_escape_sequences() {
    let output = run(r#"print("line1\nline2");"#);
    assert_eq!(output, vec!["line1\nline2"]);
}

// ==================== Complex Programs ====================

#[test]
fn test_fizzbuzz() {
    let output = run(
        r#"
        let i = 1;
        while i <= 15 {
            if i % 15 == 0 {
                print("FizzBuzz");
            } else if i % 3 == 0 {
                print("Fizz");
            } else if i % 5 == 0 {
                print("Buzz");
            } else {
                print(i);
            }
            i = i + 1;
        }
        "#,
    );
    assert_eq!(
        output,
        vec![
            "1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13",
            "14", "FizzBuzz"
        ]
    );
}

#[test]
fn test_sum_of_numbers() {
    let output = run(
        r#"
        let sum = 0;
        let i = 1;
        while i <= 100 {
            sum = sum + i;
            i = i + 1;
        }
        print(sum);
        "#,
    );
    assert_eq!(output, vec!["5050"]);
}

#[test]
fn test_is_prime() {
    let output = run(
        r#"
        fn is_prime(n) {
            if n <= 1 { return false; }
            if n <= 3 { return true; }
            if n % 2 == 0 { return false; }
            let i = 3;
            while i * i <= n {
                if n % i == 0 { return false; }
                i = i + 2;
            }
            return true;
        }

        let n = 2;
        while n <= 20 {
            if is_prime(n) {
                print(n);
            }
            n = n + 1;
        }
        "#,
    );
    assert_eq!(output, vec!["2", "3", "5", "7", "11", "13", "17", "19"]);
}

#[test]
fn test_gcd() {
    let output = run(
        r#"
        fn gcd(a, b) {
            while b != 0 {
                let temp = b;
                b = a % b;
                a = temp;
            }
            return a;
        }
        print(gcd(48, 18));
        "#,
    );
    assert_eq!(output, vec!["6"]);
}

#[test]
fn test_power_function() {
    let output = run(
        r#"
        fn power(base, exp) {
            if exp == 0 { return 1; }
            return base * power(base, exp - 1);
        }
        print(power(2, 10));
        "#,
    );
    assert_eq!(output, vec!["1024"]);
}

// ==================== Error Cases ====================

#[test]
fn test_error_undefined_variable() {
    let mut lexer = Lexer::new("print(x);");
    let tokens = lexer.tokenize().unwrap();
    let mut parser = Parser::new(tokens);
    let program = parser.parse().unwrap();
    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program).unwrap();
    let functions = codegen.get_functions().to_vec();
    let mut vm = VM::new(instructions, functions);
    assert!(vm.run().is_err());
}

#[test]
fn test_error_division_by_zero() {
    let mut lexer = Lexer::new("print(1 / 0);");
    let tokens = lexer.tokenize().unwrap();
    let mut parser = Parser::new(tokens);
    let program = parser.parse().unwrap();
    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program).unwrap();
    let functions = codegen.get_functions().to_vec();
    let mut vm = VM::new(instructions, functions);
    assert!(vm.run().is_err());
}

#[test]
fn test_error_wrong_arg_count() {
    let mut lexer = Lexer::new(
        r#"
        fn add(x, y) { return x + y; }
        print(add(1));
        "#,
    );
    let tokens = lexer.tokenize().unwrap();
    let mut parser = Parser::new(tokens);
    let program = parser.parse().unwrap();
    let mut codegen = CodeGenerator::new();
    let instructions = codegen.generate(&program).unwrap();
    let functions = codegen.get_functions().to_vec();
    let mut vm = VM::new(instructions, functions);
    assert!(vm.run().is_err());
}
