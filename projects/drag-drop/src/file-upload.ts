/**
 * 文件拖拽上传模块
 *
 * 实现文件拖拽上传功能，支持：
 * - 文件拖拽上传
 * - 文件类型验证
 * - 文件大小限制
 * - 上传进度显示
 * - 文件预览
 */

import {
  FileUploadOptions,
  UploadProgress,
  UploadResult,
  UploadError,
  ErrorCode,
  RemoveEventListener,
} from './types';
import {
  validateFileType,
  validateFileSize,
  formatFileSize,
  createFilePreview,
  addClass,
  removeClass,
} from './utils';

/**
 * 文件拖拽上传器
 *
 * 使用示例：
 * ```typescript
 * const uploader = new FileUpload({
 *   dropZone: document.getElementById('drop-zone')!,
 *   accept: ['image/*', '.pdf'],
 *   maxSize: 10 * 1024 * 1024, // 10MB
 *   maxFiles: 5,
 *   multiple: true,
 *   onFileAdd: (file) => {
 *     console.log('添加文件:', file.name);
 *   },
 *   onComplete: (result) => {
 *     console.log('上传完成:', result);
 *   },
 * });
 * ```
 */
export class FileUpload {
  /** 上传区域元素 */
  private dropZone: HTMLElement;

  /** 配置选项 */
  private options: FileUploadOptions;

  /** 已添加的文件列表 */
  private files: File[] = [];

  /** 移除事件监听的函数 */
  private removeListeners: RemoveEventListener[] = [];

  /** 预览元素映射 */
  private previewElements = new Map<File, HTMLElement>();

  /** 拖拽进入计数器 */
  private dragEnterCounter: number = 0;

  constructor(options: FileUploadOptions) {
    this.dropZone = options.dropZone;
    this.options = {
      activeClass: 'drag-active',
      multiple: true,
      autoPreview: true,
      ...options,
    };

    this.init();
  }

  /**
   * 初始化上传器
   */
  private init(): void {
    // 绑定事件处理器
    this.bindEvents();

    // 如果有预览容器，初始化预览区域
    if (this.options.previewContainer) {
      this.initPreviewContainer();
    }
  }

  /**
   * 绑定事件
   */
  private bindEvents(): void {
    const onDragEnter = this.onDragEnter.bind(this);
    const onDragOver = this.onDragOver.bind(this);
    const onDragLeave = this.onDragLeave.bind(this);
    const onDrop = this.onDrop.bind(this);

    this.dropZone.addEventListener('dragenter', onDragEnter);
    this.dropZone.addEventListener('dragover', onDragOver);
    this.dropZone.addEventListener('dragleave', onDragLeave);
    this.dropZone.addEventListener('drop', onDrop);

    this.removeListeners.push(() => {
      this.dropZone.removeEventListener('dragenter', onDragEnter);
      this.dropZone.removeEventListener('dragover', onDragOver);
      this.dropZone.removeEventListener('dragleave', onDragLeave);
      this.dropZone.removeEventListener('drop', onDrop);
    });
  }

  /**
   * 初始化预览容器
   */
  private initPreviewContainer(): void {
    const container = this.options.previewContainer;
    if (!container) return;

    // 清空容器
    container.innerHTML = '';
  }

  /**
   * 拖拽进入事件处理器
   */
  private onDragEnter(e: DragEvent): void {
    e.preventDefault();
    e.stopPropagation();

    this.dragEnterCounter++;

    // 只在第一次进入时添加样式
    if (this.dragEnterCounter === 1) {
      addClass(this.dropZone, this.options.activeClass || 'drag-active');
    }
  }

