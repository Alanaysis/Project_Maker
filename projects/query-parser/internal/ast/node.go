package ast

// NodeType represents the type of AST node
type NodeType int

const (
	NodeTerm     NodeType = iota // Single term: "hello"
	NodePhrase                   // Phrase query: "hello world"
	NodeAnd                      // AND operation: a AND b
	NodeOr                       // OR operation: a OR b
	NodeNot                      // NOT operation: NOT a
)

// Node represents an AST node in the query tree
type Node struct {
	Type     NodeType
	Value    string  // For term/phrase nodes
	Left     *Node   // For binary operations
	Right    *Node   // For binary operations
	Children []*Node // For NOT (single child)
}

// NewTerm creates a term node
func NewTerm(value string) *Node {
	return &Node{
		Type:  NodeTerm,
		Value: value,
	}
}

// NewPhrase creates a phrase node
func NewPhrase(value string) *Node {
	return &Node{
		Type:  NodePhrase,
		Value: value,
	}
}

// NewAnd creates an AND node
func NewAnd(left, right *Node) *Node {
	return &Node{
		Type:  NodeAnd,
		Left:  left,
		Right: right,
	}
}

// NewOr creates an OR node
func NewOr(left, right *Node) *Node {
	return &Node{
		Type:  NodeOr,
		Left:  left,
		Right: right,
	}
}

// NewNot creates a NOT node
func NewNot(child *Node) *Node {
	return &Node{
		Type:     NodeNot,
		Children: []*Node{child},
	}
}

// String returns a string representation of the node
func (n *Node) String() string {
	switch n.Type {
	case NodeTerm:
		return n.Value
	case NodePhrase:
		return `"` + n.Value + `"`
	case NodeAnd:
		return "(" + n.Left.String() + " AND " + n.Right.String() + ")"
	case NodeOr:
		return "(" + n.Left.String() + " OR " + n.Right.String() + ")"
	case NodeNot:
		return "(NOT " + n.Children[0].String() + ")"
	default:
		return "unknown"
	}
}

// CollectTerms extracts all terms and phrases from the AST
func (n *Node) CollectTerms() []string {
	var terms []string
	collectTermsRecursive(n, &terms)
	return terms
}

func collectTermsRecursive(n *Node, terms *[]string) {
	if n == nil {
		return
	}
	switch n.Type {
	case NodeTerm, NodePhrase:
		*terms = append(*terms, n.Value)
	case NodeAnd, NodeOr:
		collectTermsRecursive(n.Left, terms)
		collectTermsRecursive(n.Right, terms)
	case NodeNot:
		for _, child := range n.Children {
			collectTermsRecursive(child, terms)
		}
	}
}
