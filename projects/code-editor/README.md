# 代码编辑器

基于 Canvas 的简单代码编辑器，支持语法高亮和基本编辑功能。

## 项目简介

这是一个学习型项目，旨在帮助理解：

1. **编辑器架构** - 分层设计、数据流管理
2. **语法高亮** - 词法分析、状态机实现
3. **光标管理** - 位置计算、选择管理

## 功能特性

- 文本编辑（插入、删除、换行）
- 语法高亮（TypeScript/JavaScript）
- 光标管理（移动、选择）
- 基本快捷键（撤销、重做、全选）
- 行号显示
- Canvas 渲染

## 技术栈

- **语言**: TypeScript
- **渲染**: Canvas API
- **测试**: Jest
- **构建**: TypeScript Compiler

## 项目结构

```
code-editor/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── document.ts    # 文档模型
│   │   ├── cursor.ts      # 光标管理
│   │   └── types.ts       # 类型定义
│   ├── highlight/         # 语法高亮
│   │   ├── syntax.ts      # 高亮器实现
│   │   └── token.ts       # Token 定义
│   ├── render/            # 渲染模块
│   │   └── canvas.ts      # Canvas 渲染器
│   ├── editor.ts          # 编辑器主类
│   └── index.ts           # 入口文件
├── tests/                 # 测试文件
├── examples/              # 示例文件
├── docs/                  # 文档
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
└── jest.config.js         # 测试配置
```

## 快速开始

### 安装依赖

```bash
cd projects/code-editor
npm install
```

### 运行测试

```bash
npm test
```

### 构建项目

```bash
npm run build
```

### 运行示例

在浏览器中打开 `examples/basic.html` 文件。

## 核心模块

### 1. Document Model

文档模型负责管理文本内容和编辑操作：

```typescript
const doc = new DocumentModel('Hello World');
doc.insert({ line: 0, column: 5 }, ', TypeScript');
doc.delete({ start: { line: 0, column: 0 }, end: { line: 0, column: 5 } });
```

### 2. Cursor Manager

光标管理器负责光标位置和选择管理：

```typescript
const cursor = new CursorManager(doc);
cursor.moveRight();
cursor.moveDown();
cursor.selectTo({ line: 1, column: 10 });
```

### 3. Syntax Highlighter

语法高亮器基于状态机实现词法分析：

```typescript
const highlighter = new TypeScriptHighlighter();
const tokens = highlighter.tokenizeLine('const x = 42;', 0);
// tokens: [Keyword, Whitespace, Identifier, Whitespace, Operator, Whitespace, Number, Punctuation]
```

### 4. Canvas Renderer

Canvas 渲染器负责将编辑器状态渲染到画布：

```typescript
const renderer = new CanvasRenderer(canvas);
renderer.render(editorState);
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Z | 撤销 |
| Ctrl+Y | 重做 |
| Ctrl+A | 全选 |
| ← → ↑ ↓ | 移动光标 |
| Shift+方向键 | 选择文本 |
| Tab | 插入缩进 |
| Enter | 插入新行 |
| Backspace | 删除左侧字符 |
| Delete | 删除右侧字符 |

## 学习路径

1. **阅读文档**
   - [市场调研](docs/01-RESEARCH.md)
   - [架构设计](docs/02-ARCHITECTURE.md)
   - [实现指南](docs/03-IMPLEMENTATION.md)
   - [测试指南](docs/04-TESTING.md)
   - [开发指南](docs/05-DEVELOPMENT.md)

2. **理解核心模块**
   - Document Model - 文本存储和编辑
   - Cursor Manager - 光标位置管理
   - Syntax Highlighter - 语法高亮
   - Canvas Renderer - 渲染输出

3. **运行和调试**
   - 运行测试了解各模块功能
   - 修改代码观察变化
   - 添加新功能加深理解

## 扩展方向

1. **功能扩展**
   - 查找替换
   - 代码折叠
   - 自动补全
   - 多光标编辑

2. **性能优化**
   - 虚拟化渲染
   - 增量语法分析
   - Web Worker 后台处理

3. **用户体验**
   - 主题系统
   - 快捷键自定义
   - 插件系统

## 参考资源

- [CodeMirror](https://codemirror.net/) - 现代代码编辑器
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) - VS Code 编辑器组件
- [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API) - 渲染技术

## 许可证

MIT License