  /**
   * 拖拽悬停事件处理器
   */
  private onDragOver(e: DragEvent): void {
    e.preventDefault();
    e.stopPropagation();

    // 设置拖拽效果
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'copy';
    }
  }

  /**
   * 拖拽离开事件处理器
   */
  private onDragLeave(e: DragEvent): void {
    e.preventDefault();
    e.stopPropagation();

    this.dragEnterCounter--;

    // 只在完全离开时移除样式
    if (this.dragEnterCounter === 0) {
      removeClass(this.dropZone, this.options.activeClass || 'drag-active');
    }
  }

  /**
   * 放下事件处理器
   */
  private onDrop(e: DragEvent): void {
    e.preventDefault();
    e.stopPropagation();

    // 重置计数器和样式
    this.dragEnterCounter = 0;
    removeClass(this.dropZone, this.options.activeClass || 'drag-active');

    // 获取文件列表
    const files = e.dataTransfer?.files;
    if (!files || files.length === 0) return;

    // 处理文件
    this.handleFiles(Array.from(files));
  }

  /**
   * 处理文件列表
   */
  private handleFiles(fileList: File[]): void {
    const startTime = Date.now();
    const successFiles: File[] = [];
    const failedFiles: UploadError[] = [];

    for (const file of fileList) {
      // 检查文件数量限制
      if (this.options.maxFiles && this.files.length >= this.options.maxFiles) {
        failedFiles.push({
          file,
          message: `文件数量超过限制 (${this.options.maxFiles})`,
          code: ErrorCode.TOO_MANY_FILES,
        });
        continue;
      }

      // 验证文件
      const validationError = this.validateFile(file);
      if (validationError) {
        failedFiles.push(validationError);
        continue;
      }

      // 添加文件
      this.files.push(file);
      successFiles.push(file);

      // 触发文件添加回调
      this.options.onFileAdd?.(file);

      // 创建文件预览
      if (this.options.autoPreview) {
        this.createPreview(file);
      }
    }

    // 触发完成回调
    if (successFiles.length > 0 || failedFiles.length > 0) {
      const result: UploadResult = {
        success: successFiles,
        failed: failedFiles,
        duration: Date.now() - startTime,
      };

      this.options.onComplete?.(result);
    }
  }

  /**
   * 验证文件
   */
  private validateFile(file: File): UploadError | null {
    // 自定义验证
    if (this.options.onValidate) {
      const result = this.options.onValidate(file);
      if (result !== true) {
        return {
          file,
          message: typeof result === 'string' ? result : '文件验证失败',
          code: ErrorCode.VALIDATION_FAILED,
        };
      }
    }

    // 验证文件类型
    if (this.options.accept && this.options.accept.length > 0) {
      if (!validateFileType(file, this.options.accept)) {
        return {
          file,
          message: `不支持的文件类型: ${file.type || '未知'}`,
          code: ErrorCode.FILE_TYPE_NOT_ACCEPTED,
        };
      }
    }

    // 验证文件大小
    if (this.options.maxSize) {
      if (!validateFileSize(file, this.options.maxSize)) {
        return {
          file,
          message: `文件大小超过限制: ${formatFileSize(file.size)} > ${formatFileSize(this.options.maxSize)}`,
          code: ErrorCode.FILE_TOO_LARGE,
        };
      }
    }

    return null;
  }

  /**
   * 创建文件预览
   */
  private async createPreview(file: File): Promise<void> {
    const container = this.options.previewContainer;
    if (!container) return;

    const previewItem = document.createElement('div');
    previewItem.className = 'file-preview-item';

    // 创建文件信息
    const fileInfo = document.createElement('div');
    fileInfo.className = 'file-info';
    fileInfo.innerHTML = `
      <span class="file-name">${this.escapeHtml(file.name)}</span>
      <span class="file-size">${formatFileSize(file.size)}</span>
    `;

    // 创建删除按钮
    const removeBtn = document.createElement('button');
    removeBtn.className = 'file-remove';
    removeBtn.textContent = '×';
    removeBtn.onclick = () => this.removeFile(file);

    previewItem.appendChild(fileInfo);
    previewItem.appendChild(removeBtn);

    // 如果是图片，创建图片预览
    if (file.type.startsWith('image/')) {
      try {
        const dataUrl = await createFilePreview(file);
        const img = document.createElement('img');
        img.src = dataUrl;
        img.className = 'file-preview-image';
        img.alt = file.name;
        previewItem.insertBefore(img, fileInfo);
      } catch {
        // 如果无法创建预览，显示文件图标
        const icon = document.createElement('div');
        icon.className = 'file-icon';
        icon.textContent = '🖼';
        previewItem.insertBefore(icon, fileInfo);
      }
    } else {
      // 非图片文件显示图标
      const icon = document.createElement('div');
      icon.className = 'file-icon';
      icon.textContent = this.getFileIcon(file);
      previewItem.insertBefore(icon, fileInfo);
    }

    container.appendChild(previewItem);
    this.previewElements.set(file, previewItem);
  }

  /**
   * 获取文件图标
   */
  private getFileIcon(file: File): string {
    const type = file.type;
    const name = file.name.toLowerCase();

    if (type.startsWith('image/')) return '🖼';
    if (type.startsWith('video/')) return '🎬';
    if (type.startsWith('audio/')) return '🎵';
    if (type === 'application/pdf') return '📄';
    if (name.endsWith('.doc') || name.endsWith('.docx')) return '📝';
    if (name.endsWith('.xls') || name.endsWith('.xlsx')) return '📊';
    if (name.endsWith('.zip') || name.endsWith('.rar')) return '📦';
    return '📁';
  }

  /**
   * HTML 转义
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * 移除文件
   */
  removeFile(file: File): void {
    const index = this.files.indexOf(file);
    if (index === -1) return;

    this.files.splice(index, 1);

    // 移除预览
    const previewElement = this.previewElements.get(file);
    if (previewElement) {
      previewElement.remove();
      this.previewElements.delete(file);
    }

    // 触发回调
    this.options.onFileRemove?.(file);
  }

  /**
   * 清空所有文件
   */
  clearFiles(): void {
    const files = [...this.files];
    this.files = [];

    // 清空预览
    this.previewElements.forEach((element) => element.remove());
    this.previewElements.clear();

    // 触发回调
    files.forEach((file) => this.options.onFileRemove?.(file));
  }

  /**
   * 获取文件列表
   */
  getFiles(): File[] {
    return [...this.files];
  }

  /**
   * 获取文件数量
   */
  getFileCount(): number {
    return this.files.length;
  }

  /**
   * 模拟上传（示例）
   *
   * 实际项目中应该替换为真实的上传逻辑
   */
  async upload(
    url: string,
    options: RequestInit = {}
  ): Promise<UploadResult> {
    const startTime = Date.now();
    const successFiles: File[] = [];
    const failedFiles: UploadError[] = [];

    for (const file of this.files) {
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(url, {
          ...options,
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          successFiles.push(file);
        } else {
          failedFiles.push({
            file,
            message: `上传失败: ${response.statusText}`,
            code: ErrorCode.UPLOAD_FAILED,
          });
        }
      } catch (error) {
        failedFiles.push({
          file,
          message: `上传失败: ${error instanceof Error ? error.message : '未知错误'}`,
          code: ErrorCode.UPLOAD_FAILED,
        });
      }
    }

    const result: UploadResult = {
      success: successFiles,
      failed: failedFiles,
      duration: Date.now() - startTime,
    };

    return result;
  }

  /**
   * 销毁上传器
   */
  destroy(): void {
    // 移除事件监听
    this.removeListeners.forEach((remove) => remove());
    this.removeListeners = [];

    // 清空文件和预览
    this.clearFiles();
  }
}
