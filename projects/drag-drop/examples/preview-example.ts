/**
 * 拖拽预览示例
 *
 * 演示如何创建和自定义拖拽预览效果
 *
 * 运行方式：
 * npx ts-node examples/preview-example.ts
 */

import { DragManager, DragEventData, setStyles, addClass, removeClass } from '../src';

/**
 * 基础预览示例
 */
export function basicPreviewExample(): void {
  console.log('=== 基础预览示例 ===\n');

  const manager = new DragManager();

  // 创建可拖拽元素
  const element = document.createElement('div');
  element.id = 'basic-drag';
  element.textContent = '拖拽我';
  element.style.cssText = `
    width: 100px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0078d7;
    color: white;
    border-radius: 4px;
    cursor: grab;
    user-select: none;
  `;

  // 使元素可拖拽
  manager.makeDraggable(element, {
    enablePreview: true,
    onDragStart: (e: DragEventData) => {
      console.log('拖拽开始');
      // 添加拖拽状态样式
      addClass(e.element, 'dragging');
    },
    onDragEnd: (e: DragEventData) => {
      console.log('拖拽结束');
      removeClass(e.element, 'dragging');
    },
  });

  console.log('创建基础拖拽预览');
  console.log('预览元素是原始元素的克隆');
}

/**
 * 自定义预览示例
 */
export function customPreviewExample(): void {
  console.log('\n=== 自定义预览示例 ===\n');

  const manager = new DragManager();

  // 创建卡片元素
  const card = document.createElement('div');
  card.className = 'card';
  card.style.cssText = `
    width: 200px;
    padding: 16px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  `;

  const title = document.createElement('h3');
  title.textContent = '自定义预览';
  title.style.cssText = `
    margin: 0 0 8px 0;
    font-size: 16px;
  `;

  const content = document.createElement('p');
  content.textContent = '这是一个自定义预览示例';
  content.style.cssText = `
    margin: 0;
    color: #666;
    font-size: 14px;
  `;

  card.appendChild(title);
  card.appendChild(content);

  // 使卡片可拖拽，使用自定义预览
  manager.makeDraggable(card, {
    enablePreview: true,
    createPreview: (element) => {
      // 创建自定义预览
      const preview = document.createElement('div');
      preview.className = 'custom-preview';
      preview.style.cssText = `
        width: 180px;
        padding: 12px;
        background: linear-gradient(135deg, #0078d7, #00b4d8);
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,120,215,0.4);
        transform: rotate(-5deg);
        opacity: 0.9;
      `;

      const previewTitle = document.createElement('div');
      previewTitle.textContent = '✨ 自定义预览';
      previewTitle.style.cssText = `
        font-weight: bold;
        margin-bottom: 4px;
      `;

      const previewContent = document.createElement('div');
      previewContent.textContent = '拖拽中...';
      previewContent.style.cssText = `
        font-size: 12px;
        opacity: 0.8;
      `;

      preview.appendChild(previewTitle);
      preview.appendChild(previewContent);

      return preview;
    },
    onDragStart: () => {
      console.log('开始拖拽卡片');
    },
    onDragEnd: () => {
      console.log('结束拖拽卡片');
    },
  });

  console.log('创建自定义预览');
  console.log('预览元素使用渐变背景和旋转效果');
}

/**
 * 图片预览示例
 */
export function imagePreviewExample(): void {
  console.log('\n=== 图片预览示例 ===\n');

  const manager = new DragManager();

  // 创建图片元素
  const imageContainer = document.createElement('div');
  imageContainer.style.cssText = `
    width: 150px;
    height: 150px;
    border-radius: 8px;
    overflow: hidden;
    cursor: grab;
    user-select: none;
  `;

  // 创建图片（使用渐变代替真实图片）
  const image = document.createElement('div');
  image.style.cssText = `
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, #ff6b6b, #ffa07a);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 24px;
  `;
  image.textContent = '🖼';

  imageContainer.appendChild(image);

  // 使图片可拖拽，使用自定义预览
  manager.makeDraggable(imageContainer, {
    enablePreview: true,
    createPreview: (element) => {
      // 创建图片预览
      const preview = document.createElement('div');
      preview.style.cssText = `
        width: 120px;
        height: 120px;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        transform: scale(1.1);
        opacity: 0.9;
      `;

      const previewImage = document.createElement('div');
      previewImage.style.cssText = `
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, #ff6b6b, #ffa07a);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 32px;
      `;
      previewImage.textContent = '🖼';

      preview.appendChild(previewImage);

      return preview;
    },
    onDragStart: () => {
      console.log('开始拖拽图片');
    },
    onDragEnd: () => {
      console.log('结束拖拽图片');
    },
  });

  console.log('创建图片预览');
  console.log('预览元素有圆角和阴影效果');
}

