/// Token types for the Simple Language
#[derive(Debug, Clone, PartialEq)]
pub enum TokenKind {
    // Literals
    Integer(i64),
    Float(f64),
    StringLiteral(String),
    Identifier(String),

    // Keywords
    Let,
    If,
    Else,
    While,
    Fn,
    Return,
    Print,
    True,
    False,

    // Operators
    Plus,         // +
    Minus,        // -
    Star,         // *
    Slash,        // /
    Percent,      // %
    Equal,        // =
    EqualEqual,   // ==
    BangEqual,    // !=
    Less,         // <
    LessEqual,    // <=
    Greater,      // >
    GreaterEqual, // >=
    Bang,         // !
    AmpAmp,       // &&
    PipePipe,     // ||

    // Delimiters
    LeftParen,    // (
    RightParen,   // )
    LeftBrace,    // {
    RightBrace,   // }
    Comma,        // ,
    Semicolon,    // ;
    Colon,        // :
    Arrow,        // ->

    // Special
    Eof,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Token {
    pub kind: TokenKind,
    pub line: usize,
    pub column: usize,
}

impl Token {
    pub fn new(kind: TokenKind, line: usize, column: usize) -> Self {
        Self { kind, line, column }
    }
}

/// Lexer - converts source code into a stream of tokens
///
/// The lexer is the first phase of compilation. It reads the source code
/// character by character and groups them into meaningful tokens.
pub struct Lexer {
    source: Vec<char>,
    pos: usize,
    line: usize,
    column: usize,
}

impl Lexer {
    pub fn new(source: &str) -> Self {
        Self {
            source: source.chars().collect(),
            pos: 0,
            line: 1,
            column: 1,
        }
    }

    /// Tokenize the entire source code
    pub fn tokenize(&mut self) -> Result<Vec<Token>, String> {
        let mut tokens = Vec::new();

        loop {
            self.skip_whitespace_and_comments();
            if self.is_at_end() {
                tokens.push(Token::new(TokenKind::Eof, self.line, self.column));
                break;
            }

            let token = self.next_token()?;
            tokens.push(token);
        }

        Ok(tokens)
    }

    fn next_token(&mut self) -> Result<Token, String> {
        let line = self.line;
        let column = self.column;
        let ch = self.advance();

        match ch {
            // Single-character tokens
            '(' => Ok(Token::new(TokenKind::LeftParen, line, column)),
            ')' => Ok(Token::new(TokenKind::RightParen, line, column)),
            '{' => Ok(Token::new(TokenKind::LeftBrace, line, column)),
            '}' => Ok(Token::new(TokenKind::RightBrace, line, column)),
            ',' => Ok(Token::new(TokenKind::Comma, line, column)),
            ';' => Ok(Token::new(TokenKind::Semicolon, line, column)),
            ':' => Ok(Token::new(TokenKind::Colon, line, column)),
            '+' => Ok(Token::new(TokenKind::Plus, line, column)),
            '*' => Ok(Token::new(TokenKind::Star, line, column)),
            '%' => Ok(Token::new(TokenKind::Percent, line, column)),

            // Two-character tokens
            '-' => {
                if self.match_char('>') {
                    Ok(Token::new(TokenKind::Arrow, line, column))
                } else {
                    Ok(Token::new(TokenKind::Minus, line, column))
                }
            }
            '=' => {
                if self.match_char('=') {
                    Ok(Token::new(TokenKind::EqualEqual, line, column))
                } else {
                    Ok(Token::new(TokenKind::Equal, line, column))
                }
            }
            '!' => {
                if self.match_char('=') {
                    Ok(Token::new(TokenKind::BangEqual, line, column))
                } else {
                    Ok(Token::new(TokenKind::Bang, line, column))
                }
            }
            '<' => {
                if self.match_char('=') {
                    Ok(Token::new(TokenKind::LessEqual, line, column))
                } else {
                    Ok(Token::new(TokenKind::Less, line, column))
                }
            }
            '>' => {
                if self.match_char('=') {
                    Ok(Token::new(TokenKind::GreaterEqual, line, column))
                } else {
                    Ok(Token::new(TokenKind::Greater, line, column))
                }
            }
            '&' => {
                if self.match_char('&') {
                    Ok(Token::new(TokenKind::AmpAmp, line, column))
                } else {
                    Err(format!("Unexpected character '&' at {}:{}", line, column))
                }
            }
            '|' => {
                if self.match_char('|') {
                    Ok(Token::new(TokenKind::PipePipe, line, column))
                } else {
                    Err(format!("Unexpected character '|' at {}:{}", line, column))
                }
            }
            '/' => Ok(Token::new(TokenKind::Slash, line, column)),

            // String literals
            '"' => self.read_string(line, column),

            // Numbers and identifiers
            _ if ch.is_ascii_digit() => self.read_number(ch, line, column),
            _ if ch.is_ascii_alphabetic() || ch == '_' => self.read_identifier(ch, line, column),

            _ => Err(format!("Unexpected character '{}' at {}:{}", ch, line, column)),
        }
    }

