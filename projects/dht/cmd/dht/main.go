package main

import (
	"fmt"
	"log"

	"github.com/dht-chord/internal"
)

func main() {
	fmt.Println("=== Chord DHT Demo ===")
	fmt.Println()

	// 创建 Chord 环
	ring := internal.NewRing(nil)

	// 添加节点
	nodes := []string{
		"node1:8000",
		"node2:8001",
		"node3:8002",
		"node4:8003",
		"node5:8004",
	}

	fmt.Println("1. Adding nodes to the ring...")
	for _, addr := range nodes {
		node, err := ring.AddNode(addr)
		if err != nil {
			log.Printf("Failed to add node %s: %v", addr, err)
			continue
		}
		fmt.Printf("   Added node: %s (ID: %s)\n", addr, internal.FormatID(node.ID))
	}
	fmt.Println()

	// 打印环结构
	fmt.Println("2. Ring structure:")
	ring.PrintRing()
	fmt.Println()

	// 存储键值对
	fmt.Println("3. Storing key-value pairs...")
	testData := map[string]string{
		"name":    "Chord DHT",
		"version": "1.0.0",
		"lang":    "Go",
		"author":  "Student",
		"topic":   "distributed-systems",
	}

	for key, value := range testData {
		err := ring.Put(key, value)
		if err != nil {
			log.Printf("Failed to store key %s: %v", key, err)
			continue
		}
		node := ring.FindNode(key)
		fmt.Printf("   Stored '%s' = '%s' on node %s\n", key, value, internal.FormatID(node.ID))
	}
	fmt.Println()

	// 读取键值对
	fmt.Println("4. Retrieving key-value pairs...")
	for key := range testData {
		value, err := ring.Get(key)
		if err != nil {
			log.Printf("Failed to get key %s: %v", key, err)
			continue
		}
		fmt.Printf("   Got '%s' = '%s'\n", key, value)
	}
	fmt.Println()

	// 删除键值对
	fmt.Println("5. Deleting key 'lang'...")
	err := ring.Delete("lang")
	if err != nil {
		log.Printf("Failed to delete key: %v", err)
	} else {
		fmt.Println("   Successfully deleted 'lang'")
	}
	fmt.Println()

	// 验证删除
	fmt.Println("6. Verifying deletion...")
	_, err = ring.Get("lang")
	if err != nil {
		fmt.Println("   Key 'lang' not found (expected)")
	} else {
		fmt.Println("   Key 'lang' still exists (unexpected)")
	}
	fmt.Println()

	// 显示节点存储情况
	fmt.Println("7. Node storage status:")
	for _, node := range ring.GetNodes() {
		fmt.Printf("   Node %s: ", internal.FormatID(node.ID))
		// 这里需要获取节点的存储内容
		// 简化起见，只显示节点存在
		fmt.Println("active")
	}
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
}
