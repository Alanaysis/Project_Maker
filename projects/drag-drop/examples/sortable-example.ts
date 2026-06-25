/**
 * 拖拽排序示例
 *
 * 演示如何使用 Sortable 类实现拖拽排序功能
 *
 * 运行方式：
 * npx ts-node examples/sortable-example.ts
 */

import { Sortable, SortEventData } from '../src';

/**
 * 基础排序示例
 */
export function basicSortableExample(): void {
  console.log('=== 基础排序示例 ===\n');

  // 创建容器
  const container = document.createElement('div');
  container.id = 'sortable-list';
  container.style.cssText = `
    width: 300px;
    padding: 20px;
    background: #f5f5f5;
    border-radius: 8px;
  `;

  // 创建排序项
  const items = ['项目 A', '项目 B', '项目 C', '项目 D', '项目 E'];

  items.forEach((text, index) => {
    const item = document.createElement('div');
    item.className = 'sortable-item';
    item.textContent = text;
    item.dataset.index = String(index);
    item.style.cssText = `
      padding: 12px 16px;
      margin: 8px 0;
      background: white;
      border: 1px solid #ddd;
      border-radius: 4px;
      cursor: grab;
      user-select: none;
      transition: transform 0.15s ease;
    `;

    // 鼠标悬停效果
    item.addEventListener('mouseenter', () => {
      item.style.borderColor = '#0078d7';
    });
    item.addEventListener('mouseleave', () => {
      item.style.borderColor = '#ddd';
    });

    container.appendChild(item);
  });

  // 创建排序器
  const sortable = new Sortable({
    container,
    itemSelector: '.sortable-item',
    animation: 150,
    placeholderClass: 'sortable-placeholder',
    onSortEnd: (data: SortEventData) => {
      console.log(`排序完成: ${data.oldIndex} -> ${data.newIndex}`);
    },
    onSortChange: (data: SortEventData) => {
      console.log(`排序变化: ${data.oldIndex} -> ${data.newIndex}`);
    },
  });

  console.log('创建排序列表，包含 5 个项目');
  console.log('拖拽项目可以重新排序');
  console.log('当前项目:', sortable.getItems().map((item) => item.textContent));

  // 模拟排序
  console.log('\n模拟排序操作...');
  const items2 = sortable.getItems();
  console.log('排序前:', items2.map((item) => item.textContent));
}

/**
 * 带动画的排序示例
 */
export function animatedSortableExample(): void {
  console.log('\n=== 带动画的排序示例 ===\n');

  const container = document.createElement('div');
  container.id = 'animated-list';
  container.style.cssText = `
    width: 300px;
    padding: 20px;
    background: #f0f8ff;
    border-radius: 8px;
  `;

  const colors = ['#ff6b6b', '#ffa07a', '#98fb98', '#87ceeb', '#dda0dd'];

  colors.forEach((color, index) => {
    const item = document.createElement('div');
    item.className = 'color-item';
    item.style.cssText = `
      padding: 16px;
      margin: 8px 0;
      background: ${color};
      border-radius: 4px;
      cursor: grab;
      user-select: none;
      text-align: center;
      font-weight: bold;
      color: white;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    `;
    item.textContent = `颜色 ${index + 1}`;
    container.appendChild(item);
  });

  const sortable = new Sortable({
    container,
    itemSelector: '.color-item',
    animation: 300,
    placeholder: (() => {
      const ph = document.createElement('div');
      ph.style.cssText = `
        padding: 16px;
        margin: 8px 0;
        background: rgba(0,0,0,0.1);
        border: 2px dashed rgba(0,0,0,0.2);
        border-radius: 4px;
      `;
      return ph;
    })(),
    onSortEnd: (data) => {
      console.log(`颜色排序完成: ${data.oldIndex} -> ${data.newIndex}`);
    },
  });

  console.log('创建带动画的排序列表');
  console.log('动画持续时间: 300ms');
}

/**
 * 水平排序示例
 */
export function horizontalSortableExample(): void {
  console.log('\n=== 水平排序示例 ===\n');

  const container = document.createElement('div');
  container.id = 'horizontal-list';
  container.style.cssText = `
    display: flex;
    gap: 10px;
    padding: 20px;
    background: #fff5f5;
    border-radius: 8px;
  `;

  const tags = ['TypeScript', 'JavaScript', 'React', 'Vue', 'Angular'];

  tags.forEach((tag) => {
    const item = document.createElement('div');
    item.className = 'tag-item';
    item.textContent = tag;
    item.style.cssText = `
      padding: 8px 16px;
      background: #0078d7;
      color: white;
      border-radius: 20px;
      cursor: grab;
      user-select: none;
      white-space: nowrap;
    `;
    container.appendChild(item);
  });

  const sortable = new Sortable({
    container,
    itemSelector: '.tag-item',
    direction: 'horizontal',
    animation: 200,
    onSortEnd: (data) => {
      console.log(`标签排序完成: ${data.oldIndex} -> ${data.newIndex}`);
    },
  });

  console.log('创建水平排序列表');
  console.log('标签:', tags);
}

/**
 * 带拖拽手柄的排序示例
 */
export function handleSortableExample(): void {
  console.log('\n=== 带拖拽手柄的排序示例 ===\n');

  const container = document.createElement('div');
  container.id = 'handle-list';
  container.style.cssText = `
    width: 300px;
    padding: 20px;
    background: #f0fff0;
    border-radius: 8px;
  `;

  const tasks = [
    '学习 TypeScript',
    '实现拖拽排序',
    '编写单元测试',
    '优化性能',
    '编写文档',
  ];

  tasks.forEach((task, index) => {
    const item = document.createElement('div');
    item.className = 'task-item';
    item.style.cssText = `
      display: flex;
      align-items: center;
      padding: 12px;
      margin: 8px 0;
      background: white;
      border: 1px solid #ddd;
      border-radius: 4px;
      user-select: none;
    `;

    // 拖拽手柄
    const handle = document.createElement('div');
    handle.className = 'drag-handle';
    handle.textContent = '☰';
    handle.style.cssText = `
      cursor: grab;
      padding: 4px 8px;
      margin-right: 12px;
      color: #666;
    `;

    // 任务文本
    const text = document.createElement('span');
    text.textContent = task;
    text.style.cssText = `flex: 1;`;

    item.appendChild(handle);
    item.appendChild(text);
    container.appendChild(item);
  });

  const sortable = new Sortable({
    container,
    itemSelector: '.task-item',
    handle: '.drag-handle',
    animation: 150,
    onSortEnd: (data) => {
      console.log(`任务排序完成: ${data.oldIndex} -> ${data.newIndex}`);
    },
  });

  console.log('创建带拖拽手柄的排序列表');
  console.log('只有拖拽手柄可以触发排序');
}

/**
 * 运行所有示例
 */
export function runSortableExamples(): void {
  console.log('拖拽排序示例\n');
  console.log('=' .repeat(50));

  basicSortableExample();
  animatedSortableExample();
  horizontalSortableExample();
  handleSortableExample();

  console.log('\n' + '=' .repeat(50));
  console.log('所有排序示例运行完成');
}

// 如果直接运行此文件
if (typeof window === 'undefined') {
  runSortableExamples();
}
