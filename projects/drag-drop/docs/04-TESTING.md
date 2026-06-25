# 测试策略文档

## 1. 测试概述

### 测试目标

- 验证拖拽系统的核心功能
- 确保代码质量和稳定性
- 发现和修复潜在的 Bug
- 提供回归测试保障

### 测试类型

| 测试类型 | 目的 | 覆盖范围 |
|----------|------|----------|
| 单元测试 | 测试独立函数和类 | 工具函数、核心类 |
| 集成测试 | 测试模块间协作 | 拖拽排序、文件上传 |
| 边界测试 | 测试边界情况 | 异常输入、极限情况 |
| 性能测试 | 测试性能表现 | 大量元素、频繁操作 |

## 2. 测试环境

### 测试框架

- **Jest**: 主要测试框架
- **ts-jest**: TypeScript 支持
- **jsdom**: DOM 环境模拟

### 配置文件

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov'],
  verbose: true,
};
```

## 3. 单元测试

### 工具函数测试

#### 测试文件：`tests/utils.test.ts`

**测试用例**：

1. **getDistance**
   - 计算两点之间的距离
   - 处理相同点
   - 处理负坐标

2. **isPointInRect**
   - 点在矩形内
   - 点在矩形边上
   - 点在矩形外

3. **generateId**
   - 生成默认前缀的 ID
   - 生成自定义前缀的 ID
   - 生成唯一 ID

4. **throttle**
   - 限制函数调用频率
   - 延迟后再次调用

5. **debounce**
   - 延迟函数执行
   - 重置计时器

6. **validateFileType**
   - 接受空数组
   - 接受匹配的 MIME 类型
   - 拒绝不匹配的 MIME 类型
   - 接受通配符 MIME 类型
   - 接受匹配的扩展名
   - 拒绝不匹配的扩展名

7. **validateFileSize**
   - 接受文件大小在限制内
   - 拒绝文件大小超过限制
   - 接受文件大小等于限制

8. **formatFileSize**
   - 格式化字节
   - 格式化 KB
   - 格式化 MB
   - 格式化 GB
   - 处理 0 字节

9. **EventBus**
   - 发送和接收事件
   - 支持多个监听器
   - 移除监听器
   - 不同事件不触发
   - 清空所有监听器

### 拖拽管理器测试

#### 测试文件：`tests/drag-manager.test.ts`

**测试用例**：

1. **getState**
   - 初始状态为 IDLE

2. **getCurrentElement**
   - 初始为 null

3. **makeDraggable**
   - 返回移除函数
   - 添加事件监听器
   - 移除事件监听器

4. **registerDropTarget**
   - 返回移除函数
   - 允许取消注册

5. **on/off**
   - 订阅事件
   - 取消订阅

6. **destroy**
   - 清理资源
   - 重置状态

### 拖拽排序测试

#### 测试文件：`tests/sortable.test.ts`

**测试用例**：

1. **constructor**
   - 创建排序实例

2. **getItems**
   - 返回所有排序项
   - 空容器返回空数组

3. **getIndex**
   - 返回正确的索引
   - 不存在的元素返回 -1

4. **refreshItems**
   - 更新排序项列表

5. **disable/enable**
   - 禁用排序
   - 启用排序

6. **destroy**
   - 清理资源
   - 允许多次调用

7. **options**
   - 支持动画选项
   - 支持占位符选项
   - 支持手柄选项
   - 支持方向选项
   - 支持禁用选项

8. **callbacks**
   - 排序结束回调
   - 排序变化回调

### 文件上传测试

#### 测试文件：`tests/file-upload.test.ts`

**测试用例**：

1. **constructor**
   - 创建上传实例
   - 接受配置选项

2. **getFiles**
   - 初始返回空数组

3. **getFileCount**
   - 初始返回 0

4. **removeFile**
   - 移除文件

5. **clearFiles**
   - 清空所有文件

6. **destroy**
   - 清理资源
   - 允许多次调用

7. **validation**
   - 接受有效的文件类型
   - 拒绝无效的文件类型
   - 拒绝超过大小限制的文件
   - 拒绝超过数量限制的文件

8. **options**
   - 支持 activeClass 选项
   - 支持 autoPreview 选项
   - 支持 previewContainer 选项
   - 支持 onValidate 选项

9. **callbacks**
   - 文件添加回调
   - 文件移除回调
   - 完成回调

## 4. 集成测试

### 拖拽排序集成测试

```typescript
describe('Sortable Integration', () => {
  it('should sort items when dragged', () => {
    const container = document.createElement('div');
    const items = ['A', 'B', 'C', 'D', 'E'];

    items.forEach(text => {
      const item = document.createElement('div');
      item.textContent = text;
      container.appendChild(item);
    });

    const sortable = new Sortable({
      container,
      itemSelector: 'div',
      onSortEnd: (data) => {
        expect(data.oldIndex).toBe(0);
        expect(data.newIndex).toBe(2);
      },
    });

    // 模拟拖拽操作
    // ...
  });
});
```

### 文件上传集成测试

```typescript
describe('FileUpload Integration', () => {
  it('should handle multiple files', () => {
    const dropZone = document.createElement('div');
    const onFileAdd = jest.fn();

    const uploader = new FileUpload({
      dropZone,
      multiple: true,
      onFileAdd,
    });

    // 模拟文件拖拽
    const files = [
      new File([''], 'file1.png', { type: 'image/png' }),
      new File([''], 'file2.png', { type: 'image/png' }),
    ];

    // 创建拖拽事件
    const dropEvent = new Event('drop') as any;
    dropEvent.dataTransfer = { files };
    dropEvent.preventDefault = jest.fn();
    dropEvent.stopPropagation = jest.fn();

    dropZone.dispatchEvent(dropEvent);

    expect(onFileAdd).toHaveBeenCalledTimes(2);
  });
});
```

## 5. 边界测试

### 空容器测试

```typescript
describe('Empty Container', () => {
  it('should handle empty container', () => {
    const container = document.createElement('div');
    const sortable = new Sortable({
      container,
      itemSelector: '.item',
    });

    expect(sortable.getItems().length).toBe(0);
  });
});
```

### 大量元素测试

```typescript
describe('Large Number of Items', () => {
  it('should handle 1000 items', () => {
    const container = document.createElement('div');

    for (let i = 0; i < 1000; i++) {
      const item = document.createElement('div');
      item.className = 'item';
      container.appendChild(item);
    }

    const sortable = new Sortable({
      container,
      itemSelector: '.item',
    });

    expect(sortable.getItems().length).toBe(1000);
  });
});
```

### 异常输入测试

```typescript
describe('Invalid Input', () => {
  it('should handle invalid file type', () => {
    const dropZone = document.createElement('div');
    const onError = jest.fn();

    const uploader = new FileUpload({
      dropZone,
      accept: ['image/*'],
      onError,
    });

    const file = new File([''], 'test.pdf', { type: 'application/pdf' });
    // 验证文件被拒绝
  });
});
```

## 6. 性能测试

### 拖拽性能测试

```typescript
describe('Drag Performance', () => {
  it('should handle rapid mouse movements', () => {
    const manager = new DragManager();
    const element = document.createElement('div');

    manager.makeDraggable(element);

    const startTime = performance.now();

    // 模拟快速鼠标移动
    for (let i = 0; i < 1000; i++) {
      // 模拟 mousemove 事件
    }

    const endTime = performance.now();
    const duration = endTime - startTime;

    // 验证性能在可接受范围内
    expect(duration).toBeLessThan(100); // 100ms
  });
});
```

### 排序性能测试

```typescript
describe('Sort Performance', () => {
  it('should sort 1000 items within 1 second', () => {
    const container = document.createElement('div');

    for (let i = 0; i < 1000; i++) {
      const item = document.createElement('div');
      item.className = 'item';
      container.appendChild(item);
    }

    const startTime = performance.now();

    const sortable = new Sortable({
      container,
      itemSelector: '.item',
    });

    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(1000);
  });
});
```

## 7. 测试覆盖率

### 覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| utils.ts | 90%+ |
| drag-manager.ts | 85%+ |
| sortable.ts | 85%+ |
| file-upload.ts | 85%+ |

### 生成覆盖率报告

```bash
npm run test:coverage
```

### 覆盖率报告示例

```
-------------------|---------|----------|---------|---------|
File               | % Stmts | % Branch | % Funcs | % Lines |
-------------------|---------|----------|---------|---------|
All files          |   87.5  |   80.0   |   90.0  |   87.5  |
 utils.ts          |   92.0  |   85.0   |   95.0  |   92.0  |
 drag-manager.ts   |   85.0  |   75.0   |   88.0  |   85.0  |
 sortable.ts       |   86.0  |   78.0   |   87.0  |   86.0  |
 file-upload.ts    |   84.0  |   76.0   |   86.0  |   84.0  |
