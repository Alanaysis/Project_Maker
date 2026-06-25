/**
 * @file basic_window.cpp
 * @brief Dear ImGui 基础窗口示例
 * @details 展示 Dear ImGui 的基本用法
 *          Dear ImGui 是一个即时模式 GUI 库
 *          适合工具开发、调试界面等
 *
 * 注意：此示例需要图形后端支持（如 GLFW + OpenGL）
 * 编译时需要链接 imgui 库和图形后端
 */

#include <iostream>
#include <string>
#include <vector>

/**
 * @brief ImGui 基本概念说明
 * @details 解释 Dear ImGui 的设计理念
 */
void imgui_concepts() {
    std::cout << "=== Dear ImGui 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Dear ImGui 是一个即时模式（Immediate Mode）GUI 库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  1. 即时模式 - 每帧重新构建 UI" << std::endl;
    std::cout << "  2. 无状态 - 不需要管理控件状态" << std::endl;
    std::cout << "  3. 简单易用 - API 简洁明了" << std::endl;
    std::cout << "  4. 高效 - 渲染性能优秀" << std::endl;
    std::cout << "  5. 可移植 - 支持多种图形后端" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief ImGui 基本控件示例
 * @details 展示 ImGui 的基本控件使用
 */
void imgui_widgets() {
    std::cout << "=== ImGui 基本控件 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "常用控件：" << std::endl;
    std::cout << "  - ImGui::Text() - 文本显示" << std::endl;
    std::cout << "  - ImGui::Button() - 按钮" << std::endl;
    std::cout << "  - ImGui::Checkbox() - 复选框" << std::endl;
    std::cout << "  - ImGui::SliderFloat() - 滑块" << std::endl;
    std::cout << "  - ImGui::InputText() - 文本输入" << std::endl;
    std::cout << "  - ImGui::TreeNode() - 树节点" << std::endl;
    std::cout << "  - ImGui::BeginTable() - 表格" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief ImGui 代码示例
 * @details 展示 ImGui 的典型代码结构
 */
void imgui_code_example() {
    std::cout << "=== ImGui 代码示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "典型代码结构：" << std::endl;
    std::cout << std::endl;

    std::cout << R"(
// 1. 初始化
ImGui::CreateContext();
ImGui_ImplGlfw_InitForOpenGL(window, true);
ImGui_ImplOpenGL3_Init("#version 330");

// 2. 主循环
while (!glfwWindowShouldClose(window)) {
    // 开始新帧
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    // 构建 UI
    ImGui::Begin("My Window");
    ImGui::Text("Hello, World!");
    if (ImGui::Button("Click Me")) {
        // 处理按钮点击
    }
    ImGui::End();

    // 渲染
    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}

// 3. 清理
ImGui_ImplOpenGL3_Shutdown();
ImGui_ImplGlfw_Shutdown();
ImGui::DestroyContext();
)" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief ImGui 应用场景
 * @details 介绍 ImGui 的典型应用场景
 */
void imgui_applications() {
    std::cout << "=== ImGui 应用场景 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "典型应用场景：" << std::endl;
    std::cout << std::endl;

    std::cout << "1. 游戏开发工具" << std::endl;
    std::cout << "   - 调试控制台" << std::endl;
    std::cout << "   - 属性编辑器" << std::endl;
    std::cout << "   - 场景管理器" << std::endl;
    std::cout << std::endl;

    std::cout << "2. 可视化工具" << std::endl;
    std::cout << "   - 数据可视化" << std::endl;
    std::cout << "   - 图像查看器" << std::endl;
    std::cout << "   - 性能分析器" << std::endl;
    std::cout << std::endl;

    std::cout << "3. 开发工具" << std::endl;
    std::cout << "   - 代码编辑器" << std::endl;
    std::cout << "   - 日志查看器" << std::endl;
    std::cout << "   - 配置管理器" << std::endl;
    std::cout << std::endl;

    std::cout << "4. 原型开发" << std::endl;
    std::cout << "   - 快速 UI 原型" << std::endl;
    std::cout << "   - 算法可视化" << std::endl;
    std::cout << "   - 交互式演示" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief ImGui 与其他 GUI 库对比
 * @details 比较 ImGui 与其他 GUI 库的差异
 */
void imgui_comparison() {
    std::cout << "=== ImGui 与其他 GUI 库对比 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "即时模式 vs 保留模式：" << std::endl;
    std::cout << std::endl;

    std::cout << "即时模式（ImGui）：" << std::endl;
    std::cout << "  - 每帧重新构建 UI" << std::endl;
    std::cout << "  - 无状态管理" << std::endl;
    std::cout << "  - 代码即 UI" << std::endl;
    std::cout << "  - 适合工具开发" << std::endl;
    std::cout << std::endl;

    std::cout << "保留模式（Qt, GTK）：" << std::endl;
    std::cout << "  - 创建控件后保留状态" << std::endl;
    std::cout << "  - 需要状态管理" << std::endl;
    std::cout << "  - UI 与代码分离" << std::endl;
    std::cout << "  - 适合应用程序" << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "=== Dear ImGui 基础示例 ===" << std::endl;
    std::cout << std::endl;

    imgui_concepts();
    imgui_widgets();
    imgui_code_example();
    imgui_applications();
    imgui_comparison();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 ImGui 示例需要图形后端支持" << std::endl;
    std::cout << "请参考 imgui/examples 目录中的完整示例" << std::endl;

    return 0;
}