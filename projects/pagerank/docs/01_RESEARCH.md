# 01 - PageRank 算法研究

## 1. 算法背景

### 1.1 历史背景

PageRank 算法由 Google 创始人 Larry Page 和 Sergey Brin 于 1998 年在斯坦福大学开发，是 Google 搜索引擎的核心算法之一。

**关键里程碑：**
- 1998 年：PageRank 论文发表
- 1998 年：Google 公司成立
- 2000 年：PageRank 成为 Google 搜索核心
- 2005 年：Topic-Sensitive PageRank 提出

### 1.2 核心思想

PageRank 的核心思想是：**一个页面的重要性取决于链接到它的页面的重要性**。

类比学术引用：
- 被高引用论文引用的论文更有价值
- 被权威期刊收录的文章更可信

## 2. 数学基础

### 2.1 马尔可夫链

PageRank 基于随机游走模型，可以建模为马尔可夫链：

- **状态空间**: 网页集合
- **转移概率**: 从一个页面点击链接跳转到另一个页面的概率
- **平稳分布**: 长期访问概率分布 = PageRank 值

### 2.2 标准 PageRank 公式

```
PR(i) = (1-d)/N + d * Σ_{j∈In(i)} PR(j)/L(j)
```

其中：
- `d`: 阻尼因子 (通常 0.85)
- `N`: 网页总数
- `In(i)`: 链接到页面 i 的页面集合
- `L(j)`: 页面 j 的出链数

### 2.3 矩阵形式

```
PR = (1-d)/N * e + d * M * PR
```

其中：
- `PR`: PageRank 向量
- `M`: 列随机转移矩阵
- `e`: 全 1 向量

### 2.4 Google 矩阵

```
G = d * M + (1-d)/N * E
```

其中 `E` 是全 1 矩阵。PageRank 是 G 的主特征向量。

## 3. 算法变体

### 3.1 个性化 PageRank (PPR)

**动机**: 不同用户有不同的兴趣偏好

**公式**:
```
PR(i) = (1-d) * p(i) + d * Σ PR(j)/L(j)
```

其中 `p(i)` 是个性化偏好向量。

**应用**:
- 个性化搜索结果
- 社交推荐
- 目标网页发现

### 3.2 Topic-Sensitive PageRank (TSPR)

**动机**: 网页在不同主题下有不同的重要性

**方法**:
1. 为每个主题定义种子页面集合
2. 计算每个主题的 PageRank 向量
3. 根据查询主题组合 PageRank 向量

**优势**:
- 更精确的主题相关排名
- 减少主题漂移
- 提高搜索质量

### 3.3 BlockRank

**动机**: 利用网页的层级结构加速计算

**方法**:
1. 将网页按域名分块
2. 计算块级别的 PageRank
3. 在块内计算局部 PageRank

## 4. 收敛性分析

### 4.1 收敛条件

PageRank 算法收敛的充分条件：
1. 转移矩阵是随机矩阵
2. 阻尼因子 d < 1
3. 处理悬挂节点（无出链页面）

### 4.2 收敛速度

收敛速度由转移矩阵的次主导特征值决定：

```
|λ_2| ≤ d
```

- d = 0.85 时，约需 50-100 次迭代收敛
- d 越大，收敛越慢但结果越精确

### 4.3 收敛判定

常用收敛判定标准：
- L1 范数: `||PR_new - PR_old||_1 < ε`
- L2 范数: `||PR_new - PR_old||_2 < ε`
- 相对变化: `||PR_new - PR_old|| / ||PR_old|| < ε`

## 5. 算法优化

### 5.1 稀疏矩阵优化

网页图通常是稀疏的（每个页面只有少量链接），使用稀疏矩阵可以：
- 减少内存占用
- 加速矩阵运算
- 处理大规模图

### 5.2 块迭代法

将图分块，块内并行计算：
1. 块内迭代
2. 块间同步
3. 重复直到收敛

### 5.3 增量更新

当图结构变化时，不需要完全重新计算：
- 使用前一次结果作为初始值
- 只更新受影响的部分

## 6. 应用场景

### 6.1 搜索引擎

- 网页排名
- 搜索结果排序
- 广告排序

### 6.2 社交网络

- 用户影响力分析
- 社区发现
- 信息传播预测

### 6.3 推荐系统

- 基于图的推荐
- 协同过滤
- 知识图谱推理

### 6.4 其他应用

- 生物网络分析
- 引用网络分析
- 交通网络优化

## 7. 相关算法

### 7.1 HITS 算法

- Hub 和 Authority 双重排名
- 与查询相关
- 计算成本较高

### 7.2 SALSA 算法

- 结合 PageRank 和 HITS
- 随机游走模型
- 更稳定的排名

### 7.3 SimRank

- 基于图结构的相似度
- 递归定义
- 适用于推荐系统

## 8. 研究方向

### 8.1 当前研究热点

1. **动态图 PageRank**: 实时更新
2. **分布式 PageRank**: 大规模并行计算
3. **个性化 PageRank**: 更精确的用户建模
4. **多关系 PageRank**: 异构图上的 PageRank

### 8.2 开放问题

1. 如何选择最优阻尼因子？
2. 如何处理动态变化的图？
3. 如何提高个性化 PageRank 的效率？
4. 如何在隐私保护下计算 PageRank？

## 9. 参考文献

1. Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). The PageRank citation ranking: Bringing order to the web.
2. Haveliwala, T. H. (2003). Topic-sensitive PageRank: A context-sensitive ranking algorithm for web search.
3. Jeh, G., & Widom, J. (2003). Scaling personalized web search.
4. Berkhin, P. (2005). A survey on PageRank computing.
5. Langville, A. N., & Meyer, C. D. (2006). Google's PageRank and beyond.
