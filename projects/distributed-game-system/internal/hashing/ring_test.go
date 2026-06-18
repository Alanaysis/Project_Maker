package hashing

import (
	"fmt"
	"testing"
)

func TestHashRingAddNode(t *testing.T) {
	ring := NewHashRing(100)

	ring.AddNode("server-1")
	if ring.GetNodeCount() != 1 {
		t.Errorf("Node count = %d, want 1", ring.GetNodeCount())
	}
}

func TestHashRingRemoveNode(t *testing.T) {
	ring := NewHashRing(100)

	ring.AddNode("server-1")
	ring.AddNode("server-2")

	ring.RemoveNode("server-1")
	if ring.GetNodeCount() != 1 {
		t.Errorf("Node count = %d, want 1", ring.GetNodeCount())
	}
}

func TestHashRingGetNode(t *testing.T) {
	ring := NewHashRing(100)

	ring.AddNode("server-1")
	ring.AddNode("server-2")
	ring.AddNode("server-3")

	// 查找节点
	node, err := ring.GetNode("player-1")
	if err != nil {
		t.Fatalf("GetNode failed: %v", err)
	}

	if node == "" {
		t.Error("GetNode returned empty string")
	}

	t.Logf("player-1 -> %s", node)
}

func TestHashRingConsistency(t *testing.T) {
	ring := NewHashRing(100)

	ring.AddNode("server-1")
	ring.AddNode("server-2")
	ring.AddNode("server-3")

	// 同一个键应该总是返回同一个节点
	node1, _ := ring.GetNode("player-1")
	node2, _ := ring.GetNode("player-1")

	if node1 != node2 {
		t.Errorf("Inconsistent: %s != %s", node1, node2)
	}
}

func TestHashRingDistribution(t *testing.T) {
	ring := NewHashRing(100)

	ring.AddNode("server-1")
	ring.AddNode("server-2")
	ring.AddNode("server-3")

	// 检查分布
	dist := ring.GetDistribution(10000)

	t.Logf("Distribution:")
	for node, count := range dist {
		t.Logf("  %s: %d (%.1f%%)", node, count, float64(count)/100)
	}

	// 检查是否相对均匀（允许 20% 偏差）
	expected := 10000 / 3
	for node, count := range dist {
		diff := count - expected
		if diff < 0 {
			diff = -diff
		}
		if float64(diff)/float64(expected) > 0.2 {
			t.Errorf("Node %s distribution too uneven: %d (expected ~%d)", node, count, expected)
		}
	}
}

func TestHashRingMinimalMovement(t *testing.T) {
	ring1 := NewHashRing(100)
	ring1.AddNode("server-1")
	ring1.AddNode("server-2")

	ring2 := NewHashRing(100)
	ring2.AddNode("server-1")
	ring2.AddNode("server-2")
	ring2.AddNode("server-3") // 添加一个新节点

	// 计算有多少键需要移动
	moved := 0
	total := 10000
	for i := 0; i < total; i++ {
		key := fmt.Sprintf("player-%d", i)
		node1, _ := ring1.GetNode(key)
		node2, _ := ring2.GetNode(key)
		if node1 != node2 {
			moved++
		}
	}

	t.Logf("Moved: %d/%d (%.1f%%)", moved, total, float64(moved)/float64(total)*100)

	// 理论上应该只有 ~33% 的键需要移动
	// 允许一些偏差
	if float64(moved)/float64(total) > 0.5 {
		t.Errorf("Too many keys moved: %.1f%% (expected < 50%%)", float64(moved)/float64(total)*100)
	}
}

func TestHashRingGetNodes(t *testing.T) {
	ring := NewHashRing(100)

	ring.AddNode("server-1")
	ring.AddNode("server-2")
	ring.AddNode("server-3")

	nodes := ring.GetNodes()
	if len(nodes) != 3 {
		t.Errorf("GetNodes returned %d nodes, want 3", len(nodes))
	}
}
