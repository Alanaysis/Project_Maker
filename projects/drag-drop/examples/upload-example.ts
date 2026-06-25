/**
 * 文件上传示例
 *
 * 演示如何使用 FileUpload 类实现文件拖拽上传功能
 *
 * 运行方式：
 * npx ts-node examples/upload-example.ts
 */

import { FileUpload, UploadResult, UploadError, formatFileSize } from '../src';

/**
 * 基础上传示例
 */
export function basicUploadExample(): void {
  console.log('=== 基础上传示例 ===\n');

  // 创建上传区域
  const dropZone = document.createElement('div');
  dropZone.id = 'upload-zone';
  dropZone.style.cssText = `
    width: 400px;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #ccc;
    border-radius: 8px;
    background: #fafafa;
    cursor: pointer;
    transition: all 0.3s ease;
  `;

  const dropText = document.createElement('div');
  dropText.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 48px; margin-bottom: 10px;">📁</div>
      <div style="font-size: 16px; color: #666;">
        拖拽文件到此处或点击选择
      </div>
      <div style="font-size: 12px; color: #999; margin-top: 5px;">
        支持图片、文档等文件
      </div>
    </div>
  `;
  dropZone.appendChild(dropText);

  // 创建上传器
  const uploader = new FileUpload({
    dropZone,
    accept: ['image/*', '.pdf', '.doc', '.docx'],
    maxSize: 10 * 1024 * 1024, // 10MB
    maxFiles: 5,
    multiple: true,
    activeClass: 'drag-active',
    onFileAdd: (file) => {
      console.log(`添加文件: ${file.name} (${formatFileSize(file.size)})`);
    },
    onFileRemove: (file) => {
      console.log(`移除文件: ${file.name}`);
    },
    onComplete: (result: UploadResult) => {
      console.log(`处理完成:`);
      console.log(`  成功: ${result.success.length} 个文件`);
      console.log(`  失败: ${result.failed.length} 个文件`);
      console.log(`  耗时: ${result.duration}ms`);
    },
    onError: (error: UploadError) => {
      console.error(`上传错误: ${error.message}`);
    },
  });

  console.log('创建上传区域');
  console.log('支持的文件类型: image/*, .pdf, .doc, .docx');
  console.log('最大文件大小: 10MB');
  console.log('最大文件数量: 5');
}

/**
 * 带预览的上传示例
 */
export function previewUploadExample(): void {
  console.log('\n=== 带预览的上传示例 ===\n');

  // 创建上传区域
  const dropZone = document.createElement('div');
  dropZone.id = 'preview-upload-zone';
  dropZone.style.cssText = `
    width: 400px;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #0078d7;
    border-radius: 8px;
    background: #f0f8ff;
    cursor: pointer;
  `;

  const dropText = document.createElement('div');
  dropText.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 36px; margin-bottom: 8px;">🖼</div>
      <div style="font-size: 14px; color: #0078d7;">
        拖拽图片到此处
      </div>
    </div>
  `;
  dropZone.appendChild(dropText);

  // 创建预览容器
  const previewContainer = document.createElement('div');
  previewContainer.id = 'preview-container';
  previewContainer.style.cssText = `
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 15px;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 8px;
  `;

  // 创建上传器
  const uploader = new FileUpload({
    dropZone,
    accept: ['image/*'],
    maxSize: 5 * 1024 * 1024, // 5MB
    maxFiles: 10,
    multiple: true,
    autoPreview: true,
    previewContainer,
    onFileAdd: (file) => {
      console.log(`添加图片: ${file.name}`);
    },
    onComplete: (result) => {
      console.log(`处理完成: ${result.success.length} 张图片`);
    },
  });

  console.log('创建带预览的上传区域');
  console.log('支持的文件类型: image/*');
  console.log('最大文件大小: 5MB');
  console.log('最大文件数量: 10');
  console.log('自动预览: 启用');
}

/**
 * 自定义验证上传示例
 */
export function customValidationUploadExample(): void {
  console.log('\n=== 自定义验证上传示例 ===\n');

  // 创建上传区域
  const dropZone = document.createElement('div');
  dropZone.id = 'validation-upload-zone';
  dropZone.style.cssText = `
    width: 400px;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #28a745;
    border-radius: 8px;
    background: #f0fff0;
    cursor: pointer;
  `;

  const dropText = document.createElement('div');
  dropText.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 36px; margin-bottom: 8px;">📄</div>
      <div style="font-size: 14px; color: #28a745;">
        拖拽文档到此处
      </div>
      <div style="font-size: 12px; color: #666; margin-top: 5px;">
        仅支持 PDF 和 Word 文档
      </div>
    </div>
  `;
  dropZone.appendChild(dropText);

  // 创建上传器
  const uploader = new FileUpload({
    dropZone,
    accept: ['.pdf', '.doc', '.docx'],
    maxSize: 20 * 1024 * 1024, // 20MB
    maxFiles: 3,
    multiple: true,
    onValidate: (file) => {
      // 自定义验证：检查文件名
      const invalidChars = /[<>:"/\\|?*]/;
      if (invalidChars.test(file.name)) {
        return '文件名包含无效字符';
      }

      // 检查文件名长度
      if (file.name.length > 100) {
        return '文件名过长';
      }

      return true;
    },
    onFileAdd: (file) => {
      console.log(`添加文档: ${file.name}`);
    },
    onComplete: (result) => {
      if (result.failed.length > 0) {
        console.log('验证失败的文件:');
        result.failed.forEach((error) => {
          console.log(`  - ${error.file.name}: ${error.message}`);
        });
      }
    },
  });

  console.log('创建带自定义验证的上传区域');
  console.log('支持的文件类型: .pdf, .doc, .docx');
  console.log('最大文件大小: 20MB');
  console.log('最大文件数量: 3');
  console.log('自定义验证: 检查文件名');
}

/**
 * 单文件上传示例
 */
export function singleFileUploadExample(): void {
  console.log('\n=== 单文件上传示例 ===\n');

  // 创建上传区域
  const dropZone = document.createElement('div');
  dropZone.id = 'single-upload-zone';
  dropZone.style.cssText = `
    width: 400px;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #ffc107;
    border-radius: 8px;
    background: #fffdf0;
    cursor: pointer;
  `;

  const dropText = document.createElement('div');
  dropText.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 36px; margin-bottom: 8px;">📎</div>
      <div style="font-size: 14px; color: #856404;">
        拖拽文件到此处
      </div>
      <div style="font-size: 12px; color: #666; margin-top: 5px;">
        仅支持单个文件
      </div>
    </div>
  `;
  dropZone.appendChild(dropText);

  // 创建上传器
  const uploader = new FileUpload({
    dropZone,
    accept: ['image/*', '.pdf'],
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
    onFileAdd: (file) => {
      console.log(`添加文件: ${file.name}`);
      console.log('已达到文件数量限制，无法添加更多文件');
    },
    onFileRemove: (file) => {
      console.log(`移除文件: ${file.name}`);
    },
  });

  console.log('创建单文件上传区域');
  console.log('支持的文件类型: image/*, .pdf');
  console.log('最大文件大小: 10MB');
  console.log('单文件模式');
}

/**
 * 运行所有示例
 */
export function runUploadExamples(): void {
  console.log('文件上传示例\n');
  console.log('=' .repeat(50));

  basicUploadExample();
  previewUploadExample();
  customValidationUploadExample();
  singleFileUploadExample();

  console.log('\n' + '=' .repeat(50));
  console.log('所有上传示例运行完成');
}

// 如果直接运行此文件
if (typeof window === 'undefined') {
  runUploadExamples();
}
