# 05 - 开发指南

## 环境准备

### 1. 系统要求

- **Node.js**: >= 14.0.0
- **npm**: >= 6.0.0
- **TypeScript**: >= 4.5.0

### 2. 安装依赖

```bash
cd projects/virtual-scroll
npm install
```

### 3. 项目结构

```
virtual-scroll/
├── src/                    # 源代码
│   ├── index.ts           # 入口文件
│   ├── types.ts           # 类型定义
│   ├── virtual-scroll.ts  # 核心类
│   ├── height-manager.ts  # 高度管理器
│   └── dom-adapter.ts     # DOM 适配器
├── tests/                  # 测试文件
│   ├── height-manager.test.ts
│   └── virtual-scroll.test.ts
├── examples/               # 示例代码
│   ├── simple-list.ts
│   ├── dynamic-height.ts
│   ├── performance-test.ts
│   └── browser-demo.html
├── docs/                   # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── package.json
├── tsconfig.json
├── jest.config.js
└── README.md
```

## 开发流程

### 1. 本地开发

**启动开发模式**：
```bash
# 监听文件变化并自动编译
npm run build -- --watch
```

**运行测试**：
```bash
# 运行所有测试
npm test

# 监听模式
npm test -- --watch

# 生成覆盖率报告
npm test -- --coverage
```

**运行示例**：
```bash
# 简单列表示例
npm run example:simple

# 动态高度示例
npm run example:dynamic

# 性能测试示例
npm run example:performance
```

### 2. 代码规范

**TypeScript 配置**：
- 严格模式启用
- 所有函数必须有类型注解
- 使用接口定义复杂类型

**命名规范**：
- 类名：PascalCase（如 `VirtualScroll`）
- 方法名：camelCase（如 `handleScroll`）
- 常量：UPPER_SNAKE_CASE（如 `DEFAULT_OPTIONS`）
- 接口名：PascalCase（如 `VirtualScrollOptions`）

**注释规范**：
```typescript
/**
 * 处理滚动事件
 * @param scrollTop 滚动位置（像素）
 * @param scrollLeft 水平滚动位置（可选）
 * @returns void
 */
handleScroll(scrollTop: number, scrollLeft: number = 0): void {
  // 实现
}
```

### 3. Git 工作流

**分支策略**：
- `main`: 生产分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支

**提交规范**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**：
```
feat(scroll): add dynamic height support

- Implement height measurement using ResizeObserver
- Add height cache management
- Update visible range calculation

Closes #123
```

## 核心功能开发

### 1. 添加新功能

**步骤**：

1. **创建功能分支**
```bash
git checkout -b feature/new-feature
```

2. **实现功能**
```typescript
// src/new-feature.ts
export class NewFeature {
  // 实现
}
```

3. **编写测试**
```typescript
// tests/new-feature.test.ts
describe('NewFeature', () => {
  test('should work correctly', () => {
    // 测试
  });
});
```

4. **更新文档**
```markdown
<!-- docs/03-IMPLEMENTATION.md -->
### 新功能实现

...
```

5. **提交代码**
```bash
git add .
git commit -m "feat(feature): add new feature"
```

6. **创建 Pull Request**

### 2. 修复 Bug

**步骤**：

1. **重现 Bug**
```bash
# 运行测试重现问题
npm test -- --testPathPattern=buggy-test
```

2. **定位问题**
```typescript
// 添加调试日志
console.log('Debug:', variable);
```

3. **修复问题**
```typescript
// 修复代码
```

4. **编写回归测试**
```typescript
test('should fix bug #123', () => {
  // 确保 bug 不再复现
});
```

5. **提交修复**
```bash
git commit -m "fix(scroll): fix scroll position calculation"
```

### 3. 性能优化

**步骤**：

1. **性能分析**
```bash
# 运行性能测试
npm run example:performance
```

2. **识别瓶颈**
```typescript
// 使用 performance.mark
performance.mark('start');
// 代码
performance.mark('end');
performance.measure('operation', 'start', 'end');
```

3. **优化实现**
```typescript
// 优化前
for (let i = 0; i < n; i++) {
  // O(n) 操作
}

// 优化后
// 使用 O(log n) 算法
```

4. **验证优化**
```bash
# 重新运行性能测试
npm run example:performance
```

## API 文档

### 1. VirtualScroll 类