    fn read_string(&mut self, line: usize, column: usize) -> Result<Token, String> {
        let mut value = String::new();
        loop {
            if self.is_at_end() {
                return Err(format!("Unterminated string at {}:{}", line, column));
            }
            let ch = self.advance();
            if ch == '"' {
                break;
            }
            if ch == '\\' {
                let escaped = self.advance();
                match escaped {
                    'n' => value.push('\n'),
                    't' => value.push('\t'),
                    '\\' => value.push('\\'),
                    '"' => value.push('"'),
                    _ => return Err(format!("Invalid escape sequence '\\{}' at {}:{}", escaped, line, column)),
                }
            } else {
                value.push(ch);
            }
        }
        Ok(Token::new(TokenKind::StringLiteral(value), line, column))
    }

    fn read_number(&mut self, first: char, line: usize, column: usize) -> Result<Token, String> {
        let mut text = String::from(first);
        let mut is_float = false;

        while !self.is_at_end() && (self.peek().is_ascii_digit() || self.peek() == '.') {
            if self.peek() == '.' {
                if is_float {
                    return Err(format!("Invalid number at {}:{}", line, column));
                }
                is_float = true;
            }
            text.push(self.advance());
        }

        if is_float {
            text.parse::<f64>()
                .map(|v| Token::new(TokenKind::Float(v), line, column))
                .map_err(|_| format!("Invalid float at {}:{}", line, column))
        } else {
            text.parse::<i64>()
                .map(|v| Token::new(TokenKind::Integer(v), line, column))
                .map_err(|_| format!("Invalid integer at {}:{}", line, column))
        }
    }

    fn read_identifier(&mut self, first: char, line: usize, column: usize) -> Result<Token, String> {
        let mut text = String::from(first);
        while !self.is_at_end() && (self.peek().is_ascii_alphanumeric() || self.peek() == '_') {
            text.push(self.advance());
        }

        let kind = match text.as_str() {
            "let" => TokenKind::Let,
            "if" => TokenKind::If,
            "else" => TokenKind::Else,
            "while" => TokenKind::While,
            "fn" => TokenKind::Fn,
            "return" => TokenKind::Return,
            "print" => TokenKind::Print,
            "true" => TokenKind::True,
            "false" => TokenKind::False,
            _ => TokenKind::Identifier(text),
        };

        Ok(Token::new(kind, line, column))
    }

    fn skip_whitespace_and_comments(&mut self) {
        loop {
            if self.is_at_end() {
                return;
            }
            match self.peek() {
                ' ' | '\t' | '\r' => {
                    self.advance();
                }
                '\n' => {
                    self.advance();
                    self.line += 1;
                    self.column = 1;
                }
                '/' if self.peek_next() == '/' => {
                    // Line comment
                    while !self.is_at_end() && self.peek() != '\n' {
                        self.advance();
                    }
                }
                '/' if self.peek_next() == '*' => {
                    // Block comment
                    self.advance(); // skip /
                    self.advance(); // skip *
                    let mut depth = 1;
                    while depth > 0 && !self.is_at_end() {
                        if self.peek() == '/' && self.peek_next() == '*' {
                            self.advance();
                            self.advance();
                            depth += 1;
                        } else if self.peek() == '*' && self.peek_next() == '/' {
                            self.advance();
                            self.advance();
                            depth -= 1;
                        } else {
                            if self.peek() == '\n' {
                                self.line += 1;
                                self.column = 0;
                            }
                            self.advance();
                        }
                    }
                }
                _ => return,
            }
        }
    }

    fn advance(&mut self) -> char {
        let ch = self.source[self.pos];
        self.pos += 1;
        self.column += 1;
        ch
    }

    fn peek(&self) -> char {
        if self.is_at_end() {
            '\0'
        } else {
            self.source[self.pos]
        }
    }

    fn peek_next(&self) -> char {
        if self.pos + 1 >= self.source.len() {
            '\0'
        } else {
            self.source[self.pos + 1]
        }
    }

    fn match_char(&mut self, expected: char) -> bool {
        if self.is_at_end() || self.source[self.pos] != expected {
            false
        } else {
            self.advance();
            true
        }
    }

    fn is_at_end(&self) -> bool {
        self.pos >= self.source.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_source() {
        let mut lexer = Lexer::new("");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].kind, TokenKind::Eof);
    }

