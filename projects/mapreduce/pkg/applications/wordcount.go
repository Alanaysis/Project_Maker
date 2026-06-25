// Package applications 提供了 MapReduce 的应用示例。
// 包括词频统计、倒排索引、日志分析等经典场景。
package applications

import (
	"strconv"
	"strings"

	"mapreduce/internal/mapreduce"
)

// WordCountMap 是词频统计的 Map 函数。
// 将文本分割为单词，输出 (word, "1") 键值对。
//
// 输入: (文件名, 文件内容)
// 输出: [(word1, "1"), (word2, "1"), ...]
//
// 示例:
//
//	Input: "hello world hello"
//	Output: [("hello", "1"), ("world", "1"), ("hello", "1")]
func WordCountMap(filename string, contents string) []mapreduce.KeyValue {
	// 按空白字符分割
	words := strings.Fields(contents)

	// 创建键值对
	kvs := make([]mapreduce.KeyValue, 0, len(words))
	for _, w := range words {
		// 转换为小写
		w = strings.ToLower(w)
		// 移除标点符号
		w = strings.Trim(w, ".,;:!?\"'()[]{}<>")
		if w != "" {
			kvs = append(kvs, mapreduce.KeyValue{Key: w, Value: "1"})
		}
	}

	return kvs
}

// WordCountReduce 是词频统计的 Reduce 函数。
// 统计每个单词出现的次数。
//
// 输入: (word, ["1", "1", ...])
// 输出: "count"
//
// 示例:
//
//	Input: ("hello", ["1", "1", "1"])
//	Output: "3"
func WordCountReduce(key string, values []string) string {
	// 统计出现次数
	return strconv.Itoa(len(values))
}
