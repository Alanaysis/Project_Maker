use crate::ast::*;
use crate::lexer::{Token, TokenKind};

/// Parser - converts tokens into an Abstract Syntax Tree
///
/// Uses recursive descent parsing, one of the simplest and most
/// intuitive parsing techniques. Each grammar rule maps to a function.
///
/// Grammar (simplified):
///   program     -> statement*
///   statement   -> let_stmt | assign_stmt | print_stmt | if_stmt
///                | while_stmt | fn_def | return_stmt | expr_stmt
///   let_stmt    -> "let" IDENT "=" expr ";"
///   assign_stmt -> IDENT "=" expr ";"
///   print_stmt  -> "print" "(" expr ("," expr)* ")" ";"
///   if_stmt     -> "if" expr block ("else" block)?
///   while_stmt  -> "while" expr block
///   fn_def      -> "fn" IDENT "(" params? ")" ("->" type)? block
///   return_stmt -> "return" expr? ";"
///   block       -> "{" statement* "}"
///
///   expr        -> or_expr
///   or_expr     -> and_expr ("||" and_expr)*
///   and_expr    -> equality ("&&" equality)*
///   equality    -> comparison (("==" | "!=") comparison)*
///   comparison  -> addition (("<" | "<=" | ">" | ">=") addition)*
///   addition    -> multiplication (("+" | "-") multiplication)*
///   multiplication -> unary (("*" | "/" | "%") unary)*
///   unary       -> ("-" | "!") unary | call
///   call        -> primary ("(" args? ")")?
///   primary     -> INTEGER | FLOAT | STRING | "true" | "false"
///                | IDENT | "(" expr ")"
pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, pos: 0 }
    }

    /// Parse the token stream into an AST
    pub fn parse(&mut self) -> Result<Program, String> {
        let mut statements = Vec::new();

        while !self.check(&TokenKind::Eof) {
            statements.push(self.parse_statement()?);
        }

        Ok(Program { statements })
    }

    fn parse_statement(&mut self) -> Result<Statement, String> {
        match &self.peek().kind {
            TokenKind::Let => self.parse_let(),
            TokenKind::If => self.parse_if(),
            TokenKind::While => self.parse_while(),
            TokenKind::Fn => self.parse_fn_def(),
            TokenKind::Return => self.parse_return(),
            TokenKind::Print => self.parse_print(),
            TokenKind::Identifier(_) => {
                // Could be assignment or expression statement
                if self.peek_next_kind() == Some(&TokenKind::Equal) {
                    self.parse_assign()
                } else {
                    self.parse_expr_stmt()
                }
            }
            _ => self.parse_expr_stmt(),
        }
    }

    fn parse_let(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::Let)?;
        let name = self.expect_identifier()?;
        self.expect(&TokenKind::Equal)?;
        let value = self.parse_expression()?;
        self.expect(&TokenKind::Semicolon)?;

        Ok(Statement::Let {
            name,
            type_ann: None,
            value,
        })
    }

    fn parse_assign(&mut self) -> Result<Statement, String> {
        let name = self.expect_identifier()?;
        self.expect(&TokenKind::Equal)?;
        let value = self.parse_expression()?;
        self.expect(&TokenKind::Semicolon)?;

        Ok(Statement::Assign { name, value })
    }

    fn parse_print(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::Print)?;
        self.expect(&TokenKind::LeftParen)?;

        let mut args = Vec::new();
        if !self.check(&TokenKind::RightParen) {
            args.push(self.parse_expression()?);
            while self.check(&TokenKind::Comma) {
                self.advance();
                args.push(self.parse_expression()?);
            }
        }

        self.expect(&TokenKind::RightParen)?;
        self.expect(&TokenKind::Semicolon)?;

        Ok(Statement::Print { args })
    }

    fn parse_if(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::If)?;
        let condition = self.parse_expression()?;
        let then_block = self.parse_block()?;

        let else_block = if self.check(&TokenKind::Else) {
            self.advance();
            if self.check(&TokenKind::If) {
                // else if: wrap in a single-statement block
                Some(vec![self.parse_if()?])
            } else {
                Some(self.parse_block()?)
            }
        } else {
            None
        };

        Ok(Statement::If {
            condition,
            then_block,
            else_block,
        })
    }

    fn parse_while(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::While)?;
        let condition = self.parse_expression()?;
        let body = self.parse_block()?;

        Ok(Statement::While { condition, body })
    }

    fn parse_fn_def(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::Fn)?;
        let name = self.expect_identifier()?;
        self.expect(&TokenKind::LeftParen)?;

        let mut params = Vec::new();
        if !self.check(&TokenKind::RightParen) {
            params.push(self.parse_param()?);
            while self.check(&TokenKind::Comma) {
                self.advance();
                params.push(self.parse_param()?);
            }
        }

        self.expect(&TokenKind::RightParen)?;

        let return_type = if self.check(&TokenKind::Arrow) {
            self.advance();
            Some(self.parse_type()?)
        } else {
            None
        };

        let body = self.parse_block()?;

        Ok(Statement::FunctionDef {
            name,
            params,
            return_type,
            body,
        })
    }

    fn parse_param(&mut self) -> Result<Param, String> {
        let name = self.expect_identifier()?;
        let type_ann = if self.check(&TokenKind::Colon) {
            self.advance();
            Some(self.parse_type()?)
        } else {
            None
        };
        Ok(Param { name, type_ann })
    }

    fn parse_type(&mut self) -> Result<TypeExpr, String> {
        let name = self.expect_identifier()?;
        match name.as_str() {
            "int" => Ok(TypeExpr::Int),
            "float" => Ok(TypeExpr::Float),
            "bool" => Ok(TypeExpr::Bool),
            "string" => Ok(TypeExpr::String),
            _ => Err(format!("Unknown type '{}' at {}:{}", name, self.peek().line, self.peek().column)),
        }
    }

    fn parse_return(&mut self) -> Result<Statement, String> {
        self.expect(&TokenKind::Return)?;

        let value = if self.check(&TokenKind::Semicolon) {
            None
        } else {
            Some(self.parse_expression()?)
        };

        self.expect(&TokenKind::Semicolon)?;

        Ok(Statement::Return { value })
    }

    fn parse_expr_stmt(&mut self) -> Result<Statement, String> {
        let expr = self.parse_expression()?;
        self.expect(&TokenKind::Semicolon)?;
        Ok(Statement::Expression { expr })
    }

    fn parse_block(&mut self) -> Result<Vec<Statement>, String> {
        self.expect(&TokenKind::LeftBrace)?;
        let mut statements = Vec::new();

        while !self.check(&TokenKind::RightBrace) && !self.check(&TokenKind::Eof) {
            statements.push(self.parse_statement()?);
        }

        self.expect(&TokenKind::RightBrace)?;
        Ok(statements)
    }

    // Expression parsing with precedence climbing

    fn parse_expression(&mut self) -> Result<Expression, String> {
        self.parse_or()
    }

    fn parse_or(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_and()?;

        while self.check(&TokenKind::PipePipe) {
            self.advance();
            let right = self.parse_and()?;
            left = Expression::BinaryOp {
                op: BinaryOp::Or,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_and(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_equality()?;

        while self.check(&TokenKind::AmpAmp) {
            self.advance();
            let right = self.parse_equality()?;
            left = Expression::BinaryOp {
                op: BinaryOp::And,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_equality(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_comparison()?;

        while matches!(self.peek().kind, TokenKind::EqualEqual | TokenKind::BangEqual) {
            let op = match self.advance().kind {
                TokenKind::EqualEqual => BinaryOp::Eq,
                TokenKind::BangEqual => BinaryOp::NotEq,
                _ => unreachable!(),
            };
            let right = self.parse_comparison()?;
            left = Expression::BinaryOp {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_comparison(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_addition()?;

        while matches!(
            self.peek().kind,
            TokenKind::Less | TokenKind::LessEqual | TokenKind::Greater | TokenKind::GreaterEqual
        ) {
            let op = match self.advance().kind {
                TokenKind::Less => BinaryOp::Lt,
                TokenKind::LessEqual => BinaryOp::LtEq,
                TokenKind::Greater => BinaryOp::Gt,
                TokenKind::GreaterEqual => BinaryOp::GtEq,
                _ => unreachable!(),
            };
            let right = self.parse_addition()?;
            left = Expression::BinaryOp {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_addition(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_multiplication()?;

        while matches!(self.peek().kind, TokenKind::Plus | TokenKind::Minus) {
            let op = match self.advance().kind {
                TokenKind::Plus => BinaryOp::Add,
                TokenKind::Minus => BinaryOp::Sub,
                _ => unreachable!(),
            };
            let right = self.parse_multiplication()?;
            left = Expression::BinaryOp {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_multiplication(&mut self) -> Result<Expression, String> {
        let mut left = self.parse_unary()?;

        while matches!(
            self.peek().kind,
            TokenKind::Star | TokenKind::Slash | TokenKind::Percent
        ) {
            let op = match self.advance().kind {
                TokenKind::Star => BinaryOp::Mul,
                TokenKind::Slash => BinaryOp::Div,
                TokenKind::Percent => BinaryOp::Mod,
                _ => unreachable!(),
            };
            let right = self.parse_unary()?;
            left = Expression::BinaryOp {
                op,
                left: Box::new(left),
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn parse_unary(&mut self) -> Result<Expression, String> {
        if matches!(self.peek().kind, TokenKind::Minus | TokenKind::Bang) {
            let op = match self.advance().kind {
                TokenKind::Minus => UnaryOp::Neg,
                TokenKind::Bang => UnaryOp::Not,
                _ => unreachable!(),
            };
            let operand = self.parse_unary()?;
            return Ok(Expression::UnaryOp {
                op,
                operand: Box::new(operand),
            });
        }

        self.parse_call()
    }

    fn parse_call(&mut self) -> Result<Expression, String> {
        let expr = self.parse_primary()?;

        if self.check(&TokenKind::LeftParen) {
            if let Expression::Identifier(name) = expr {
                self.advance(); // consume (
                let mut args = Vec::new();

                if !self.check(&TokenKind::RightParen) {
                    args.push(self.parse_expression()?);
                    while self.check(&TokenKind::Comma) {
                        self.advance();
                        args.push(self.parse_expression()?);
                    }
                }

                self.expect(&TokenKind::RightParen)?;
                return Ok(Expression::Call { name, args });
            }
        }

        Ok(expr)
    }

    fn parse_primary(&mut self) -> Result<Expression, String> {
        let token = self.advance();
        match &token.kind {
            TokenKind::Integer(n) => Ok(Expression::IntegerLiteral(*n)),
            TokenKind::Float(f) => Ok(Expression::FloatLiteral(*f)),
            TokenKind::StringLiteral(s) => Ok(Expression::StringLiteral(s.clone())),
            TokenKind::True => Ok(Expression::BoolLiteral(true)),
            TokenKind::False => Ok(Expression::BoolLiteral(false)),
            TokenKind::Identifier(name) => Ok(Expression::Identifier(name.clone())),
            TokenKind::LeftParen => {
                let expr = self.parse_expression()?;
                self.expect(&TokenKind::RightParen)?;
                Ok(expr)
            }
            _ => Err(format!(
                "Unexpected token {:?} at {}:{}",
                token.kind, token.line, token.column
            )),
        }
    }

    // Helper methods

    fn advance(&mut self) -> &Token {
        if !self.is_at_end() {
            self.pos += 1;
        }
        &self.tokens[self.pos - 1]
    }

    fn peek(&self) -> &Token {
        &self.tokens[self.pos]
    }

    fn peek_next_kind(&self) -> Option<&TokenKind> {
        if self.pos + 1 < self.tokens.len() {
            Some(&self.tokens[self.pos + 1].kind)
        } else {
            None
        }
    }

    fn check(&self, kind: &TokenKind) -> bool {
        std::mem::discriminant(&self.peek().kind) == std::mem::discriminant(kind)
    }

    fn expect(&mut self, kind: &TokenKind) -> Result<&Token, String> {
        if std::mem::discriminant(&self.peek().kind) == std::mem::discriminant(kind) {
            Ok(self.advance())
        } else {
            Err(format!(
                "Expected {:?}, got {:?} at {}:{}",
                kind,
                self.peek().kind,
                self.peek().line,
                self.peek().column
            ))
        }
    }

    fn expect_identifier(&mut self) -> Result<String, String> {
        match &self.peek().kind {
            TokenKind::Identifier(name) => {
                let name = name.clone();
                self.advance();
                Ok(name)
            }
            other => Err(format!(
                "Expected identifier, got {:?} at {}:{}",
                other,
                self.peek().line,
                self.peek().column
            )),
        }
    }

    fn is_at_end(&self) -> bool {
        self.pos >= self.tokens.len() || self.tokens[self.pos].kind == TokenKind::Eof
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;

    fn parse(source: &str) -> Program {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        parser.parse().unwrap()
    }

    #[test]
    fn test_let_statement() {
        let program = parse("let x = 42;");
        assert_eq!(program.statements.len(), 1);
        match &program.statements[0] {
            Statement::Let { name, value, .. } => {
                assert_eq!(name, "x");
                assert_eq!(*value, Expression::IntegerLiteral(42));
            }
            _ => panic!("Expected Let statement"),
        }
    }

    #[test]
    fn test_binary_expression() {
        let program = parse("let x = 1 + 2 * 3;");
        match &program.statements[0] {
            Statement::Let { value, .. } => {
                // Should parse as 1 + (2 * 3)
                match value {
                    Expression::BinaryOp {
                        op: BinaryOp::Add,
                        left,
                        right,
                    } => {
                        assert_eq!(**left, Expression::IntegerLiteral(1));
                        match right.as_ref() {
                            Expression::BinaryOp {
                                op: BinaryOp::Mul,
                                left,
                                right,
                            } => {
                                assert_eq!(**left, Expression::IntegerLiteral(2));
                                assert_eq!(**right, Expression::IntegerLiteral(3));
                            }
                            _ => panic!("Expected Mul"),
                        }
                    }
                    _ => panic!("Expected Add"),
                }
            }
            _ => panic!("Expected Let"),
        }
    }

    #[test]
    fn test_parenthesized_expression() {
        let program = parse("let x = (1 + 2) * 3;");
        match &program.statements[0] {
            Statement::Let { value, .. } => {
                match value {
                    Expression::BinaryOp {
                        op: BinaryOp::Mul,
                        left,
                        ..
                    } => {
                        match left.as_ref() {
                            Expression::BinaryOp {
                                op: BinaryOp::Add, ..
                            } => {}
                            _ => panic!("Expected Add inside parens"),
                        }
                    }
                    _ => panic!("Expected Mul"),
                }
            }
            _ => panic!("Expected Let"),
        }
    }

    #[test]
    fn test_if_statement() {
        let program = parse("if x > 0 { print(x); }");
        match &program.statements[0] {
            Statement::If {
                condition,
                then_block,
                else_block,
            } => {
                assert!(matches!(condition, Expression::BinaryOp { op: BinaryOp::Gt, .. }));
                assert_eq!(then_block.len(), 1);
                assert!(else_block.is_none());
            }
            _ => panic!("Expected If"),
        }
    }

    #[test]
    fn test_if_else_statement() {
        let program = parse("if x > 0 { print(x); } else { print(0); }");
        match &program.statements[0] {
            Statement::If { else_block, .. } => {
                assert!(else_block.is_some());
                assert_eq!(else_block.as_ref().unwrap().len(), 1);
            }
            _ => panic!("Expected If"),
        }
    }

    #[test]
    fn test_while_statement() {
        let program = parse("while x > 0 { x = x - 1; }");
        match &program.statements[0] {
            Statement::While { condition, body } => {
                assert!(matches!(condition, Expression::BinaryOp { op: BinaryOp::Gt, .. }));
                assert_eq!(body.len(), 1);
            }
            _ => panic!("Expected While"),
        }
    }

    #[test]
    fn test_function_definition() {
        let program = parse("fn add(x, y) -> int { return x + y; }");
        match &program.statements[0] {
            Statement::FunctionDef {
                name,
                params,
                return_type,
                body,
            } => {
                assert_eq!(name, "add");
                assert_eq!(params.len(), 2);
                assert!(return_type.is_some());
                assert_eq!(body.len(), 1);
            }
            _ => panic!("Expected FunctionDef"),
        }
    }

    #[test]
    fn test_function_call() {
        let program = parse("print(add(1, 2));");
        match &program.statements[0] {
            Statement::Print { args } => {
                match &args[0] {
                    Expression::Call { name, args } => {
                        assert_eq!(name, "add");
                        assert_eq!(args.len(), 2);
                    }
                    _ => panic!("Expected Call"),
                }
            }
            _ => panic!("Expected Print"),
        }
    }

    #[test]
    fn test_comparison_operators() {
        let program = parse("let x = 1 < 2 && 3 > 2;");
        match &program.statements[0] {
            Statement::Let { value, .. } => {
                assert!(matches!(value, Expression::BinaryOp { op: BinaryOp::And, .. }));
            }
            _ => panic!("Expected Let"),
        }
    }

    #[test]
    fn test_unary_operators() {
        let program = parse("let x = -42;");
        match &program.statements[0] {
            Statement::Let { value, .. } => {
                match value {
                    Expression::UnaryOp { op, operand } => {
                        assert_eq!(*op, UnaryOp::Neg);
                        assert_eq!(**operand, Expression::IntegerLiteral(42));
                    }
                    _ => panic!("Expected UnaryOp"),
                }
            }
            _ => panic!("Expected Let"),
        }
    }

    #[test]
    fn test_error_unexpected_token() {
        let mut lexer = Lexer::new("let = 42;");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        assert!(parser.parse().is_err());
    }

    #[test]
    fn test_multiple_statements() {
        let program = parse("let x = 1; let y = 2; print(x + y);");
        assert_eq!(program.statements.len(), 3);
    }
}
