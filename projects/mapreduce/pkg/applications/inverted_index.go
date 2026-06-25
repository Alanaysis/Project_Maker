package applications

import (
	"fmt"
	"sort"
	"strings"

	"mapreduce/internal/mapreduce"
)

// InvertedIndexMap 是倒排索引的 Map 函数。
// 将文档中的单词映射到文档 ID。
//
// 输入: (文件名, 文件内容)
// 输出: [(word1, filename), (word2, filename), ...]
//
// 示例:
//
//	Input: ("doc1.txt", "hello world")
//	Output: [("hello", "doc1.txt"), ("world", "doc1.txt")]
func InvertedIndexMap(filename string, contents string) []mapreduce.KeyValue {
	// 按空白字符分割
	words := strings.Fields(contents)

	// 使用 map 去重（同一文档中同一单词只记录一次）
	wordSet := make(map[string]bool)
	for _, w := range words {
		w = strings.ToLower(w)
		w = strings.Trim(w, ".,;:!?\"'()[]{}<>")
		if w != "" {
			wordSet[w] = true
		}
	}

	// 创建键值对
	kvs := make([]mapreduce.KeyValue, 0, len(wordSet))
	for w := range wordSet {
		kvs = append(kvs, mapreduce.KeyValue{Key: w, Value: filename})
	}

	return kvs
}

// InvertedIndexReduce 是倒排索引的 Reduce 函数。
// 将同一单词出现的所有文档合并为一个列表。
//
// 输入: (word, [filename1, filename2, ...])
// 输出: "filename1,filename2,..."
//
// 示例:
//
//	Input: ("hello", ["doc1.txt", "doc2.txt", "doc1.txt"])
//	Output: "doc1.txt,doc2.txt"
func InvertedIndexReduce(key string, values []string) string {
	// 去重并排序
	fileSet := make(map[string]bool)
	for _, v := range values {
		fileSet[v] = true
	}

	// 转换为切片并排序
	files := make([]string, 0, len(fileSet))
	for f := range fileSet {
		files = append(files, f)
	}
	sort.Strings(files)

	// 返回文档数量和文档列表
	return fmt.Sprintf("%d %s", len(files), strings.Join(files, ","))
}
