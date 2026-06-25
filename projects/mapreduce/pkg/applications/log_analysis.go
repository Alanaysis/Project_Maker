package applications

import (
	"regexp"
	"strconv"
	"strings"

	"mapreduce/internal/mapreduce"
)

// 日志格式正则表达式
// 示例: 192.168.1.1 - - [15/Jan/2024:10:30:00 +0800] "GET /api/users HTTP/1.1" 200 1234
var logRegex = regexp.MustCompile(`^(\S+) \S+ \S+ \[.*?\] "(\S+) (\S+) \S+" (\d+) \d+$`)

// LogEntry 表示解析后的日志条目
type LogEntry struct {
	IP       string
	Method   string
	Path     string
	Status   string
}

// LogAnalysisMap 是日志分析的 Map 函数。
// 解析 Web 服务器日志，提取 URL 和访问状态。
//
// 输入: (文件名, 日志内容)
// 输出: [(url, "1"), (url, "1"), ...]
//
// 示例:
//
//	Input: "192.168.1.1 - - [...] "GET /api/users HTTP/1.1" 200 1234"
//	Output: [("/api/users", "1")]
func LogAnalysisMap(filename string, contents string) []mapreduce.KeyValue {
	lines := strings.Split(contents, "\n")

	var kvs []mapreduce.KeyValue
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// 解析日志行
		matches := logRegex.FindStringSubmatch(line)
		if matches == nil {
			continue
		}

		method := matches[2]
		path := matches[3]
		status := matches[4]

		// 输出 URL 访问次数
		kvs = append(kvs, mapreduce.KeyValue{Key: path, Value: "1"})

		// 输出状态码统计
		kvs = append(kvs, mapreduce.KeyValue{Key: "status:" + status, Value: "1"})

		// 输出方法统计
		kvs = append(kvs, mapreduce.KeyValue{Key: "method:" + method, Value: "1"})
	}

	return kvs
}

// LogAnalysisReduce 是日志分析的 Reduce 函数。
// 统计每个 URL/状态码/方法的访问次数。
//
// 输入: (key, ["1", "1", ...])
// 输出: "count"
//
// 示例:
//
//	Input: ("/api/users", ["1", "1", "1"])
//	Output: "3"
func LogAnalysisReduce(key string, values []string) string {
	return strconv.Itoa(len(values))
}

// SlowQueryMap 是慢查询分析的 Map 函数。
// 识别响应时间超过阈值的请求。
//
// 输入: (文件名, 日志内容)
// 输出: [(url, response_time), ...] 仅包含慢查询
func SlowQueryMap(filename string, contents string) []mapreduce.KeyValue {
	// 慢查询阈值: 1000ms
	slowThreshold := 1000

	lines := strings.Split(contents, "\n")

	var kvs []mapreduce.KeyValue
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// 解析日志行
		matches := logRegex.FindStringSubmatch(line)
		if matches == nil {
			continue
		}

		path := matches[3]

		// 提取响应时间 (假设在日志末尾)
		parts := strings.Fields(line)
		if len(parts) < 2 {
			continue
		}

		// 尝试解析响应时间
		responseTime, err := strconv.Atoi(parts[len(parts)-1])
		if err != nil {
			continue
		}

		// 仅输出慢查询
		if responseTime > slowThreshold {
			kvs = append(kvs, mapreduce.KeyValue{
				Key:   path,
				Value: strconv.Itoa(responseTime),
			})
		}
	}

	return kvs
}

// SlowQueryReduce 是慢查询分析的 Reduce 函数。
// 计算每个 URL 的平均响应时间。
func SlowQueryReduce(key string, values []string) string {
	if len(values) == 0 {
		return "0"
	}

	total := 0
	for _, v := range values {
		t, err := strconv.Atoi(v)
		if err != nil {
			continue
		}
		total += t
	}

	avg := total / len(values)
	return strconv.Itoa(avg)
}