-------------------|---------|----------|---------|---------|
```

## 8. 测试最佳实践

### 测试命名规范

```typescript
// 好的命名
describe('DragManager', () => {
  it('should start in IDLE state', () => {});
  it('should make element draggable', () => {});
  it('should return remove function', () => {});
});

// 不好的命名
describe('DragManager', () => {
  it('test1', () => {});
  it('test2', () => {});
});
```

### 测试结构

```typescript
describe('Module', () => {
  describe('method', () => {
    it('should do something when condition', () => {
      // Arrange - 准备
      const input = 'test';

      // Act - 执行
      const result = doSomething(input);

      // Assert - 断言
      expect(result).toBe('expected');
    });
  });
});
```

### Mock 使用

```typescript
// Mock DOM 元素
const createMockElement = (id: string): HTMLElement => {
  const element = document.createElement('div');
  element.id = id;
  element.getBoundingClientRect = jest.fn(() => ({
    x: 0,
    y: 0,
    width: 100,
    height: 50,
    top: 0,
    right: 100,
    bottom: 50,
    left: 0,
  }));
  return element;
};

// Mock 事件
const createMockEvent = (type: string): Event => {
  const event = new Event(type);
  event.preventDefault = jest.fn();
  event.stopPropagation = jest.fn();
  return event;
};
```

## 9. 持续集成

### CI 配置示例

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'

      - name: Install dependencies
        run: npm install

      - name: Run tests
        run: npm test

      - name: Run coverage
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 10. 测试维护

### 测试更新流程

1. 代码变更时更新测试
2. 添加新功能时添加测试
3. 修复 Bug 时添加回归测试
4. 定期审查和清理测试

### 测试文档

- 每个测试文件添加注释说明
- 复杂测试用例添加详细说明
- 记录测试的目的和预期行为
