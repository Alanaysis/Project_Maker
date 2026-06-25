# 开发手册

## 1. 开发环境

### 环境要求

- Node.js 16+
- npm 或 yarn
- TypeScript 5.3+
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 安装依赖

```bash
cd projects/drag-drop
npm install
```

### 开发工具推荐

- VS Code
- TypeScript 插件
- ESLint 插件
- Prettier 插件

## 2. 项目结构

```
drag-drop/
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
├── jest.config.js         # Jest 测试配置
├── README.md              # 项目文档
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

## 3. 开发流程

### 1. 创建功能分支

```bash
git checkout -b feature/new-feature
```

### 2. 编写代码

- 遵循 TypeScript 编码规范
- 添加类型定义
- 编写注释和文档

### 3. 编写测试

```bash
# 运行测试
npm test

# 监听模式
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: add new feature"
```

### 5. 推送分支

```bash
git push origin feature/new-feature
```

### 6. 创建 Pull Request

## 4. 编码规范

### TypeScript 规范

```typescript
// 使用接口定义类型
interface User {
  id: number;
  name: string;
  email: string;
}

// 使用类型别名定义复杂类型
type EventHandler<T> = (data: T) => void;

// 使用枚举定义常量
enum DragState {
  IDLE = 'idle',
  PENDING = 'pending',
  DRAGGING = 'dragging',
}

// 使用泛型提高代码复用
function identity<T>(arg: T): T {
  return arg;
}
```

### 命名规范

```typescript
// 类名：PascalCase
class DragManager {}

// 接口名：PascalCase，可选 I 前缀
interface IDraggable {}
interface DragOptions {}

// 枚举名：PascalCase
enum DragState {}

// 变量和函数：camelCase
const dragManager = new DragManager();
function getElementRect() {}

// 常量：UPPER_SNAKE_CASE
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// 私有成员：下划线前缀（可选）
class MyClass {
  private _value: number = 0;
}
```

### 注释规范

```typescript
/**
 * 拖拽管理器
 *
 * 拖拽系统的核心模块，负责管理所有拖拽相关的事件和状态
 *
 * @example
 * ```typescript
 * const manager = new DragManager();
 * manager.makeDraggable(element, {
 *   onDragStart: () => console.log('开始拖拽'),
 * });
 * ```
 */
class DragManager {
  /**
   * 使元素可拖拽
   *
   * @param element - 要拖拽的元素
   * @param options - 拖拽配置选项
   * @returns 移除拖拽功能的函数
   */
  makeDraggable(element: HTMLElement, options: DragOptions = {}): RemoveEventListener {
    // 实现...
  }
}
```

## 5. 调试技巧

### 浏览器调试

```typescript
// 添加断点
function handleDragStart(event: DragEventData) {
  debugger; // 浏览器会在此处暂停
  console.log('拖拽开始', event);
}

// 使用 console 输出
console.log('当前状态:', this.state);
console.log('拖拽元素:', this.currentElement);
console.log('鼠标位置:', this.currentPosition);
```

### 单元测试调试

```typescript
// 使用 describe.only 只运行特定测试
describe.only('DragManager', () => {
  it('should work', () => {});
});

// 使用 it.only 只运行特定用例
describe('DragManager', () => {
  it.only('should work', () => {});
});

// 使用 debugger
it('should work', () => {
  debugger;
  // 测试代码...
});
```

### VS Code 调试配置

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Tests",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": ["--runInBand"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    }
  ]
}
```

## 6. 性能优化

### 节流和防抖

```typescript
import { throttle, debounce } from './utils';

// 节流：限制函数调用频率
const throttledHandler = throttle((position: Position) => {
  this.handleMove(position);
}, 16); // 约 60fps

// 防抖：延迟函数执行
const debouncedHandler = debounce((value: string) => {
  this.search(value);
}, 300);
```

### 虚拟滚动

```typescript
// 只渲染可见区域的元素
function getVisibleItems(
  items: HTMLElement[],
  scrollTop: number,
  viewportHeight: number
): HTMLElement[] {
  return items.filter(item => {
    const rect = item.getBoundingClientRect();
    return rect.bottom > 0 && rect.top < viewportHeight;
  });
}
```

### 批量 DOM 更新

```typescript
// 使用 requestAnimationFrame 批量更新
function batchUpdate(updates: (() => void)[]): void {
  requestAnimationFrame(() => {
    updates.forEach(update => update());
  });
}
```

## 7. 错误处理

### 验证错误

```typescript
function validateFile(file: File): UploadError | null {
  if (!validateFileType(file, accept)) {
    return {
      file,
      message: `不支持的文件类型: ${file.type}`,
      code: ErrorCode.FILE_TYPE_NOT_ACCEPTED,
    };
  }

  if (!validateFileSize(file, maxSize)) {
    return {
      file,
      message: `文件大小超过限制: ${formatFileSize(file.size)}`,
      code: ErrorCode.FILE_TOO_LARGE,
    };
  }

  return null;
}
```

### 状态错误

```typescript
private startDrag(element: HTMLElement, position: Position, options: DragOptions): void {
  if (this.state !== DragState.IDLE) {
    console.warn('Drag already in progress');
    return;
  }

  // 开始拖拽...
}
```

## 8. 发布流程

### 版本管理

```bash
# 更新版本号
npm version patch  # 1.0.0 -> 1.0.1
npm version minor  # 1.0.0 -> 1.1.0
npm version major  # 1.0.0 -> 2.0.0
```

### 构建

```bash
# 编译 TypeScript
npm run build

# 检查编译结果
ls dist/
```

### 发布到 npm

```bash
# 登录 npm
npm login

# 发布
npm publish
```

## 9. 常见问题

### Q: 拖拽不工作怎么办？

A: 检查以下几点：
1. 确保元素已添加到 DOM
2. 检查事件监听器是否正确绑定
3. 确认没有阻止默认行为
4. 检查浏览器控制台是否有错误

### Q: 排序动画不流畅怎么办？

A: 尝试以下优化：
1. 使用节流限制事件触发频率
2. 使用 requestAnimationFrame 更新动画
3. 减少 DOM 操作次数
4. 使用 CSS transform 代替 top/left

### Q: 文件上传失败怎么办？

A: 检查以下几点：
1. 确认文件类型是否被接受
2. 检查文件大小是否超过限制
3. 查看浏览器控制台的错误信息
4. 确认服务器端是否正常

### Q: 如何支持移动设备？

A: 本项目已支持触摸事件：
1. 自动检测触摸设备
2. 使用 touchstart/touchmove/touchend
3. 防止页面滚动
4. 支持多点触控

## 10. 学习资源

### 官方文档

- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [MDN Web Docs](https://developer.mozilla.org/)
- [Jest 官方文档](https://jestjs.io/)

### 教程和文章

- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/)
- [JavaScript.info](https://javascript.info/)
- [Web.dev](https://web.dev/)

### 开源项目

- [SortableJS](https://github.com/SortableJS/Sortable)
- [react-beautiful-dnd](https://github.com/atlassian/react-beautiful-dnd)
- [dragula](https://github.com/bevacqua/dragula)

## 11. 贡献指南

### 如何贡献

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### 代码审查

- 确保代码符合编码规范
- 添加必要的测试
- 更新相关文档
- 确保所有测试通过

### 问题反馈

- 使用 GitHub Issues 报告问题
- 提供详细的问题描述
- 包含复现步骤和环境信息
