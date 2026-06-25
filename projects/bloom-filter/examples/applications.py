"""
布隆过滤器实际应用示例

展示布隆过滤器在实际场景中的应用:
1. URL 去重
2. 垃圾邮件过滤
3. 数据库查询优化
4. 缓存穿透防护
"""

import sys
import os
import random
import string
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bloom_filter import BloomFilter, CountingBloomFilter, ScalableBloomFilter


def example_url_deduplication():
    """URL 去重示例"""
    print("=" * 60)
    print("1. URL 去重")
    print("=" * 60)

    # 模拟爬虫场景
    url_filter = BloomFilter(expected_items=1000000, false_positive_rate=0.01)

    # 生成模拟 URL
    domains = ["example.com", "test.org", "demo.net", "sample.io"]
    paths = ["/page", "/article", "/post", "/news", "/blog"]

    urls = []
    for _ in range(10000):
        domain = random.choice(domains)
        path = random.choice(paths)
        page = random.randint(1, 100)
        urls.append(f"https://{domain}{path}/{page}")

    # 添加一些重复 URL
    urls.extend(urls[:1000])

    # 去重
    unique_urls = []
    duplicates = 0

    start = time.perf_counter()
    for url in urls:
        if url not in url_filter:
            url_filter.add(url)
            unique_urls.append(url)
        else:
            duplicates += 1
    elapsed = time.perf_counter() - start

    print(f"\n结果:")
    print(f"  总 URL 数量: {len(urls)}")
    print(f"  去重后数量: {len(unique_urls)}")
    print(f"  检测到重复: {duplicates}")
    print(f"  处理时间: {elapsed:.4f} 秒")
    print(f"  处理速度: {len(urls) / elapsed:.0f} URL/秒")
    print(f"  内存使用: {url_filter.memory_usage()['bit_array_mb']:.2f} MB")


def example_spam_filter():
    """垃圾邮件过滤示例"""
    print("\n" + "=" * 60)
    print("2. 垃圾邮件过滤")
    print("=" * 60)

    # 垃圾邮件关键词
    spam_keywords = [
        "viagra", "cialis", "lottery", "winner", "prize",
        "click here", "free money", "earn fast", "act now",
        "limited time", "exclusive offer", "no obligation",
        "weight loss", "diet pills", "enlargement",
    ]

    # 正常邮件关键词
    normal_keywords = [
        "meeting", "project", "deadline", "report", "team",
        "schedule", "update", "review", "feedback", "discussion",
        "agenda", "minutes", "budget", "proposal", "presentation",
    ]

    # 创建垃圾邮件过滤器
    spam_filter = BloomFilter(expected_items=10000, false_positive_rate=0.001)

    # 添加垃圾邮件关键词
    for keyword in spam_keywords:
        spam_filter.add(keyword)

    # 测试邮件
    test_emails = [
        ("Win a free lottery ticket! Click here now!", True),
        ("Meeting tomorrow at 3pm to discuss the project", False),
        ("You are the winner of our exclusive prize!", True),
        ("Please review the attached report and provide feedback", False),
        ("Limited time offer: earn fast money!", True),
        ("Team schedule update for next week", False),
        ("Free viagra and diet pills!", True),
        ("Budget proposal for Q4", False),
        ("Act now to claim your prize!", True),
        ("Discussion agenda for tomorrow's meeting", False),
    ]

    print(f"\n垃圾邮件关键词: {len(spam_keywords)} 个")
    print(f"过滤器误判率: {spam_filter.estimated_false_positive_rate():.6f}")

    print(f"\n邮件分类结果:")
    correct = 0
    for email, expected_spam in test_emails:
        words = email.lower().split()
        is_spam = any(word in spam_filter for word in words)
        status = "SPAM" if is_spam else "CLEAN"
        expected = "SPAM" if expected_spam else "CLEAN"
        match = "✓" if is_spam == expected_spam else "✗"

        if is_spam == expected_spam:
            correct += 1

        print(f"  [{status}] {match} {email[:50]}...")

    accuracy = correct / len(test_emails) * 100
    print(f"\n准确率: {accuracy:.1f}%")


