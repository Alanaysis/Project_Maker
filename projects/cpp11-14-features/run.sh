#!/bin/bash

# C++11/14 新特性项目运行脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 检查构建
check_build() {
    if [ ! -d "build" ]; then
        print_warn "构建目录不存在，正在构建..."
        ./build.sh build
    fi
}

# 运行单个示例
run_example() {
    local example=$1
    local executable="build/$example"

    if [ ! -f "$executable" ]; then
        print_error "示例 $example 不存在，请先编译项目"
        exit 1
    fi

    print_header "运行示例: $example"
    ./$executable
}

# 显示菜单
show_menu() {
    echo ""
    print_header "C++11/14 新特性示例"
    echo ""
    echo "请选择要运行的示例："
    echo ""
    echo "  1. 移动语义和右值引用 (01_move_semantics)"
    echo "  2. Lambda 表达式 (02_lambda)"
    echo "  3. 智能指针 (03_smart_pointers)"
    echo "  4. 并发编程 (04_threads)"
    echo "  5. 可变参数模板 (05_variadic_templates)"
    echo "  6. constexpr (06_constexpr)"
    echo "  7. auto 和 decltype (07_auto_decltype)"
    echo "  8. 范围 for 循环 (08_range_for)"
    echo "  9. 初始化列表 (09_initializer_list)"
    echo ""
    echo "  a. 运行所有示例"
    echo "  m. 运行主程序"
    echo "  t. 运行测试"
    echo "  q. 退出"
    echo ""
    read -p "请输入选项 [1-9/a/m/t/q]: " choice
}

# 运行所有示例
run_all_examples() {
    local examples=(
        "01_move_semantics"
        "02_lambda"
        "03_smart_pointers"
        "04_threads"
        "05_variadic_templates"
        "06_constexpr"
        "07_auto_decltype"
        "08_range_for"
        "09_initializer_list"
    )

    for example in "${examples[@]}"; do
        run_example "$example"
        echo ""
        read -p "按 Enter 继续下一个示例..."
    done
}

# 主函数
main() {
    # 切换到脚本所在目录
    cd "$(dirname "$0")"

    # 检查构建
    check_build

    # 如果有参数，直接运行指定示例
    if [ $# -gt 0 ]; then
        case "$1" in
            1|01_move_semantics)
                run_example "01_move_semantics"
                ;;
            2|02_lambda)
                run_example "02_lambda"
                ;;
            3|03_smart_pointers)
                run_example "03_smart_pointers"
                ;;
            4|04_threads)
                run_example "04_threads"
                ;;
            5|05_variadic_templates)
                run_example "05_variadic_templates"
                ;;
            6|06_constexpr)
                run_example "06_constexpr"
                ;;
            7|07_auto_decltype)
                run_example "07_auto_decltype"
                ;;
            8|08_range_for)
                run_example "08_range_for"
                ;;
            9|09_initializer_list)
                run_example "09_initializer_list"
                ;;
            all|a)
                run_all_examples
                ;;
            main|m)
                run_example "main"
                ;;
            test|t)
                ./build.sh test
                ;;
            *)
                print_error "未知选项: $1"
                echo "用法: $0 [1-9|all|main|test]"
                exit 1
                ;;
        esac
        return
    fi

    # 交互式菜单
    while true; do
        show_menu

        case $choice in
            1)
                run_example "01_move_semantics"
                ;;
            2)
                run_example "02_lambda"
                ;;
            3)
                run_example "03_smart_pointers"
                ;;
            4)
                run_example "04_threads"
                ;;
            5)
                run_example "05_variadic_templates"
                ;;
            6)
                run_example "06_constexpr"
                ;;
            7)
                run_example "07_auto_decltype"
                ;;
            8)
                run_example "08_range_for"
                ;;
            9)
                run_example "09_initializer_list"
                ;;
            a|A)
                run_all_examples
                ;;
            m|M)
                run_example "main"
                ;;
            t|T)
                ./build.sh test
                ;;
            q|Q)
                print_info "退出程序"
                exit 0
                ;;
            *)
                print_error "无效选项，请重新选择"
                ;;
        esac

        echo ""
        read -p "按 Enter 继续..."
    done
}

# 运行主函数
main "$@"
