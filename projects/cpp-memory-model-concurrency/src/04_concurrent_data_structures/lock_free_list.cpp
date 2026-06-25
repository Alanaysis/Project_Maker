/**
 * 无锁链表 (Lock-free Linked List)
 *
 * Harris Linked List 的实现：
 * 1. 使用标记指针表示删除状态
 * 2. 两阶段删除：标记和物理删除
 * 3. 支持并发插入和删除
 * 4. 适合有序集合
 *
 * 编译：g++ -std=c++17 -pthread lock_free_list.cpp -o lock_free_list
 */

#include <iostream>
#include <atomic>
#include <memory>
#include <thread>
#include <vector>
#include <set>
#include <cassert>

// Harris 无锁链表
template<typename T>
class LockFreeList {
private:
    struct Node {
        T key;
        std::atomic<Node*> next;
        bool marked;

        Node() : key(T()), next(nullptr), marked(false) {}
        Node(const T& k) : key(k), next(nullptr), marked(false) {}
    };

    Node* head_;
    Node* tail_;

    // 查找位置
    struct Window {
        Node* prev;
        Node* curr;
    };

    Window find(const T& key) {
        Node* prev;
        Node* curr;
        Node* next;

        retry:
        while (true) {
            prev = head_;
            curr = prev->next.load();

            while (true) {
                if (curr == tail_) {
                    return {prev, curr};
                }

                next = curr->next.load();
                bool marked = curr->marked;

                if (marked) {
                    // 尝试物理删除
                    if (!prev->next.compare_exchange_strong(curr, next)) {
                        goto retry;
                    }
                    curr = next;
                } else {
                    if (curr->key >= key) {
                        return {prev, curr};
                    }
                    prev = curr;
                    curr = next;
                }
            }
        }
    }

public:
    LockFreeList() {
        head_ = new Node();
        tail_ = new Node();
        head_->next.store(tail_, std::memory_order_relaxed);
    }

    ~LockFreeList() {
        Node* current = head_;
        while (current) {
            Node* next = current->next.load();
            delete current;
            current = next;
        }
    }

    bool insert(const T& key) {
        Node* new_node = new Node(key);

        while (true) {
            Window window = find(key);
            Node* prev = window.prev;
            Node* curr = window.curr;

            if (curr != tail_ && curr->key == key) {
                delete new_node;
                return false;  // 已存在
            }

            new_node->next.store(curr, std::memory_order_relaxed);
            if (prev->next.compare_exchange_strong(curr, new_node)) {
                return true;
            }
        }
    }

    bool remove(const T& key) {
        while (true) {
            Window window = find(key);
            Node* prev = window.prev;
            Node* curr = window.curr;

            if (curr == tail_ || curr->key != key) {
                return false;  // 不存在
            }

            Node* next = curr->next.load();

            // 阶段1：标记删除
            curr->marked = true;

            // 阶段2：物理删除
            prev->next.compare_exchange_strong(curr, next);
            return true;
        }
    }

    bool contains(const T& key) {
        Node* curr = head_->next.load();

        while (curr != tail_ && curr->key <= key) {
            if (!curr->marked && curr->key == key) {
                return true;
            }
            curr = curr->next.load();
        }
        return false;
    }

    void print() {
        Node* curr = head_->next.load();
        std::cout << "List: ";
        while (curr != tail_) {
            if (!curr->marked) {
                std::cout << curr->key << " ";
            }
            curr = curr->next.load();
        }
        std::cout << std::endl;
    }
};

// 基本测试
void basic_test() {
    std::cout << "=== 基本测试 ===" << std::endl;

    LockFreeList<int> list;

    // 插入
    for (int i = 0; i < 10; ++i) {
        list.insert(i);
    }

    list.print();

    // 查找
    std::cout << "contains(5): " << list.contains(5) << std::endl;
    std::cout << "contains(15): " << list.contains(15) << std::endl;

    // 删除
    list.remove(5);
    list.remove(9);

    list.print();
}

// 并发测试
void concurrent_test() {
    std::cout << "\n=== 并发测试 ===" << std::endl;

    LockFreeList<int> list;
    const int num_threads = 4;
    const int ops_per_thread = 1000;
    std::vector<std::thread> threads;

    // 并发插入
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&list, i]() {
            for (int j = 0; j < ops_per_thread; ++j) {
                list.insert(i * ops_per_thread + j);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "插入完成" << std::endl;

    // 并发查找
    threads.clear();
    std::atomic<int> found{0};

    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&list, i, &found]() {
            for (int j = 0; j < ops_per_thread; ++j) {
                if (list.contains(i * ops_per_thread + j)) {
                    found.fetch_add(1);
                }
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "找到: " << found.load() << " / "
              << num_threads * ops_per_thread << std::endl;
}

int main() {
    std::cout << "C++ 并发数据结构：无锁链表" << std::endl;
    std::cout << "===========================\n" << std::endl;

    basic_test();
    concurrent_test();

    return 0;
}
