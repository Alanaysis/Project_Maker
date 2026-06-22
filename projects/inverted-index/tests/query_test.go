package tests

import (
	"testing"

	"github.com/copyninja/inverted-index/internal/query"
)

func TestParseQueryAND(t *testing.T) {
	q := query.ParseQuery("hello world")
	if q.Operator != query.OpAND {
		t.Errorf("expected AND operator, got %v", q.Operator)
	}
	if len(q.Terms) != 2 {
		t.Errorf("expected 2 terms, got %d", len(q.Terms))
	}
}

func TestParseQueryOR(t *testing.T) {
	q := query.ParseQuery("hello OR world")
	if q.Operator != query.OpOR {
		t.Errorf("expected OR operator, got %v", q.Operator)
	}
	if len(q.Terms) != 2 {
		t.Errorf("expected 2 terms, got %d", len(q.Terms))
	}
}

func TestParseQueryNOT(t *testing.T) {
	q := query.ParseQuery("NOT hello")
	if q.Operator != query.OpNOT {
		t.Errorf("expected NOT operator, got %v", q.Operator)
	}
	if len(q.Terms) != 1 {
		t.Errorf("expected 1 term, got %d", len(q.Terms))
	}
}

func TestParseQueryExplicitAND(t *testing.T) {
	q := query.ParseQuery("hello AND world")
	if q.Operator != query.OpAND {
		t.Errorf("expected AND operator, got %v", q.Operator)
	}
	if len(q.Terms) != 2 {
		t.Errorf("expected 2 terms, got %d", len(q.Terms))
	}
}

func TestParseQueryEmpty(t *testing.T) {
	q := query.ParseQuery("")
	if q.Operator != query.OpAND {
		t.Errorf("expected AND operator for empty query, got %v", q.Operator)
	}
	if len(q.Terms) != 0 {
		t.Errorf("expected 0 terms, got %d", len(q.Terms))
	}
}

func TestParseQueryMultipleOR(t *testing.T) {
	q := query.ParseQuery("go OR python OR rust")
	if q.Operator != query.OpOR {
		t.Errorf("expected OR operator, got %v", q.Operator)
	}
	if len(q.Terms) != 3 {
		t.Errorf("expected 3 terms, got %d", len(q.Terms))
	}
}

func TestParseQueryCaseInsensitive(t *testing.T) {
	q := query.ParseQuery("Hello OR World")
	if q.Operator != query.OpOR {
		t.Errorf("expected OR operator, got %v", q.Operator)
	}
	if q.Terms[0] != "hello" || q.Terms[1] != "world" {
		t.Errorf("expected lowercase terms, got %v", q.Terms)
	}
}