/**
 * 列表项预览示例
 */
export function listItemPreviewExample(): void {
  console.log('\n=== 列表项预览示例 ===\n');

  const manager = new DragManager();

  // 创建列表
  const list = document.createElement('div');
  list.style.cssText = `
    width: 300px;
    background: #f5f5f5;
    border-radius: 8px;
    padding: 10px;
  `;

  const items = ['任务 1', '任务 2', '任务 3'];

  items.forEach((text, index) => {
    const item = document.createElement('div');
    item.className = 'list-item';
    item.style.cssText = `
      display: flex;
      align-items: center;
      padding: 12px;
      margin: 6px 0;
      background: white;
      border: 1px solid #ddd;
      border-radius: 4px;
      cursor: grab;
      user-select: none;
    `;

    const handle = document.createElement('div');
    handle.textContent = '☰';
    handle.style.cssText = `
      margin-right: 12px;
      color: #999;
    `;

    const textEl = document.createElement('span');
    textEl.textContent = text;
    textEl.style.cssText = `flex: 1;`;

    item.appendChild(handle);
    item.appendChild(textEl);
    list.appendChild(item);

    // 使列表项可拖拽，使用自定义预览
    manager.makeDraggable(item, {
      handle: '.list-item',
      enablePreview: true,
      createPreview: (element) => {
        // 创建简洁的预览
        const preview = document.createElement('div');
        preview.style.cssText = `
          padding: 8px 16px;
          background: #0078d7;
          color: white;
          border-radius: 20px;
          font-size: 14px;
          white-space: nowrap;
          box-shadow: 0 2px 8px rgba(0,120,215,0.3);
        `;
        preview.textContent = text;
        return preview;
      },
      onDragStart: () => {
        console.log(`开始拖拽: ${text}`);
      },
      onDragEnd: () => {
        console.log(`结束拖拽: ${text}`);
      },
    });
  });

  console.log('创建列表项预览');
  console.log('预览元素是圆角胶囊形状');
}

/**
 * 拖放目标示例
 */
export function dropTargetExample(): void {
  console.log('\n=== 拖放目标示例 ===\n');

  const manager = new DragManager();

  // 创建可拖拽元素
  const draggable = document.createElement('div');
  draggable.textContent = '拖拽我到目标区域';
  draggable.style.cssText = `
    width: 150px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0078d7;
    color: white;
    border-radius: 4px;
    cursor: grab;
    user-select: none;
  `;

  // 创建拖放目标
  const dropTarget = document.createElement('div');
  dropTarget.id = 'drop-target';
  dropTarget.style.cssText = `
    width: 200px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #ccc;
    border-radius: 8px;
    background: #fafafa;
    margin-top: 20px;
    transition: all 0.3s ease;
  `;
  dropTarget.textContent = '放置区域';

  // 使元素可拖拽
  manager.makeDraggable(draggable, {
    enablePreview: true,
  });

  // 注册拖放目标
  manager.registerDropTarget(dropTarget, {
    activeClass: 'drag-over',
    onDragEnter: (e) => {
      console.log('进入目标区域');
      setStyles(dropTarget, {
        borderColor: '#0078d7',
        backgroundColor: '#f0f8ff',
      });
    },
    onDragLeave: (e) => {
      console.log('离开目标区域');
      setStyles(dropTarget, {
        borderColor: '#ccc',
        backgroundColor: '#fafafa',
      });
    },
    onDrop: (e) => {
      console.log('放置在目标区域');
      setStyles(dropTarget, {
        borderColor: '#28a745',
        backgroundColor: '#f0fff0',
      });
      dropTarget.textContent = '已放置!';
    },
  });

  console.log('创建拖放目标示例');
  console.log('拖拽元素到目标区域会触发事件');
}

/**
 * 运行所有示例
 */
export function runPreviewExamples(): void {
  console.log('拖拽预览示例\n');
  console.log('=' .repeat(50));

  basicPreviewExample();
  customPreviewExample();
  imagePreviewExample();
  listItemPreviewExample();
  dropTargetExample();

  console.log('\n' + '=' .repeat(50));
  console.log('所有预览示例运行完成');
}

// 如果直接运行此文件
if (typeof window === 'undefined') {
  runPreviewExamples();
}
