// 代码编辑器核心类型定义

// 位置
export interface Position {
  line: number;
  column: number;
}

// 范围
export interface Range {
  start: Position;
  end: Position;
}

// 编辑操作（用于撤销/重做）
export interface EditOperation {
  range: Range;
  text: string;
  inverse: EditOperation;
}

// 光标
export interface Cursor {
  position: Position;
  selection?: Range;
  visible: boolean;
}

// Token 类型
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

// Token
export interface Token {
  type: TokenType;
  value: string;
  start: number;
  end: number;
  line: number;
}

// 滚动位置
export interface ScrollPosition {
  top: number;
  left: number;
}

// 视口
export interface Viewport {
  topLine: number;
  bottomLine: number;
  leftColumn: number;
}

// 编辑器状态
export interface EditorState {
  document: any;
  cursors: Cursor[];
  selections: Range[];
  tokens: Token[][];
  scroll: ScrollPosition;
  viewport: Viewport;
  config: any;
}

// 渲染配置
export interface RenderConfig {
  fontSize?: number;
  fontFamily?: string;
  lineHeight?: number;
  tabSize?: number;
  padding?: number;
  showLineNumbers?: boolean;
  lineNumberWidth?: number;
}

// 编辑器选项
export interface EditorOptions {
  initialContent?: string;
  renderConfig?: Partial<RenderConfig>;
}
