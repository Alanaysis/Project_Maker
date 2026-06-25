/**
 * 对象模型 (Object Model)
 *
 * C++ 对象模型的核心概念：
 * 1. 对象由类型、地址、值、存储期组成
 * 2. 对象可能包含子对象（成员、基类、数组元素）
 * 3. 对象有生命周期（创建、使用、销毁）
 * 4. 对象的表示包括值表示和对象表示
 *
 * 编译：g++ -std=c++17 -pthread object_model.cpp -o object_model
 */

#include <iostream>
#include <memory>
#include <new>
#include <cstring>

// 示例1：对象的创建和销毁
void object_creation_destruction() {
    std::cout << "=== 对象的创建和销毁 ===" << std::endl;

    // 栈上对象（自动存储期）
    {
        int stack_obj = 42;
        std::cout << "栈对象: " << stack_obj << ", 地址: " << &stack_obj << std::endl;
    } // stack_obj 在此销毁

    // 堆上对象（动态存储期）
    {
        int* heap_obj = new int(42);
        std::cout << "堆对象: " << *heap_obj << ", 地址: " << heap_obj << std::endl;
        delete heap_obj;  // 必须手动销毁
    }

    // 智能指针管理堆对象
    {
        auto smart_obj = std::make_unique<int>(42);
        std::cout << "智能指针对象: " << *smart_obj << ", 地址: " << smart_obj.get() << std::endl;
    } // 自动销毁

    // 静态存储期对象
    static int static_obj = 42;
    std::cout << "静态对象: " << static_obj << ", 地址: " << &static_obj << std::endl;
}

// 示例2：对象的值表示和对象表示
void object_representation() {
    std::cout << "\n=== 对象的值表示和对象表示 ===" << std::endl;

    // 值表示：对象的值的位模式
    // 对象表示：值表示 + 填充位

    int value = 42;
    std::cout << "值: " << value << std::endl;

    // 查看对象表示（字节级）
    unsigned char* bytes = reinterpret_cast<unsigned char*>(&value);
    std::cout << "对象表示 (字节): ";
    for (size_t i = 0; i < sizeof(int); ++i) {
        std::cout << static_cast<int>(bytes[i]) << " ";
    }
    std::cout << std::endl;

    // 浮点数的对象表示
    float f = 3.14f;
    unsigned char* fbytes = reinterpret_cast<unsigned char*>(&f);
    std::cout << "float 3.14 的对象表示: ";
    for (size_t i = 0; i < sizeof(float); ++i) {
        std::cout << std::hex << static_cast<int>(fbytes[i]) << " ";
    }
    std::cout << std::dec << std::endl;
}

// 示例3：子对象
struct Point {
    int x;
    int y;

    Point(int x, int y) : x(x), y(y) {
        std::cout << "Point 构造: (" << x << ", " << y << ")" << std::endl;
    }

    ~Point() {
        std::cout << "Point 析构: (" << x << ", " << y << ")" << std::endl;
    }
};

struct Line {
    Point start;
    Point end;

    Line(int x1, int y1, int x2, int y2)
        : start(x1, y1), end(x2, y2) {
        std::cout << "Line 构造" << std::endl;
    }

    ~Line() {
        std::cout << "Line 析构" << std::endl;
    }
};

void subobjects() {
    std::cout << "\n=== 子对象 ===" << std::endl;

    // Line 包含两个 Point 子对象
    {
        Line line(0, 0, 10, 10);
        std::cout << "Line 起点: (" << line.start.x << ", " << line.start.y << ")" << std::endl;
        std::cout << "Line 终点: (" << line.end.x << ", " << line.end.y << ")" << std::endl;
    } // 先销毁 Line，再销毁 Point 子对象

    // 数组元素是子对象
    std::cout << "\n数组元素是子对象:" << std::endl;
    Point points[2] = {{1, 2}, {3, 4}};
    std::cout << "points[0]: (" << points[0].x << ", " << points[0].y << ")" << std::endl;
    std::cout << "points[1]: (" << points[1].x << ", " << points[1].y << ")" << std::endl;
}