def example_database_query_optimization():
    """数据库查询优化示例"""
    print("\n" + "=" * 60)
    print("3. 数据库查询优化")
    print("=" * 60)

    # 模拟数据库
    db_size = 100000
    db_keys = set(f"user_{i}" for i in range(db_size))

    # 创建布隆过滤器
    db_filter = BloomFilter(expected_items=db_size, false_positive_rate=0.01)

    # 将数据库键添加到过滤器
    start = time.perf_counter()
    for key in db_keys:
        db_filter.add(key)
    build_time = time.perf_counter() - start

    # 模拟查询
    query_count = 10000
    existing_queries = [f"user_{random.randint(0, db_size - 1)}" for _ in range(query_count // 2)]
    non_existing_queries = [f"user_{random.randint(db_size, db_size * 2)}" for _ in range(query_count // 2)]
    all_queries = existing_queries + non_existing_queries
    random.shuffle(all_queries)

    # 使用布隆过滤器优化查询
    bloom_hits = 0
    bloom_misses = 0
    db_queries = 0

    start = time.perf_counter()
    for query in all_queries:
        if query in db_filter:
            bloom_hits += 1
            db_queries += 1
            # 实际查询数据库
            _ = query in db_keys
        else:
            bloom_misses += 1
            # 跳过数据库查询
    optimized_time = time.perf_counter() - start

    # 不使用布隆过滤器的查询
    db_queries_direct = 0
    start = time.perf_counter()
    for query in all_queries:
        _ = query in db_keys
        db_queries_direct += 1
    direct_time = time.perf_counter() - start

    print(f"\n数据库大小: {db_size:,} 条记录")
    print(f"查询数量: {query_count:,}")
    print(f"过滤器构建时间: {build_time:.4f} 秒")

    print(f"\n使用布隆过滤器:")
    print(f"  过滤器命中: {bloom_hits:,}")
    print(f"  过滤器未命中: {bloom_misses:,}")
    print(f"  实际数据库查询: {db_queries:,}")
    print(f"  查询时间: {optimized_time:.4f} 秒")

    print(f"\n不使用布隆过滤器:")
    print(f"  数据库查询: {db_queries_direct:,}")
    print(f"  查询时间: {direct_time:.4f} 秒")

    print(f"\n性能提升: {direct_time / optimized_time:.2f}x")


def example_cache_penetration():
    """缓存穿透防护示例"""
    print("\n" + "=" * 60)
    print("4. 缓存穿透防护")
    print("=" * 60)

    # 模拟缓存
    cache = {}
    cache_hits = 0
    cache_misses = 0

    # 模拟数据库
    db = {f"key_{i}": f"value_{i}" for i in range(10000)}

    # 布隆过滤器
    bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
    for key in db:
        bf.add(key)

    # 模拟查询 (包含大量不存在的键)
    queries = [f"key_{random.randint(0, 15000)}" for _ in range(10000)]

    db_queries = 0
    blocked = 0

    start = time.perf_counter()
    for query in queries:
        # 先检查布隆过滤器
        if query not in bf:
            # 一定不存在，直接返回
            blocked += 1
            continue

        # 可能存在，检查缓存
        if query in cache:
            cache_hits += 1
            continue

        # 缓存未命中，查询数据库
        cache_misses += 1
        db_queries += 1
        if query in db:
            cache[query] = db[query]
    elapsed = time.perf_counter() - start

    print(f"\n查询统计:")
    print(f"  总查询: {len(queries)}")
    print(f"  布隆过滤器拦截: {blocked}")
    print(f"  缓存命中: {cache_hits}")
    print(f"  缓存未命中: {cache_misses}")
    print(f"  数据库查询: {db_queries}")
    print(f"  处理时间: {elapsed:.4f} 秒")

    print(f"\n防护效果:")
    print(f"  数据库查询减少: {(1 - db_queries / len(queries)) * 100:.1f}%")


def example_membership_testing():
    """集合成员测试示例"""
    print("\n" + "=" * 60)
    print("5. 集合成员测试")
    print("=" * 60)

    # 创建两个集合
    set_a = {f"a_{i}" for i in range(1000)}
    set_b = {f"b_{i}" for i in range(1000)}
    set_c = {f"a_{i}" for i in range(500)}  # set_a 的子集

    # 创建布隆过滤器
    bf_a = BloomFilter(expected_items=1000, false_positive_rate=0.01)
    bf_b = BloomFilter(expected_items=1000, false_positive_rate=0.01)
    bf_c = BloomFilter(expected_items=1000, false_positive_rate=0.01)

    for item in set_a:
        bf_a.add(item)
    for item in set_b:
        bf_b.add(item)
    for item in set_c:
        bf_c.add(item)

    # 测试成员关系
    test_items = [f"a_{i}" for i in range(100)] + [f"b_{i}" for i in range(100)]

    print(f"\n集合 A: {len(set_a)} 个元素")
    print(f"集合 B: {len(set_b)} 个元素")
    print(f"集合 C: {len(set_c)} 个元素 (A 的子集)")

    print(f"\n成员测试结果:")
    for item in test_items[:10]:
        in_a = item in bf_a
        in_b = item in bf_b
        in_c = item in bf_c
        print(f"  {item}: A={in_a}, B={in_b}, C={in_c}")


def main():
    """主函数"""
    print("布隆过滤器实际应用示例")
    print("=" * 60)

    example_url_deduplication()
    example_spam_filter()
    example_database_query_optimization()
    example_cache_penetration()
    example_membership_testing()

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