**构造函数**：
```typescript
new VirtualScroll(
  options?: Partial<VirtualScrollOptions>,
  events?: VirtualScrollEvents
)
```

**方法**：

| 方法 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| setDataSource | items: ItemConfig[] | void | 设置数据源 |
| handleScroll | scrollTop: number, scrollLeft?: number | void | 处理滚动事件 |
| scrollToIndex | index: number, align?: string | number | 滚动到指定位置 |
| getRenderItems | - | RenderItem[] | 获取渲染队列 |
| getVisibleRange | - | VisibleRange | 获取可视范围 |
| getScrollPosition | - | ScrollPosition | 获取滚动位置 |
| getTotalHeight | - | number | 获取总高度 |
| getMetrics | - | PerformanceMetrics | 获取性能指标 |
| updateItemHeight | index: number, height: number | void | 更新项目高度 |
| updateOptions | options: Partial<VirtualScrollOptions> | void | 更新配置 |
| destroy | - | void | 销毁实例 |

**属性**：

| 属性 | 类型 | 描述 |
|------|------|------|
| options | VirtualScrollOptions | 配置选项 |
| events | VirtualScrollEvents | 事件处理器 |

### 2. HeightManager 类

**构造函数**：
```typescript
new HeightManager(estimatedHeight?: number)
```

**方法**：

| 方法 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| setTotalCount | count: number | void | 设置列表总数 |
| getTotalCount | - | number | 获取列表总数 |
| setEstimatedHeight | height: number | void | 设置预估高度 |
| getEstimatedHeight | - | number | 获取预估高度 |
| updateItemHeight | index: number, height: number | void | 更新项目高度 |
| getItemHeight | index: number | number | 获取项目高度 |
| getItemOffset | index: number | number | 获取项目偏移量 |
| getTotalHeight | - | number | 获取总高度 |
| findStartIndex | scrollTop: number | number | 查找起始索引 |
| clearCache | - | void | 清除缓存 |
| getCacheSize | - | number | 获取缓存大小 |
| getCacheHitRate | - | number | 获取缓存命中率 |
| isValidIndex | index: number | boolean | 检查索引有效性 |

### 3. DOMAdapter 类

**构造函数**：
```typescript
new DOMAdapter(options: DOMAdapterOptions)
```

**方法**：

| 方法 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| setDataSource | items: ItemConfig[] | void | 设置数据源 |
| scrollToIndex | index: number, align?: string | void | 滚动到指定位置 |
| getVirtualScroll | - | VirtualScroll | 获取虚拟滚动实例 |
| getMetrics | - | PerformanceMetrics | 获取性能指标 |
| updateOptions | options: Partial<VirtualScrollOptions> | void | 更新配置 |
| destroy | - | void | 销毁实例 |

## 常见问题

### 1. 如何处理动态高度？

**问题**：列表项高度不一致，如何正确计算？

**解决方案**：
```typescript
const scroll = new VirtualScroll({
  containerHeight: 500,
  dynamicHeight: true,
  estimatedHeight: 60
});

// 在元素渲染后测量实际高度
scroll.on('itemRender', (index, item) => {
  requestAnimationFrame(() => {
    const element = document.querySelector(`[data-index="${index}"]`);
    if (element) {
      const height = element.offsetHeight;
      scroll.updateItemHeight(index, height);
    }
  });
});
```

### 2. 如何实现滚动到底部加载更多？

**问题**：当滚动到底部时，如何触发加载更多？

**解决方案**：
```typescript
const scroll = new VirtualScroll({
  containerHeight: 500,
  itemHeight: 50
}, {
  onScroll: (position) => {
    const totalHeight = scroll.getTotalHeight();
    const containerHeight = 500;
    const threshold = 100;

    if (position.scrollTop + containerHeight >= totalHeight - threshold) {
      loadMoreItems();
    }
  }
});
```

### 3. 如何保持滚动位置？

**问题**：页面切换后如何恢复滚动位置？

**解决方案**：
```typescript
// 保存滚动位置
const savedPosition = scroll.getScrollPosition().scrollTop;
localStorage.setItem('scrollPosition', savedPosition.toString());

// 恢复滚动位置
const savedPosition = localStorage.getItem('scrollPosition');
if (savedPosition) {
  scroll.handleScroll(parseInt(savedPosition));
}
```

