# 05 - 开发指南

## 环境准备

### 系统要求
- Node.js >= 16
- npm >= 8

### 安装依赖
```bash
cd projects/chart-library
npm install
```

## 开发流程

### 1. 启动开发服务器
```bash
npm run dev
```

### 2. 运行测试
```bash
npm test
```

### 3. 构建生产版本
```bash
npm run build
```

## 项目结构说明

```
src/
├── core/           # 核心功能模块
├── charts/         # 图表类型实现
├── utils/          # 工具函数
└── index.ts        # 入口文件

tests/              # 测试文件
examples/           # 使用示例
docs/               # 项目文档
```

## 编码规范

### TypeScript 配置
- 启用严格模式
- 使用 ES2020 目标
- 启用所有严格检查

### 代码风格
- 使用 2 空格缩进
- 使用单引号
- 每行不超过 100 字符

### 命名规范
- 类名: PascalCase
- 方法/变量: camelCase
- 常量: UPPER_SNAKE_CASE
- 文件名: camelCase.ts

## 调试技巧

### Canvas 调试
```typescript
// 开启调试模式
const chart = new LineChart(container, {
  debug: true,
  // 显示坐标轴、边界框等
});
```

### 性能分析
```typescript
console.time('render');
chart.render();
console.timeEnd('render');
```

## 常见问题

### Q: 图表在高清屏幕上模糊？
A: 确保正确处理 devicePixelRatio

### Q: 动画卡顿？
A: 使用 requestAnimationFrame，避免在渲染循环中创建对象

### Q: 交互事件不准确？
A: 检查坐标转换，考虑 Canvas 的 CSS 尺寸和实际尺寸差异
