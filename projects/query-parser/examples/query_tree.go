// Command querytree visualizes query trees as ASCII art.
//
// This example demonstrates how different query types are represented
// as tree structures, making it easier to understand the parsed output.
//
// Usage:
//
//	go run examples/query_tree.go
//
// Key concepts demonstrated:
//   - Query tree structure
//   - AST representation
//   - Tree visualization
package main

import (
	"fmt"

	"query-parser/src"
)

func main() {
	fmt.Println("=== Query Tree Visualization ===")
	fmt.Println()

	queries := []struct {
		name  string
		query string
	}{
		{"Simple Term", "golang"},
		{"Boolean AND", "golang AND python"},
		{"Boolean OR", "golang OR python"},
		{"Nested Boolean", "golang AND (python OR java)"},
		{"Phrase Query", `"web framework"`},
		{"Fuzzy Query", "golan~"},
		{"Wildcard Query", "go*"},
		{"Range Query", "price:[10 TO 100]"},
		{"Complex Query", "golang AND (web OR \"web framework\")~1"},
		{"Boosted Query", "golang^2.0"},
		{"NOT Query", "NOT python"},
		{"Deep Nesting", "((a AND b) OR (c AND d)) AND e"},
	}

	for _, q := range queries {
		fmt.Printf("--- %s ---\n", q.name)
		fmt.Printf("Input:  %q\n", q.query)

		parser := queryparser.NewParser(q.query)
		tree, err := parser.Parse()
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			fmt.Println()
			continue
		}

		// Print the tree visualization
		fmt.Println("Output:")
		printTree(tree, "    ")
		fmt.Println()
	}
}

// printTree prints the query tree in a compact format.
func printTree(tree *queryparser.QueryTree, indent string) {
	if tree == nil || tree.Root == nil {
		fmt.Printf("%s(empty)\n", indent)
		return
	}

	// We use the tree's String() method which already provides ASCII art
	// But we add our own formatting
	fmt.Println(indent + "[" + tree.Root.Type.String() + "] " + formatNodeValue(tree.Root))

	for i, child := range tree.Root.Children {
		if i == len(tree.Root.Children)-1 {
			fmt.Println(indent + "    └── " + formatChildTree(child, indent+"        "))
		} else {
			fmt.Println(indent + "    ├── " + formatChildTree(child, indent+"        "))
		}
	}
}

func formatNodeValue(node *queryparser.QueryNode) string {
	if node.Value == "" {
		return ""
	}

	switch node.Type {
	case queryparser.NodeBoolean:
		return node.Operator.String()
	case queryparser.NodeFuzzy:
		return fmt.Sprintf("%q~%d", node.Value, node.FuzzyDist)
	case queryparser.NodeRange:
		return fmt.Sprintf("[%s TO %s]", node.LowerBound, node.UpperBound)
	case queryparser.NodePhrase:
		return fmt.Sprintf("phrase(%q)", node.Value)
	case queryparser.NodeTerm, queryparser.NodeWildcard:
		return fmt.Sprintf("%q", node.Value)
	case queryparser.NodeBoosted:
		return fmt.Sprintf("%q^%.1f", node.Value, node.Boost)
	default:
		return fmt.Sprintf("%q", node.Value)
	}
}

func formatChildTree(node *queryparser.QueryNode, indent string) string {
	if node == nil {
		return "(nil)"
	}

	var result string
	result += "[" + node.Type.String() + "] "

	switch node.Type {
	case queryparser.NodeBoolean:
		result += node.Operator.String()
	case queryparser.NodeFuzzy:
		result += fmt.Sprintf("%q~%d", node.Value, node.FuzzyDist)
	case queryparser.NodeRange:
		result += fmt.Sprintf("[%s TO %s]", node.LowerBound, node.UpperBound)
	case queryparser.NodePhrase:
		result += fmt.Sprintf("phrase(%q)", node.Value)
	case queryparser.NodeTerm, queryparser.NodeWildcard:
		result += fmt.Sprintf("%q", node.Value)
	case queryparser.NodeBoosted:
		result += fmt.Sprintf("%q^%.1f", node.Value, node.Boost)
	default:
		result += fmt.Sprintf("%q", node.Value)
	}

	if node.Boost != 1.0 && node.Type != queryparser.NodeBoosted {
		result += fmt.Sprintf("^%.1f", node.Boost)
	}

	// Show children
	if len(node.Children) > 0 {
		result += "\n" + indent
		for i, child := range node.Children {
			prefix := "├── "
			if i == len(node.Children)-1 {
				prefix = "└── "
			}
			result += prefix + "[" + child.Type.String() + "] "
			if child.Value != "" {
				result += fmt.Sprintf("%q", child.Value)
			}
			if child.Boost != 1.0 {
				result += fmt.Sprintf("^%.1f", child.Boost)
			}
			if len(child.Children) > 0 {
				result += "\n" + indent + "    "
				for j, gc := range child.Children {
					gpfx := "├── "
					if j == len(child.Children)-1 {
						gpfx = "└── "
					}
					result += gpfx + "[" + gc.Type.String() + "] "
					if gc.Value != "" {
						result += fmt.Sprintf("%q", gc.Value)
					}
					result += "\n" + indent + "        "
				}
			}
			if i < len(node.Children)-1 {
				result += "\n" + indent
			}
		}
	}

	return result
}
