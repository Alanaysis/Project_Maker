#include "storage/bplus_tree.h"
#include <iostream>
#include <queue>
#include <stack>

namespace minidb {

BPlusTree::BPlusTree(BufferPoolManager* bpm, const std::string& name,
                     const KeyComparator& comparator)
    : bpm_(bpm), name_(name), root_page_id_(INVALID_PAGE_ID),
      comparator_(comparator) {
    MINIDB_LOG("BPlusTree created: " + name_);
}

BPlusTree::~BPlusTree() {
    MINIDB_LOG("BPlusTree destroyed: " + name_);
}

bool BPlusTree::insert(const KeyType& key, const ValueType& value) {
    std::lock_guard<std::mutex> lock(root_latch_);

    // 如果树为空，创建根节点
    if (root_page_id_ == INVALID_PAGE_ID) {
        page_id_t root_id;
        Page* root_page = bpm_->newPage(&root_id);
        if (!root_page) return false;

        LeafNode* root = reinterpret_cast<LeafNode*>(root_page->getData());
        root->header.page_type = PageType::LEAF_PAGE;
        root->header.page_id = root_id;
        root->header.parent_id = INVALID_PAGE_ID;
        root->header.key_count = 0;
        root->header.next_page_id = INVALID_PAGE_ID;

        root->insertAt(0, key, value);

        root_page->setDirty(true);
        bpm_->unpinPage(root_id, true);

        root_page_id_ = root_id;
        return true;
    }

    // 查找叶子节点
    Page* leaf_page = findLeafPage(key);
    if (!leaf_page) return false;

    LeafNode* leaf = reinterpret_cast<LeafNode*>(leaf_page->getData());
    page_id_t leaf_page_id = leaf->header.page_id;

    // 检查 key 是否已存在
    int existing_idx = leaf->findKeyIndex(key, comparator_);
    if (existing_idx != -1) {
        // key 已存在，更新值
        leaf->values[existing_idx] = value;
        leaf_page->setDirty(true);
        bpm_->unpinPage(leaf_page_id, true);
        return true;
    }

    // 检查叶子节点是否有空间
    if (leaf->header.key_count < LEAF_MAX_SIZE) {
        // 有空间，直接插入
        int insert_pos = leaf->findInsertPosition(key, comparator_);
        leaf->insertAt(insert_pos, key, value);
        leaf_page->setDirty(true);
        bpm_->unpinPage(leaf_page_id, true);
        return true;
    }

    // 叶子节点已满，需要分裂
    // 先插入再分裂
    int insert_pos = leaf->findInsertPosition(key, comparator_);
    leaf->insertAt(insert_pos, key, value);
    leaf_page->setDirty(true);

    splitLeaf(leaf_page);

    bpm_->unpinPage(leaf_page_id, true);
    return true;
}

bool BPlusTree::remove(const KeyType& key) {
    std::lock_guard<std::mutex> lock(root_latch_);

    if (root_page_id_ == INVALID_PAGE_ID) {
        return false;
    }

    // 查找叶子节点
    Page* leaf_page = findLeafPage(key);
    if (!leaf_page) return false;

    LeafNode* leaf = reinterpret_cast<LeafNode*>(leaf_page->getData());
    page_id_t leaf_page_id = leaf->header.page_id;

    // 查找 key
    int key_idx = leaf->findKeyIndex(key, comparator_);
    if (key_idx == -1) {
        // key 不存在
        bpm_->unpinPage(leaf_page_id, false);
        return false;
    }

    // 删除 key
    leaf->removeAt(key_idx);
    leaf_page->setDirty(true);

    // 检查是否需要合并或重新分配
    if (leaf->header.key_count < LEAF_MAX_SIZE / 2 &&
        leaf->header.parent_id != INVALID_PAGE_ID) {
        // 尝试合并或重新分配
        // 简化实现：暂时不做合并
    }

    bpm_->unpinPage(leaf_page_id, true);
    return true;
}

bool BPlusTree::search(const KeyType& key, ValueType* result) {
    std::lock_guard<std::mutex> lock(root_latch_);

    if (root_page_id_ == INVALID_PAGE_ID) {
        return false;
    }

    // 查找叶子节点
    Page* leaf_page = findLeafPage(key);
    if (!leaf_page) return false;

    LeafNode* leaf = reinterpret_cast<LeafNode*>(leaf_page->getData());
    page_id_t leaf_page_id = leaf->header.page_id;

    // 查找 key
    int key_idx = leaf->findKeyIndex(key, comparator_);
    if (key_idx == -1) {
        bpm_->unpinPage(leaf_page_id, false);
        return false;
    }

    *result = leaf->values[key_idx];
    bpm_->unpinPage(leaf_page_id, false);
    return true;
}

std::vector<ValueType> BPlusTree::rangeQuery(const KeyType& start,
                                              const KeyType& end) {
    std::lock_guard<std::mutex> lock(root_latch_);

    std::vector<ValueType> results;

    if (root_page_id_ == INVALID_PAGE_ID) {
        return results;
    }

    // 找到起始叶子节点
    Page* leaf_page = findLeafPage(start);
    if (!leaf_page) return results;

    LeafNode* leaf = reinterpret_cast<LeafNode*>(leaf_page->getData());

    // 找到起始位置
    int start_idx = 0;
    for (int i = 0; i < leaf->header.key_count; ++i) {
        if (comparator_(leaf->keys[i], start) >= 0) {
            start_idx = i;
            break;
        }
    }

    // 遍历叶子节点链表
    while (leaf_page != nullptr) {
        for (int i = start_idx; i < leaf->header.key_count; ++i) {
            if (comparator_(leaf->keys[i], end) > 0) {
                // 超出范围
                bpm_->unpinPage(leaf->header.page_id, false);
                return results;
            }
            results.push_back(leaf->values[i]);
        }

        // 移动到下一个叶子节点
        page_id_t next_page_id = leaf->header.next_page_id;
        page_id_t current_page_id = leaf->header.page_id;
        bpm_->unpinPage(current_page_id, false);

        if (next_page_id == INVALID_PAGE_ID) {
            break;
        }

        leaf_page = bpm_->fetchPage(next_page_id);
        if (!leaf_page) break;

        leaf = reinterpret_cast<LeafNode*>(leaf_page->getData());
        start_idx = 0;
    }

    return results;
}

std::vector<std::pair<KeyType, ValueType>> BPlusTree::getAll() {
    std::lock_guard<std::mutex> lock(root_latch_);

    std::vector<std::pair<KeyType, ValueType>> results;

    if (root_page_id_ == INVALID_PAGE_ID) {
        return results;
    }

    // 使用 BFS 遍历找到最左边的叶子节点
    std::queue<page_id_t> queue;
    queue.push(root_page_id_);

    page_id_t first_leaf_id = INVALID_PAGE_ID;

    while (!queue.empty()) {
        page_id_t current_id = queue.front();
        queue.pop();

        Page* page = bpm_->fetchPage(current_id);
        if (!page) continue;

        PageType page_type = page->getPageType();

        if (page_type == PageType::LEAF_PAGE) {
            first_leaf_id = current_id;
            bpm_->unpinPage(current_id, false);
            break;
        }

        // 内部节点
        InternalNode* internal = reinterpret_cast<InternalNode*>(page->getData());
        if (internal->header.key_count > 0) {
            queue.push(internal->children[0]);
        }
        bpm_->unpinPage(current_id, false);
    }

    if (first_leaf_id == INVALID_PAGE_ID) {
        return results;
    }

    // 遍历叶子节点链表
    page_id_t current_id = first_leaf_id;
    while (current_id != INVALID_PAGE_ID) {
        Page* page = bpm_->fetchPage(current_id);
        if (!page) break;

        LeafNode* leaf = reinterpret_cast<LeafNode*>(page->getData());

        for (int i = 0; i < leaf->header.key_count; ++i) {
            results.push_back({leaf->keys[i], leaf->values[i]});
        }

        page_id_t next_id = leaf->header.next_page_id;
        bpm_->unpinPage(current_id, false);
        current_id = next_id;
    }

    return results;
}

int BPlusTree::getHeight() const {
    if (root_page_id_ == INVALID_PAGE_ID) return 0;

    int height = 1;
    page_id_t current_id = root_page_id_;

    while (true) {
        Page* page = const_cast<BufferPoolManager*>(bpm_)->fetchPage(current_id);
        if (!page) break;

        PageType page_type = page->getPageType();
        if (page_type == PageType::LEAF_PAGE) {
            const_cast<BufferPoolManager*>(bpm_)->unpinPage(current_id, false);
            break;
        }

        InternalNode* internal = reinterpret_cast<InternalNode*>(page->getData());
        if (internal->header.key_count > 0) {
            current_id = internal->children[0];
            height++;
        }
        const_cast<BufferPoolManager*>(bpm_)->unpinPage(current_id, false);
    }

    return height;
}

int BPlusTree::getNodeCount() const {
    if (root_page_id_ == INVALID_PAGE_ID) return 0;

    int count = 0;
    std::queue<page_id_t> queue;
    queue.push(root_page_id_);

    while (!queue.empty()) {
        page_id_t current_id = queue.front();
        queue.pop();

        Page* page = const_cast<BufferPoolManager*>(bpm_)->fetchPage(current_id);
        if (!page) continue;

        count++;

        PageType page_type = page->getPageType();
        if (page_type != PageType::LEAF_PAGE) {
            InternalNode* internal = reinterpret_cast<InternalNode*>(page->getData());
            for (int i = 0; i <= internal->header.key_count; ++i) {
                queue.push(internal->children[i]);
            }
        }

        const_cast<BufferPoolManager*>(bpm_)->unpinPage(current_id, false);
    }

    return count;
}

int BPlusTree::getSize() const {
    auto* self = const_cast<BPlusTree*>(this);
    auto all = self->getAll();
    return all.size();
}

bool BPlusTree::isEmpty() const {
    return root_page_id_ == INVALID_PAGE_ID;
}

void BPlusTree::printTree() const {
    if (root_page_id_ == INVALID_PAGE_ID) {
        std::cout << "Empty tree" << std::endl;
        return;
    }

    std::cout << "B+ Tree: " << name_ << std::endl;
    std::cout << "Root page: " << root_page_id_ << std::endl;

    // BFS 遍历
    std::queue<std::pair<page_id_t, int>> queue;
    queue.push({root_page_id_, 0});

    int current_level = -1;

    while (!queue.empty()) {
        auto [page_id, level] = queue.front();
        queue.pop();

        if (level != current_level) {
            std::cout << "\nLevel " << level << ": ";
            current_level = level;
        }

        Page* page = const_cast<BufferPoolManager*>(bpm_)->fetchPage(page_id);
        if (!page) continue;

        PageType page_type = page->getPageType();

        if (page_type == PageType::LEAF_PAGE) {
            LeafNode* leaf = reinterpret_cast<LeafNode*>(page->getData());
            std::cout << "[";
            for (int i = 0; i < leaf->header.key_count; ++i) {
                if (i > 0) std::cout << ",";
                std::cout << leaf->keys[i];
            }
            std::cout << "] ";
        } else {
            InternalNode* internal = reinterpret_cast<InternalNode*>(page->getData());
            std::cout << "[";
            for (int i = 0; i < internal->header.key_count; ++i) {
                if (i > 0) std::cout << ",";
                std::cout << internal->keys[i];
            }
            std::cout << "] ";

            for (int i = 0; i <= internal->header.key_count; ++i) {
                queue.push({internal->children[i], level + 1});
            }
        }

        const_cast<BufferPoolManager*>(bpm_)->unpinPage(page_id, false);
    }

    std::cout << std::endl;
}

Page* BPlusTree::findLeafPage(const KeyType& key) {
    if (root_page_id_ == INVALID_PAGE_ID) {
        return nullptr;
    }

    page_id_t current_id = root_page_id_;

    while (true) {
        Page* page = bpm_->fetchPage(current_id);
        if (!page) return nullptr;

        PageType page_type = page->getPageType();

        if (page_type == PageType::LEAF_PAGE) {
            return page;
        }

        // 内部节点
        InternalNode* internal = reinterpret_cast<InternalNode*>(page->getData());
        int child_idx = internal->findChildIndex(key, comparator_);
        page_id_t child_id = internal->children[child_idx];

        bpm_->unpinPage(current_id, false);
        current_id = child_id;
    }
}

void BPlusTree::splitLeaf(Page* leaf_page) {
    LeafNode* old_leaf = reinterpret_cast<LeafNode*>(leaf_page->getData());
    page_id_t old_page_id = old_leaf->header.page_id;

    // 创建新叶子节点
    page_id_t new_page_id;
    Page* new_page = bpm_->newPage(&new_page_id);
    if (!new_page) return;

    LeafNode* new_leaf = reinterpret_cast<LeafNode*>(new_page->getData());
    new_leaf->header.page_type = PageType::LEAF_PAGE;
    new_leaf->header.page_id = new_page_id;
    new_leaf->header.next_page_id = old_leaf->header.next_page_id;

    // 分裂：将后半部分移到新节点
    int split_point = LEAF_MAX_SIZE / 2;
    int new_count = 0;

    for (int i = split_point; i < old_leaf->header.key_count + 1; ++i) {
        new_leaf->keys[new_count] = old_leaf->keys[i];
        new_leaf->values[new_count] = old_leaf->values[i];
        new_count++;
    }

    new_leaf->header.key_count = new_count;
    old_leaf->header.key_count = split_point;
    old_leaf->header.next_page_id = new_page_id;

    // 获取提升的 key
    KeyType promote_key = new_leaf->keys[0];

    // 更新页面
    leaf_page->setDirty(true);
    new_page->setDirty(true);

    // 插入到父节点
    if (old_leaf->header.parent_id == INVALID_PAGE_ID) {
        // 没有父节点，创建新的根节点
        page_id_t root_id;
        Page* root_page = bpm_->newPage(&root_id);
        if (!root_page) return;

        InternalNode* root = reinterpret_cast<InternalNode*>(root_page->getData());
        root->header.page_type = PageType::INDEX_PAGE;
        root->header.page_id = root_id;
        root->header.parent_id = INVALID_PAGE_ID;
        root->header.key_count = 1;
        root->keys[0] = promote_key;
        root->children[0] = old_page_id;
        root->children[1] = new_page_id;

        // 更新子节点的父节点
        old_leaf->header.parent_id = root_id;
        new_leaf->header.parent_id = root_id;

        root_page->setDirty(true);
        bpm_->unpinPage(root_id, true);

        root_page_id_ = root_id;
    } else {
        // 有父节点
        Page* parent_page = bpm_->fetchPage(old_leaf->header.parent_id);
        if (!parent_page) return;

        new_leaf->header.parent_id = old_leaf->header.parent_id;

        insertIntoParent(parent_page, old_page_id, new_page_id, promote_key);
    }

    bpm_->unpinPage(new_page_id, true);
}

void BPlusTree::splitInternal(Page* internal_page) {
    InternalNode* old_node = reinterpret_cast<InternalNode*>(internal_page->getData());
    page_id_t old_page_id = old_node->header.page_id;

    // 创建新内部节点
    page_id_t new_page_id;
    Page* new_page = bpm_->newPage(&new_page_id);
    if (!new_page) return;

    InternalNode* new_node = reinterpret_cast<InternalNode*>(new_page->getData());
    new_node->header.page_type = PageType::INDEX_PAGE;
    new_node->header.page_id = new_page_id;
    new_node->header.parent_id = old_node->header.parent_id;

    // 分裂
    int split_point = INTERNAL_MAX_SIZE / 2;
    KeyType promote_key = old_node->keys[split_point];

    // 复制后半部分到新节点
    int new_count = 0;
    for (int i = split_point + 1; i < old_node->header.key_count; ++i) {
        new_node->keys[new_count] = old_node->keys[i];
        new_node->children[new_count + 1] = old_node->children[i + 1];
        new_count++;
    }
    new_node->children[0] = old_node->children[split_point + 1];
    new_node->header.key_count = new_count;

    old_node->header.key_count = split_point;

    // 更新子节点的父节点
    for (int i = 0; i <= new_node->header.key_count; ++i) {
        Page* child_page = bpm_->fetchPage(new_node->children[i]);
        if (child_page) {
            if (child_page->getPageType() == PageType::LEAF_PAGE) {
                LeafNode* leaf = reinterpret_cast<LeafNode*>(child_page->getData());
                leaf->header.parent_id = new_page_id;
            } else {
                InternalNode* internal = reinterpret_cast<InternalNode*>(child_page->getData());
                internal->header.parent_id = new_page_id;
            }
            child_page->setDirty(true);
            bpm_->unpinPage(new_node->children[i], true);
        }
    }

    internal_page->setDirty(true);
    new_page->setDirty(true);

    // 插入到父节点
    if (old_node->header.parent_id == INVALID_PAGE_ID) {
        // 创建新的根节点
        page_id_t root_id;
        Page* root_page = bpm_->newPage(&root_id);
        if (!root_page) return;

        InternalNode* root = reinterpret_cast<InternalNode*>(root_page->getData());
        root->header.page_type = PageType::INDEX_PAGE;
        root->header.page_id = root_id;
        root->header.parent_id = INVALID_PAGE_ID;
        root->header.key_count = 1;
        root->keys[0] = promote_key;
        root->children[0] = old_page_id;
        root->children[1] = new_page_id;

        old_node->header.parent_id = root_id;
        new_node->header.parent_id = root_id;

        root_page->setDirty(true);
        bpm_->unpinPage(root_id, true);

        root_page_id_ = root_id;
    } else {
        Page* parent_page = bpm_->fetchPage(old_node->header.parent_id);
        if (!parent_page) return;

        insertIntoParent(parent_page, old_page_id, new_page_id, promote_key);
    }

    bpm_->unpinPage(new_page_id, true);
}

void BPlusTree::insertIntoParent(Page* parent_page, page_id_t old_page_id,
                                  page_id_t new_page_id, const KeyType& key) {
    InternalNode* parent = reinterpret_cast<InternalNode*>(parent_page->getData());

    // 找到 old_page_id 的位置
    int old_idx = -1;
    for (int i = 0; i <= parent->header.key_count; ++i) {
        if (parent->children[i] == old_page_id) {
            old_idx = i;
            break;
        }
    }

    if (old_idx == -1) {
        MINIDB_ERROR("BPlusTree: Child not found in parent");
        bpm_->unpinPage(parent->header.page_id, false);
        return;
    }

    // 检查父节点是否有空间
    if (parent->header.key_count < INTERNAL_MAX_SIZE) {
        // 有空间
        parent->insertAt(old_idx, key, new_page_id);
        parent_page->setDirty(true);
        bpm_->unpinPage(parent->header.page_id, true);
    } else {
        // 父节点已满，需要分裂
        parent->insertAt(old_idx, key, new_page_id);
        parent_page->setDirty(true);
        splitInternal(parent_page);
        bpm_->unpinPage(parent->header.page_id, true);
    }
}

void BPlusTree::coalesceLeaf(Page* leaf_page) {
    // 简化实现：暂不实现合并
    MINIDB_LOG("BPlusTree: coalesceLeaf not implemented");
}

void BPlusTree::coalesceInternal(Page* internal_page) {
    // 简化实现：暂不实现合并
    MINIDB_LOG("BPlusTree: coalesceInternal not implemented");
}

void BPlusTree::redistributeLeaf(Page* leaf_page) {
    // 简化实现：暂不实现重新分配
    MINIDB_LOG("BPlusTree: redistributeLeaf not implemented");
}

void BPlusTree::redistributeInternal(Page* internal_page) {
    // 简化实现：暂不实现重新分配
    MINIDB_LOG("BPlusTree: redistributeInternal not implemented");
}

page_id_t BPlusTree::findSibling(Page* page) {
    // 简化实现
    return INVALID_PAGE_ID;
}

void BPlusTree::updateRootPageId(page_id_t new_root_page_id) {
    root_page_id_ = new_root_page_id;
}

}  // namespace minidb
