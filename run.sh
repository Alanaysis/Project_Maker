#!/bin/bash

# 自动化项目生成器启动脚本

set -e

echo "🎯 学习型项目工厂 - 自动化生成器"
echo "=================================="

# 检查依赖
echo "🔍 检查环境..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 需要安装 Node.js"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要安装 Python 3"
    exit 1
fi

echo "✅ 环境检查通过"

# 显示配置
echo ""
echo "📋 配置信息:"
echo "  最大轮数: 2"
echo "  最大并发: 3"
echo "  日志级别: standard"
echo ""

# 确认执行
read -p "是否开始执行? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "🚀 开始执行..."
echo ""

# 创建日志目录
mkdir -p logs

# 执行工作流
# 注意: 这里需要调用 Claude Code 的工作流引擎
# 实际执行时，用户需要在 Claude Code 中运行工作流

echo "📝 工作流脚本已准备就绪"
echo ""
echo "请在 Claude Code 中执行以下命令:"
echo ""
echo "  /workflow auto-project-generator"
echo ""
echo "或者手动执行:"
echo ""
echo "  1. 查看愿望单: cat WISHLIST.md"
echo "  2. 选择任务开始实现"
echo ""

# 如果有 Claude Code CLI，可以尝试直接执行
if command -v claude &> /dev/null; then
    echo "🤖 检测到 Claude Code CLI"
    read -p "是否使用 Claude Code 执行工作流? (y/N) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 启动 Claude Code 工作流..."
        claude /workflow auto-project-generator
    fi
fi

echo ""
echo "✅ 脚本执行完成"
