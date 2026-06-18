#pragma once

#include "core/common.h"
#include "core/config.h"
#include "core/status.h"
#include "storage/page.h"
#include "storage/buffer_pool.h"
#include <functional>
#include <vector>
#include <optional>

namespace minidb {

// B+ 树键类型 (使用整数作为简化)
using KeyType = int32_t;

// B+ 树值类型 (RowId)
using ValueType = RowId;

// 键比较器
using KeyComparator = std::function<int(const KeyType&, const KeyType&)>;

// 默认键比较器
inline int defaultKeyComparator(const KeyType& a, const KeyType& b) {
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
}

// ==================== B+ 树节点 ====================

// 内部节点头
struct BPlusTreeInternalHeader {
    PageType page_type;      // PageType::INDEX_PAGE
    page_id_t parent_id;     // 父节点页面 ID
    int key_count;           // 当前 key 数量
    page_id_t page_id;       // 当前节点页面 ID

    BPlusTreeInternalHeader()
        : page_type(PageType::INDEX_PAGE),
          parent_id(INVALID_PAGE_ID),
          key_count(0),
          page_id(INVALID_PAGE_ID) {}
};

// 内部节点布局:
// [header | keys[0..n-1] | children[0..n]]
struct InternalNode {
    BPlusTreeInternalHeader header;
    KeyType keys[INTERNAL_MAX_SIZE];
    page_id_t children[INTERNAL_MAX_SIZE + 1];

    // 查找 key 应该去往的子节点索引
    int findChildIndex(const KeyType& key, const KeyComparator& comp) const {
        for (int i = 0; i < header.key_count; ++i) {
            if (comp(key, keys[i]) < 0) {
                return i;
            }
        }
        return header.key_count;
    }

    // 在指定位置插入 key 和 child
    void insertAt(int index, const KeyType& key, page_id_t child) {
        // 向后移动
        for (int i = header.key_count; i > index; --i) {
            keys[i] = keys[i - 1];
            children[i + 1] = children[i];
        }
        keys[index] = key;
        children[index + 1] = child;
        header.key_count++;
    }

    // 删除指定位置的 key
    void removeAt(int index) {
        for (int i = index; i < header.key_count - 1; ++i) {
            keys[i] = keys[i + 1];
            children[i + 1] = children[i + 2];
        }
        header.key_count--;
    }
};

// 叶子节点头
struct BPlusTreeLeafHeader {
    PageType page_type;      // PageType::LEAF_PAGE
    page_id_t parent_id;     // 父节点页面 ID
    int key_count;           // 当前 key 数量
    page_id_t page_id;       // 当前节点页面 ID
    page_id_t next_page_id;  // 下一个叶子节点 (链表)

    BPlusTreeLeafHeader()
        : page_type(PageType::LEAF_PAGE),
          parent_id(INVALID_PAGE_ID),
          key_count(0),
          page_id(INVALID_PAGE_ID),
          next_page_id(INVALID_PAGE_ID) {}
};

// 叶子节点布局:
// [header | keys[0..n-1] | values[0..n-1]]
struct LeafNode {
    BPlusTreeLeafHeader header;
    KeyType keys[LEAF_MAX_SIZE];
    ValueType values[LEAF_MAX_SIZE];

    // 查找 key 的位置，返回 -1 表示未找到
    int findKeyIndex(const KeyType& key, const KeyComparator& comp) const {
        // 二分查找
        int left = 0;
        int right = header.key_count - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            int cmp = comp(key, keys[mid]);
            if (cmp == 0) return mid;
            if (cmp < 0) right = mid - 1;
            else left = mid + 1;
        }
        return -1;
    }

    // 查找 key 应该插入的位置
    int findInsertPosition(const KeyType& key, const KeyComparator& comp) const {
        for (int i = 0; i < header.key_count; ++i) {
            if (comp(key, keys[i]) < 0) {
                return i;
            }
        }
        return header.key_count;
    }

    // 在指定位置插入
    void insertAt(int index, const KeyType& key, const ValueType& value) {
        // 向后移动
        for (int i = header.key_count; i > index; --i) {
            keys[i] = keys[i - 1];
            values[i] = values[i - 1];
        }
        keys[index] = key;
        values[index] = value;
        header.key_count++;
    }