    #[test]
    fn test_single_tokens() {
        let mut lexer = Lexer::new("+ - * / ( ) { } ; =");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Plus);
        assert_eq!(tokens[1].kind, TokenKind::Minus);
        assert_eq!(tokens[2].kind, TokenKind::Star);
        assert_eq!(tokens[3].kind, TokenKind::Slash);
        assert_eq!(tokens[4].kind, TokenKind::LeftParen);
        assert_eq!(tokens[5].kind, TokenKind::RightParen);
        assert_eq!(tokens[6].kind, TokenKind::LeftBrace);
        assert_eq!(tokens[7].kind, TokenKind::RightBrace);
        assert_eq!(tokens[8].kind, TokenKind::Semicolon);
        assert_eq!(tokens[9].kind, TokenKind::Equal);
    }

    #[test]
    fn test_two_char_operators() {
        let mut lexer = Lexer::new("== != <= >= && || ->");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::EqualEqual);
        assert_eq!(tokens[1].kind, TokenKind::BangEqual);
        assert_eq!(tokens[2].kind, TokenKind::LessEqual);
        assert_eq!(tokens[3].kind, TokenKind::GreaterEqual);
        assert_eq!(tokens[4].kind, TokenKind::AmpAmp);
        assert_eq!(tokens[5].kind, TokenKind::PipePipe);
        assert_eq!(tokens[6].kind, TokenKind::Arrow);
    }

    #[test]
    fn test_integer_literal() {
        let mut lexer = Lexer::new("42 0 100000");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Integer(42));
        assert_eq!(tokens[1].kind, TokenKind::Integer(0));
        assert_eq!(tokens[2].kind, TokenKind::Integer(100000));
    }

    #[test]
    fn test_float_literal() {
        let mut lexer = Lexer::new("3.14 0.5 100.0");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Float(3.14));
        assert_eq!(tokens[1].kind, TokenKind::Float(0.5));
        assert_eq!(tokens[2].kind, TokenKind::Float(100.0));
    }

    #[test]
    fn test_string_literal() {
        let mut lexer = Lexer::new(r#""hello" "world\n""#);
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::StringLiteral("hello".to_string()));
        assert_eq!(tokens[1].kind, TokenKind::StringLiteral("world\n".to_string()));
    }

    #[test]
    fn test_keywords() {
        let mut lexer = Lexer::new("let if else while fn return print true false");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Let);
        assert_eq!(tokens[1].kind, TokenKind::If);
        assert_eq!(tokens[2].kind, TokenKind::Else);
        assert_eq!(tokens[3].kind, TokenKind::While);
        assert_eq!(tokens[4].kind, TokenKind::Fn);
        assert_eq!(tokens[5].kind, TokenKind::Return);
        assert_eq!(tokens[6].kind, TokenKind::Print);
        assert_eq!(tokens[7].kind, TokenKind::True);
        assert_eq!(tokens[8].kind, TokenKind::False);
    }

    #[test]
    fn test_identifiers() {
        let mut lexer = Lexer::new("foo bar_baz x1");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Identifier("foo".to_string()));
        assert_eq!(tokens[1].kind, TokenKind::Identifier("bar_baz".to_string()));
        assert_eq!(tokens[2].kind, TokenKind::Identifier("x1".to_string()));
    }

    #[test]
    fn test_comments() {
        let mut lexer = Lexer::new("42 // this is a comment\n10");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Integer(42));
        assert_eq!(tokens[1].kind, TokenKind::Integer(10));
    }

    #[test]
    fn test_block_comment() {
        let mut lexer = Lexer::new("42 /* block\ncomment */ 10");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Integer(42));
        assert_eq!(tokens[1].kind, TokenKind::Integer(10));
    }

    #[test]
    fn test_let_statement() {
        let mut lexer = Lexer::new("let x = 42;");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].kind, TokenKind::Let);
        assert_eq!(tokens[1].kind, TokenKind::Identifier("x".to_string()));
        assert_eq!(tokens[2].kind, TokenKind::Equal);
        assert_eq!(tokens[3].kind, TokenKind::Integer(42));
        assert_eq!(tokens[4].kind, TokenKind::Semicolon);
    }

    #[test]
    fn test_error_unterminated_string() {
        let mut lexer = Lexer::new(r#""hello"#);
        assert!(lexer.tokenize().is_err());
    }

    #[test]
    fn test_error_invalid_character() {
        let mut lexer = Lexer::new("@");
        assert!(lexer.tokenize().is_err());
    }

    #[test]
    fn test_line_and_column_tracking() {
        let mut lexer = Lexer::new("let\n  x = 42;");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].line, 1);
        assert_eq!(tokens[0].column, 1);
        assert_eq!(tokens[1].line, 2);
        assert_eq!(tokens[1].column, 3);
    }
}
