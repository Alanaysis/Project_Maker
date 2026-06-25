// Token 类型定义

export enum TokenType {
  Keyword = 'keyword',
  Identifier = 'identifier',
  String = 'string',
  Number = 'number',
  Comment = 'comment',
  Operator = 'operator',
  Punctuation = 'punctuation',
  Whitespace = 'whitespace',
  Unknown = 'unknown'
}

export interface Token {
  type: TokenType;
  value: string;
  start: number;
  end: number;
  line: number;
}