    // 删除指定位置
    void removeAt(int index) {
        for (int i = index; i < header.key_count - 1; ++i) {
            keys[i] = keys[i + 1];
            values[i] = values[i + 1];
        }
        header.key_count--;
    }
};

// ==================== B+ 树类 ====================

/**
 * @brief B+ 树索引
 *
 * 特点:
 * - 支持高效的点查询和范围查询
 * - 叶子节点通过链表连接
 * - 支持并发访问 (需要外部锁)
 */
class BPlusTree {
public:
    /**
     * @brief 构造函数
     * @param bpm 缓冲池管理器
     * @param name 索引名称
     * @param comparator 键比较器
     */
    BPlusTree(BufferPoolManager* bpm, const std::string& name,
              const KeyComparator& comparator = defaultKeyComparator);

    /**
     * @brief 析构函数
     */
    ~BPlusTree();

    /**
     * @brief 插入键值对
     * @param key 键
     * @param value 值
     * @return 是否成功
     */
    bool insert(const KeyType& key, const ValueType& value);

    /**
     * @brief 删除键
     * @param key 键
     * @return 是否成功
     */
    bool remove(const KeyType& key);

    /**
     * @brief 查找键
     * @param key 键
     * @param result 输出参数，查找结果
     * @return 是否找到
     */
    bool search(const KeyType& key, ValueType* result);

    /**
     * @brief 范围查询
     * @param start 起始键 (包含)
     * @param end 结束键 (包含)
     * @return 结果列表
     */
    std::vector<ValueType> rangeQuery(const KeyType& start, const KeyType& end);

    /**
     * @brief 获取所有键值对
     * @return 所有键值对
     */
    std::vector<std::pair<KeyType, ValueType>> getAll();

    /**
     * @brief 获取树的高度
     * @return 树的高度
     */
    int getHeight() const;

    /**
     * @brief 获取节点数量
     * @return 节点数量
     */
    int getNodeCount() const;

    /**
     * @brief 获取键值对数量
     * @return 键值对数量
     */
    int getSize() const;

    /**
     * @brief 检查树是否为空
     * @return 是否为空
     */
    bool isEmpty() const;

    /**
     * @brief 打印树结构 (调试用)
     */
    void printTree() const;

private:
    /**
     * @brief 查找叶子节点
     * @param key 键
     * @return 叶子节点页面
     */
    Page* findLeafPage(const KeyType& key);

    /**
     * @brief 分裂叶子节点
     * @param leaf_page 叶子节点页面
     */
    void splitLeaf(Page* leaf_page);

    /**
     * @brief 分裂内部节点
     * @param internal_page 内部节点页面
     */
    void splitInternal(Page* internal_page);

    /**
     * @brief 插入到父节点
     * @param parent_page 父节点页面
     * @param old_page_id 旧节点页面 ID
     * @param new_page_id 新节点页面 ID
     * @param key 提升的键
     */
    void insertIntoParent(Page* parent_page, page_id_t old_page_id,
                          page_id_t new_page_id, const KeyType& key);

    /**
     * @brief 合并叶子节点
     * @param leaf_page 叶子节点页面
     */
    void coalesceLeaf(Page* leaf_page);

    /**
     * @brief 合并内部节点
     * @param internal_page 内部节点页面
     */
    void coalesceInternal(Page* internal_page);

    /**
     * @brief 重新分配叶子节点
     * @param leaf_page 叶子节点页面
     */
    void redistributeLeaf(Page* leaf_page);

    /**
     * @brief 重新分配内部节点
     * @param internal_page 内部节点页面
     */
    void redistributeInternal(Page* internal_page);

    /**
     * @brief 查找兄弟节点
     * @param page 当前节点页面
     * @return 兄弟节点页面 ID，如果不存在返回 INVALID_PAGE_ID
     */
    page_id_t findSibling(Page* page);

    /**
     * @brief 更新根节点
     * @param new_root_page_id 新根节点页面 ID
     */
    void updateRootPageId(page_id_t new_root_page_id);

    BufferPoolManager* bpm_;       // 缓冲池管理器
    std::string name_;             // 索引名称
    page_id_t root_page_id_;       // 根节点页面 ID
    KeyComparator comparator_;     // 键比较器
    std::mutex root_latch_;        // 根节点锁
};

}  // namespace minidb
