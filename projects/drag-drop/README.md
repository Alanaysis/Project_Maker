# 拖拽系统 (Drag & Drop System)

## 学习目标

通过这个项目，你将掌握：
- [ ] 理解 HTML5 拖拽 API（Drag and Drop API）的工作原理
- [ ] 掌握拖拽排序算法的实现
- [ ] 学会文件拖拽上传的完整流程
- [ ] 理解拖拽预览的创建和优化
- [ ] 掌握拖拽系统的性能优化技巧

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| TypeScript | 主语言 | ⭐⭐ |
| DOM API | 操作文档对象 | ⭐⭐ |
| HTML5 Drag API | 拖拽功能 | ⭐⭐⭐ |
| File API | 文件处理 | ⭐⭐ |
| Jest | 单元测试 | ⭐⭐ |

## 重点难点

### 重点1：拖拽事件生命周期
**为什么重要**：理解拖拽事件的完整生命周期是实现拖拽系统的基础
**关键代码**：`src/drag-manager.ts`
**理解要点**：
- `dragstart` → `drag` → `dragend` 是核心事件链
- `dragenter` → `dragover` → `dragleave` → `drop` 是目标区域事件
- 需要正确处理事件冒泡和默认行为

### 重点2：拖拽排序算法
**为什么重要**：排序是拖拽系统最常用的功能
**关键代码**：`src/sortable.ts`
**理解要点**：
- 使用占位符（Placeholder）指示放置位置
- 计算鼠标位置与元素中心点的关系
- 支持动画过渡效果

### 重点3：文件拖拽上传
**为什么重要**：文件上传是现代 Web 应用的常见需求
**关键代码**：`src/file-upload.ts`
**理解要点**：
- 使用 `DataTransfer` 对象获取拖拽的文件
- 验证文件类型和大小
- 生成文件预览

## 值得思考

### 1. 为什么不直接使用 HTML5 原生拖拽 API？
**背景**：HTML5 提供了原生的拖拽 API
**权衡**：原生 API 在不同浏览器上有兼容性问题，且样式定制困难
**结论**：封装统一的拖拽系统，提供更好的开发体验和兼容性

### 2. 如何优化大量元素的拖拽性能？
**背景**：拖拽排序时需要频繁计算位置和更新 DOM
**权衡**：每次移动都重新计算会导致性能问题
**结论**：使用节流（Throttle）和虚拟滚动优化性能

### 3. 如何处理跨容器拖拽？
**背景**：实际应用中经常需要在不同容器间拖拽元素
**权衡**：跨容器拖拽增加了状态管理的复杂度
**结论**：使用分组（Group）机制实现跨容器拖拽

## 快速开始

### 环境要求
- Node.js 16+
- npm 或 yarn

### 安装

```bash
cd projects/drag-drop
npm install
```

### 编译

```bash
npm run build
```

### 运行示例

```bash
# 运行排序示例
npm run example:sortable

# 运行上传示例
npm run example:upload

# 运行预览示例
npm run example:preview
```

### 运行测试

```bash
# 运行所有测试
npm test

# 运行测试并监听变化
npm run test:watch

# 运行测试并生成覆盖率报告
npm run test:coverage
```

## 项目结构

```
drag-drop/
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
├── jest.config.js         # Jest 测试配置
├── README.md              # 本文件
├── src/                   # 源代码
│   ├── index.ts           # 主入口
│   ├── types.ts           # 类型定义
│   ├── utils.ts           # 工具函数
│   ├── drag-manager.ts    # 拖拽管理器
│   ├── sortable.ts        # 拖拽排序
│   └── file-upload.ts     # 文件上传
├── tests/                 # 测试
│   ├── utils.test.ts      # 工具函数测试
│   ├── drag-manager.test.ts # 拖拽管理器测试
│   ├── sortable.test.ts   # 排序测试
│   └── file-upload.test.ts # 文件上传测试
├── examples/              # 示例
│   ├── sortable-example.ts # 排序示例
│   ├── upload-example.ts  # 上传示例
│   └── preview-example.ts # 预览示例
├── docs/                  # 文档
│   ├── 01-RESEARCH.md     # 市场调研
│   ├── 02-DESIGN.md       # 技术设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md      # 测试策略
│   └── 05-DEVELOPMENT.md  # 开发手册
└── LEARNING_NOTES.md      # 学习笔记
```

## 核心循环

```
拖拽开始 → 拖拽中 → 位置计算 → 元素移动 → 拖拽结束
```

## 学习路径

1. 阅读 [01-RESEARCH.md](docs/01-RESEARCH.md) 了解拖拽系统的背景
2. 阅读 [02-DESIGN.md](docs/02-DESIGN.md) 学习系统设计
3. 阅读 [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) 理解实现细节
4. 阅读 [04-TESTING.md](docs/04-TESTING.md) 学习测试策略
5. 阅读 [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) 开始开发
6. 运行 [examples/](examples/) 中的示例
7. 阅读源代码，重点关注 ⭐ 标记的部分
8. 完成 [LEARNING_NOTES.md](LEARNING_NOTES.md) 中的练习

## 相关资源

- [MDN - Drag and Drop API](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)
- [MDN - File API](https://developer.mozilla.org/en-US/docs/Web/API/File_API)
- [SortableJS](https://sortablejs.github.io/Sortable/)
- [dragula](https://github.com/bevacqua/dragula)
- [React DnD](https://react-dnd.github.io/react-dnd/)

---

[返回应用模块](../APPS_README.md) | [返回主目录](../../README.md)