// 示例4：对象的存储期
void storage_duration() {
    std::cout << "\n=== 对象的存储期 ===" << std::endl;

    // 自动存储期（栈）
    {
        int auto_var = 42;
        std::cout << "自动存储期: " << auto_var << std::endl;
    }

    // 静态存储期
    static int static_var = 42;
    std::cout << "静态存储期: " << static_var << std::endl;

    // 线程存储期
    thread_local int thread_var = 42;
    std::cout << "线程存储期: " << thread_var << std::endl;

    // 动态存储期
    int* dynamic_var = new int(42);
    std::cout << "动态存储期: " << *dynamic_var << std::endl;
    delete dynamic_var;
}

// 示例5：对象的对齐
void object_alignment() {
    std::cout << "\n=== 对象的对齐 ===" << std::endl;

    // alignof 返回类型的对齐要求
    std::cout << "char 对齐: " << alignof(char) << std::endl;
    std::cout << "int 对齐: " << alignof(int) << std::endl;
    std::cout << "double 对齐: " << alignof(double) << std::endl;

    // alignas 指定对齐
    struct alignas(16) AlignedStruct {
        int value;
        // 编译器会添加填充以满足 16 字节对齐
    };

    std::cout << "\nAlignedStruct 大小: " << sizeof(AlignedStruct) << std::endl;
    std::cout << "AlignedStruct 对齐: " << alignof(AlignedStruct) << std::endl;

    // 动态内存的对齐分配
    void* ptr = ::operator new(sizeof(AlignedStruct), std::align_val_t(16));
    std::cout << "对齐分配地址: " << ptr << std::endl;
    std::cout << "地址是否 16 字节对齐: "
              << (reinterpret_cast<uintptr_t>(ptr) % 16 == 0 ? "是" : "否") << std::endl;
    ::operator delete(ptr, std::align_val_t(16));
}

// 示例6：对象的生命周期
class LifetimeDemo {
public:
    LifetimeDemo(int id) : id_(id) {
        std::cout << "LifetimeDemo " << id_ << " 构造" << std::endl;
    }

    ~LifetimeDemo() {
        std::cout << "LifetimeDemo " << id_ << " 析构" << std::endl;
    }

    int id() const { return id_; }

private:
    int id_;
};

void object_lifetime() {
    std::cout << "\n=== 对象的生命周期 ===" << std::endl;

    // 局部对象的生命周期
    std::cout << "1. 局部对象:" << std::endl;
    {
        LifetimeDemo local(1);
        std::cout << "   使用对象 " << local.id() << std::endl;
    }
    std::cout << "   局部对象已销毁" << std::endl;

    // 动态对象的生命周期
    std::cout << "\n2. 动态对象:" << std::endl;
    LifetimeDemo* dynamic = new LifetimeDemo(2);
    std::cout << "   使用对象 " << dynamic->id() << std::endl;
    delete dynamic;
    std::cout << "   动态对象已销毁" << std::endl;

    // 智能指针管理的生命周期
    std::cout << "\n3. 智能指针对象:" << std::endl;
    {
        auto smart = std::make_unique<LifetimeDemo>(3);
        std::cout << "   使用对象 " << smart->id() << std::endl;
    }
    std::cout << "   智能指针对象已销毁" << std::endl;

    // 对象数组的生命周期
    std::cout << "\n4. 对象数组:" << std::endl;
    {
        LifetimeDemo arr[3] = {{4}, {5}, {6}};
        for (const auto& obj : arr) {
            std::cout << "   使用对象 " << obj.id() << std::endl;
        }
    }
    std::cout << "   对象数组已销毁（逆序析构）" << std::endl;
}

int main() {
    std::cout << "C++ 内存模型：对象模型 (Object Model)" << std::endl;
    std::cout << "=======================================\n" << std::endl;

    object_creation_destruction();
    object_representation();
    subobjects();
    storage_duration();
    object_alignment();
    object_lifetime();

    return 0;
}