### 4. 如何处理快速滚动？

**问题**：快速滚动时出现白屏或闪烁？

**解决方案**：
```typescript
const scroll = new VirtualScroll({
  containerHeight: 500,
  itemHeight: 50,
  bufferCount: 20, // 增加缓冲区
  throttleInterval: 16 // 使用 RAF 节流
});
```

### 5. 如何优化内存占用？

**问题**：大量数据导致内存占用过高？

**解决方案**：
```typescript
// 使用 LRU 缓存限制大小
const scroll = new VirtualScroll({
  containerHeight: 500,
  itemHeight: 50,
  maxCacheSize: 1000
});

// 定期清理缓存
setInterval(() => {
  scroll.clearCache();
}, 60000);
```

## 调试技巧

### 1. 开启调试模式

```typescript
const scroll = new VirtualScroll({
  containerHeight: 500,
  itemHeight: 50,
  debug: true
});
```

### 2. 查看性能指标

```typescript
const metrics = scroll.getMetrics();
console.log('Total items:', metrics.totalItems);
console.log('Rendered items:', metrics.renderedItems);
console.log('Cache hit rate:', metrics.cacheHitRate);
console.log('Average render time:', metrics.averageRenderTime);
```

### 3. 监控滚动事件

```typescript
const scroll = new VirtualScroll({
  containerHeight: 500,
  itemHeight: 50
}, {
  onScroll: (position) => {
    console.log('Scroll position:', position);
  },
  onVisibleChange: (range) => {
    console.log('Visible range:', range);
  }
});
```

### 4. 使用 Chrome DevTools

1. 打开 Chrome DevTools
2. 切换到 Performance 面板
3. 点击 Record 按钮
4. 执行滚动操作
5. 停止录制并分析性能

## 发布流程

### 1. 版本管理

**语义化版本**：
- `major`: 不兼容的 API 变更
- `minor`: 向后兼容的功能性新增
- `patch`: 向后兼容的问题修正

**更新版本**：
```bash
npm version patch  # 1.0.0 -> 1.0.1
npm version minor  # 1.0.0 -> 1.1.0
npm version major  # 1.0.0 -> 2.0.0
```

### 2. 构建和测试

```bash
# 运行测试
npm test

# 构建
npm run build

# 检查构建产物
ls dist/
```

### 3. 发布到 npm

```bash
# 登录 npm
npm login

# 发布
npm publish
```

### 4. 创建 GitHub Release

```bash
# 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签
git push origin v1.0.0
```

## 贡献指南

### 1. 如何贡献

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 2. 代码审查

**审查要点**：
- 代码风格是否符合规范
- 是否有足够的测试覆盖
- 性能是否有影响
- 文档是否更新

### 3. 问题报告

**报告内容**：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息

## 学习资源

### 1. 官方文档

- [TypeScript 文档](https://www.typescriptlang.org/)
- [Jest 文档](https://jestjs.io/)
- [Node.js 文档](https://nodejs.org/)

### 2. 相关文章

- [Virtual Scrolling: A Technique for Building Incredibly Fast Lists](https://blog.emberjs.com/virtual-scrolling-a-technique-for-building-incredibly/)
- [Understanding Virtual Scrolling](https://www.patterns.dev/posts/virtual-lists/)
- [Rendering a Million Rows with Virtual Scrolling](https://medium.com/@romanonthego/rendering-a-million-rows-with-virtual-scrolling-3e6b4b3b7a4c)

### 3. 开源项目

- [react-window](https://github.com/bvaughn/react-window)
- [react-virtualized](https://github.com/bvaughn/react-virtualized)
- [vue-virtual-scroller](https://github.com/Akryum/vue-virtual-scroller)
- [tanstack-virtual](https://tanstack.com/virtual)

## 总结

开发指南的关键点：

1. **环境准备**：确保 Node.js 和 npm 版本符合要求
2. **开发流程**：遵循 Git 工作流和代码规范
3. **功能开发**：按照步骤实现新功能和修复 Bug
4. **API 文档**：详细记录所有公共 API
5. **常见问题**：提供常见问题的解决方案
6. **调试技巧**：掌握性能分析和调试方法
7. **发布流程**：遵循语义化版本和发布规范

通过遵循这些开发指南，我们可以高效地开发和维护虚拟滚动组件。
