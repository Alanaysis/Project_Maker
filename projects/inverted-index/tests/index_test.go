// Package invertedindex_test contains tests for the inverted index package.
package invertedindex_test

import (
	"math"
	"sort"
	"testing"

	"inverted-index/src"
)

// ============================================================
// Tokenization Tests
// ============================================================

func TestTokenizeEnglish(t *testing.T) {
	tests := []struct {
		input    string
		wantLen  int
		wantTerm string
	}{
		{"hello world", 2, "hello"},
		{"Go is great", 3, "go"},
		{"", 0, ""},
		{"  spaced  ", 1, "spaced"},
		{"hello, world!", 2, "hello"},
	}

	for _, tt := range tests {
		tokens := invertedindex.Tokenize(tt.input)
		if len(tokens) != tt.wantLen {
			t.Errorf("Tokenize(%q) = %d tokens, want %d", tt.input, len(tokens), tt.wantLen)
		}
		if tt.wantLen > 0 && tokens[0].Text != tt.wantTerm {
			t.Errorf("Tokenize(%q)[0] = %q, want %q", tt.input, tokens[0].Text, tt.wantTerm)
		}
	}
}

func TestTokenizeChinese(t *testing.T) {
	tokens := invertedindex.Tokenize("机器学习是一种人工智能")
	if len(tokens) != 10 {
		t.Errorf("Tokenize Chinese: got %d tokens, want 10", len(tokens))
	}
}

func TestTokenizeMixed(t *testing.T) {
	tokens := invertedindex.Tokenize("Machine learning 机器学习 AI")
	if len(tokens) < 4 {
		t.Errorf("Tokenize mixed: got %d tokens, want at least 4", len(tokens))
	}
}

// ============================================================
// Index Building Tests
// ============================================================

func TestNewInvertedIndex(t *testing.T) {
	idx := invertedindex.NewInvertedIndex()
	if idx == nil {
		t.Fatal("NewInvertedIndex returned nil")
	}
	if idx.Size() != 0 {
		t.Errorf("New index size = %d, want 0", idx.Size())
	}
}

func TestIndexBuilderAddDocument(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()

	err := builder.AddDocument(1, "hello world hello")
	if err != nil {
		t.Fatalf("AddDocument(1) error: %v", err)
	}

	err = builder.AddDocument(2, "world peace")
	if err != nil {
		t.Fatalf("AddDocument(2) error: %v", err)
	}

	builder.Build()
	index := builder.GetIndex()

	if index.TotalDocCount() != 2 {
		t.Errorf("Doc count = %d, want 2", index.TotalDocCount())
	}
	if index.Size() != 3 { // hello, world, peace
		t.Errorf("Term count = %d, want 3", index.Size())
	}
}

func TestIndexBuilderEmptyDocument(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	err := builder.AddDocument(1, "")
	if err == nil {
		t.Error("Expected error for empty document, got nil")
	}
}

func TestIndexBuilderTermFrequency(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go go go python go")
	builder.AddDocument(2, "go python")
	builder.Build()

	index := builder.GetIndex()
	entry := index.GetEntry("go")

	if entry.TF[1] != 4 {
		t.Errorf("TF of 'go' in doc 1 = %d, want 4", entry.TF[1])
	}
	if entry.TF[2] != 1 {
		t.Errorf("TF of 'go' in doc 2 = %d, want 1", entry.TF[2])
	}
}

func TestIndexBuilderDocumentFrequency(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go python go")
	builder.AddDocument(2, "go rust")
	builder.AddDocument(3, "python java")
	builder.Build()

	index := builder.GetIndex()

	if index.DocumentFreq("go") != 2 {
		t.Errorf("DF of 'go' = %d, want 2", index.DocumentFreq("go"))
	}
	if index.DocumentFreq("python") != 2 {
		t.Errorf("DF of 'python' = %d, want 2", index.DocumentFreq("python"))
	}
	if index.DocumentFreq("rust") != 1 {
		t.Errorf("DF of 'rust' = %d, want 1", index.DocumentFreq("rust"))
	}
	if index.DocumentFreq("java") != 1 {
		t.Errorf("DF of 'java' = %d, want 1", index.DocumentFreq("java"))
	}
}

// ============================================================
// Postings List Tests
// ============================================================

func TestPostingsListIntersect(t *testing.T) {
	pl1 := invertedindex.NewPostingsList()
	pl1.Add(&invertedindex.Posting{DocID: 1, Positions: []int{0}})
	pl1.Add(&invertedindex.Posting{DocID: 3, Positions: []int{5}})
	pl1.Add(&invertedindex.Posting{DocID: 5, Positions: []int{10}})

	pl2 := invertedindex.NewPostingsList()
	pl2.Add(&invertedindex.Posting{DocID: 2, Positions: []int{1}})
	pl2.Add(&invertedindex.Posting{DocID: 3, Positions: []int{7}})
	pl2.Add(&invertedindex.Posting{DocID: 5, Positions: []int{12}})

	intersected := pl1.Intersect(pl2)
	if intersected.Len() != 2 {
		t.Errorf("Intersect: got %d results, want 2", intersected.Len())
	}

	// Check that the intersected docs are 3 and 5
	docIDs := make(map[int]bool)
	for _, p := range intersected.Items {
		docIDs[p.DocID] = true
	}
	if !docIDs[3] || !docIDs[5] {
		t.Errorf("Intersect: expected docs 3 and 5, got %v", docIDs)
	}
}

func TestPostingsListUnion(t *testing.T) {
	pl1 := invertedindex.NewPostingsList()
	pl1.Add(&invertedindex.Posting{DocID: 1, Positions: []int{0}})
	pl1.Add(&invertedindex.Posting{DocID: 3, Positions: []int{5}})

	pl2 := invertedindex.NewPostingsList()
	pl2.Add(&invertedindex.Posting{DocID: 2, Positions: []int{1}})
	pl2.Add(&invertedindex.Posting{DocID: 4, Positions: []int{3}})

	union := pl1.Union(pl2)
	if union.Len() != 4 {
		t.Errorf("Union: got %d results, want 4", union.Len())
	}
}

// ============================================================
// Query Parser Tests
// ============================================================

func TestQueryParserSingleTerm(t *testing.T) {
	parser := invertedindex.NewQueryParser()
	query, err := parser.Parse("search")
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}
	if query.Type != invertedindex.QueryTerm {
		t.Errorf("Query type = %v, want QueryTerm", query.Type)
	}
	if query.Term != "search" {
		t.Errorf("Query term = %q, want %q", query.Term, "search")
	}
}

func TestQueryParserAND(t *testing.T) {
	parser := invertedindex.NewQueryParser()
	query, err := parser.Parse("go AND rust")
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}
	if query.Type != invertedindex.QueryAnd {
		t.Errorf("Query type = %v, want QueryAnd", query.Type)
	}
	if len(query.Terms) != 2 {
		t.Errorf("Terms count = %d, want 2", len(query.Terms))
	}
}

func TestQueryParserOR(t *testing.T) {
	parser := invertedindex.NewQueryParser()
	query, err := parser.Parse("go OR rust")
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}
	if query.Type != invertedindex.QueryOr {
		t.Errorf("Query type = %v, want QueryOr", query.Type)
	}
}

func TestQueryParserPhrase(t *testing.T) {
	parser := invertedindex.NewQueryParser()
	query, err := parser.Parse(`"machine learning"`)
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}
	if query.Type != invertedindex.QueryPhrase {
		t.Errorf("Query type = %v, want QueryPhrase", query.Type)
	}
}

func TestQueryParserEmpty(t *testing.T) {
	parser := invertedindex.NewQueryParser()
	_, err := parser.Parse("")
	if err == nil {
		t.Error("Expected error for empty query, got nil")
	}
}

// ============================================================
// BM25 Scoring Tests
// ============================================================

func TestBM25ScoreBasic(t *testing.T) {
	cfg := invertedindex.DefaultBM25Config()
	score := invertedindex.BM25Score(5, 100, 10, 1000, 100.0, cfg)

	if score <= 0 {
		t.Errorf("BM25Score returned non-positive score: %f", score)
	}
}

func TestBM25ScoreZeroDocLen(t *testing.T) {
	cfg := invertedindex.DefaultBM25Config()
	score := invertedindex.BM25Score(5, 0, 10, 1000, 100.0, cfg)

	if score != 0 {
		t.Errorf("BM25Score with docLen=0 = %f, want 0", score)
	}
}

func TestBM25ScoreTFSaturation(t *testing.T) {
	// Higher TF should give higher score, but with diminishing returns
	cfg := invertedindex.DefaultBM25Config()
	score1 := invertedindex.BM25Score(1, 100, 10, 1000, 100.0, cfg)
	score2 := invertedindex.BM25Score(10, 100, 10, 1000, 100.0, cfg)
	score3 := invertedindex.BM25Score(100, 100, 10, 1000, 100.0, cfg)

	if score2 <= score1 {
		t.Errorf("TF saturation: score(10)=%f <= score(1)=%f", score2, score1)
	}
	if score3 <= score2 {
		t.Errorf("TF saturation: score(100)=%f <= score(10)=%f", score3, score2)
	}
	// The gain from 1->10 should be larger than 10->100
	gain1 := score2 - score1
	gain2 := score3 - score2
	if gain1 <= gain2 {
		t.Errorf("Diminishing returns: gain1=%f <= gain2=%f", gain1, gain2)
	}
}

func TestBM25DocLengthNormalization(t *testing.T) {
	// Same TF in shorter doc should score higher
	cfg := invertedindex.DefaultBM25Config()
	scoreShort := invertedindex.BM25Score(5, 50, 10, 1000, 100.0, cfg)
	scoreLong := invertedindex.BM25Score(5, 200, 10, 1000, 100.0, cfg)

	if scoreShort <= scoreLong {
		t.Errorf("Doc length norm: short=%f <= long=%f", scoreShort, scoreLong)
	}
}

func TestBM25IDFScore(t *testing.T) {
	// Rarer terms should score higher
	cfg := invertedindex.DefaultBM25Config()
	scoreCommon := invertedindex.BM25Score(1, 100, 100, 1000, 100.0, cfg)
	scoreRare := invertedindex.BM25Score(1, 100, 1, 1000, 100.0, cfg)

	if scoreRare <= scoreCommon {
		t.Errorf("IDF: rare=%f <= common=%f", scoreRare, scoreCommon)
	}
}

// ============================================================
// Search Tests
// ============================================================

func TestSearchSingleTerm(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go is great")
	builder.AddDocument(2, "python is great too")
	builder.AddDocument(3, "rust is also great")
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search("great", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}
	if len(results) != 3 {
		t.Errorf("Search results count = %d, want 3", len(results))
	}
}

func TestSearchRanked(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go go go python")
	builder.AddDocument(2, "go python")
	builder.AddDocument(3, "python python python")
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search("python", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}

	// Doc 3 has higher TF for "python", should rank higher
	if len(results) < 2 {
		t.Fatalf("Expected at least 2 results, got %d", len(results))
	}
	if results[0].DocID != 3 {
		t.Errorf("Top result docID = %d, want 3", results[0].DocID)
	}
}

func TestSearchANDQuery(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go python rust")
	builder.AddDocument(2, "go java")
	builder.AddDocument(3, "python java")
	builder.AddDocument(4, "go python")
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search("go AND python", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}

	// Only docs 1 and 4 contain both "go" and "python"
	if len(results) != 2 {
		t.Errorf("AND query results = %d, want 2", len(results))
	}
}

func TestSearchORQuery(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go is great")
	builder.AddDocument(2, "python is great")
	builder.AddDocument(3, "rust is fast")
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search("go OR rust", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}

	// Should find docs 1 and 3
	if len(results) != 2 {
		t.Errorf("OR query results = %d, want 2", len(results))
	}
}

func TestSearchPhraseQuery(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "machine learning is great")
	builder.AddDocument(2, "deep learning is also great")
	builder.AddDocument(3, "learning machine tools are different")
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search(`"machine learning"`, 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}

	// Should find docs 1 and 2 (both have "machine learning")
	if len(results) != 2 {
		t.Errorf("Phrase query results = %d, want 2", len(results))
	}
}

func TestSearchNoResults(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "hello world")
	builder.AddDocument(2, "foo bar")
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search("xyz", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}
	if len(results) != 0 {
		t.Errorf("Expected 0 results, got %d", len(results))
	}
}

func TestSearchTopK(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	for i := 0; i < 10; i++ {
		builder.AddDocument(i, "test document number")
	}
	builder.Build()

	searcher := invertedindex.NewSearcher(builder.GetIndex())
	results, err := searcher.Search("test", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}
	if len(results) != 5 {
		t.Errorf("Top-K: got %d results, want 5", len(results))
	}
}

// ============================================================
// Average Document Length Tests
// ============================================================

func TestAverageDocLen(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "hello world")          // 2 tokens
	builder.AddDocument(2, "hello world foo bar")  // 4 tokens
	builder.Build()

	avg := invertedindex.AverageDocLen(builder.GetIndex())
	expected := 3.0
	if math.Abs(avg-expected) > 1e-9 {
		t.Errorf("Average doc len = %f, want %f", avg, expected)
	}
}

// ============================================================
// Persistence Tests
// ============================================================

func TestSaveLoad(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "hello world hello")
	builder.AddDocument(2, "world peace hello")
	builder.AddDocument(3, "foo bar baz")
	builder.Build()

	original := builder.GetIndex()
	data := original.Save()

	loaded := invertedindex.Load(data)

	if loaded.TotalDocCount() != original.TotalDocCount() {
		t.Errorf("Loaded doc count = %d, want %d", loaded.TotalDocCount(), original.TotalDocCount())
	}
	if loaded.Size() != original.Size() {
		t.Errorf("Loaded term count = %d, want %d", loaded.Size(), original.Size())
	}
}

func TestPersistenceSearchConsistency(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go programming language")
	builder.AddDocument(2, "python programming language")
	builder.AddDocument(3, "rust systems programming")
	builder.Build()

	original := builder.GetIndex()
	data := original.Save()
	loaded := invertedindex.Load(data)

	searcher1 := invertedindex.NewSearcher(original)
	searcher2 := invertedindex.NewSearcher(loaded)

	results1, _ := searcher1.Search("programming", 5)
	results2, _ := searcher2.Search("programming", 5)

	if len(results1) != len(results2) {
		t.Errorf("Results count: original=%d, loaded=%d", len(results1), len(results2))
	}

	for i := range results1 {
		if results1[i].DocID != results2[i].DocID {
			t.Errorf("Result %d docID: original=%d, loaded=%d", i, results1[i].DocID, results2[i].DocID)
		}
		if mathAbs(results1[i].Score-results2[i].Score) > 1e-9 {
			t.Errorf("Result %d score: original=%f, loaded=%f", i, results1[i].Score, results2[i].Score)
		}
	}
}

// ============================================================
// Index Builder Tests
// ============================================================

func TestIndexBuilderBuildAndSearch(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "machine learning algorithms")
	builder.AddDocument(2, "deep learning neural networks")
	builder.AddDocument(3, "reinforcement learning rewards")
	builder.Build()

	results, err := builder.BuildAndSearch("learning", 5)
	if err != nil {
		t.Fatalf("BuildAndSearch error: %v", err)
	}
	if len(results) != 3 {
		t.Errorf("Results count = %d, want 3", len(results))
	}
}

// ============================================================
// Results Sorting Tests
// ============================================================

func TestResultsSorting(t *testing.T) {
	results := invertedindex.Results{
		{DocID: 1, Score: 0.5},
		{DocID: 2, Score: 0.9},
		{DocID: 3, Score: 0.3},
	}

	invertedindex.SortResults(results)

	if results[0].DocID != 2 {
		t.Errorf("Top result = doc %d, want doc 2", results[0].DocID)
	}
	if results[0].Score != 0.9 {
		t.Errorf("Top score = %f, want 0.9", results[0].Score)
	}
}

// ============================================================
// Helper
// ============================================================

func mathAbs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

// ============================================================
// Integration Tests
// ============================================================

func TestFullPipeline(t *testing.T) {
	// Complete pipeline: build index, search, verify results
	builder := invertedindex.NewIndexBuilder()

	// Add a realistic set of documents
	docs := []struct {
		id      int
		content string
	}{
		{1, "Go is a statically typed compiled programming language designed at Google"},
		{2, "Python is a dynamically typed interpreted programming language"},
		{3, "Rust is a systems programming language focused on safety and performance"},
		{4, "Java is an object-oriented programming language for enterprise applications"},
		{5, "Go and Python are both popular for web development and scripting"},
	}

	for _, doc := range docs {
		if err := builder.AddDocument(doc.id, doc.content); err != nil {
			t.Fatalf("AddDocument(%d) error: %v", doc.id, err)
		}
	}

	builder.Build()
	index := builder.GetIndex()

	// Verify index state
	if index.TotalDocCount() != 5 {
		t.Errorf("Doc count = %d, want 5", index.TotalDocCount())
	}
	if index.Size() == 0 {
		t.Error("Index is empty after building")
	}

	// Test single term search
	searcher := invertedindex.NewSearcher(index)
	results, err := searcher.Search("programming", 5)
	if err != nil {
		t.Fatalf("Search error: %v", err)
	}
	if len(results) == 0 {
		t.Error("Expected results for 'programming', got none")
	}

	// Verify results are sorted by score
	for i := 1; i < len(results); i++ {
		if results[i].Score > results[i-1].Score {
			t.Errorf("Results not sorted: result[%d].Score=%f > result[%d].Score=%f",
				i, results[i].Score, i-1, results[i-1].Score)
		}
	}

	// Test persistence
	data := index.Save()
	loaded := invertedindex.Load(data)
	if loaded.Size() != index.Size() {
		t.Errorf("Loaded size = %d, want %d", loaded.Size(), index.Size())
	}

	// Test loaded index produces same results
	searcher2 := invertedindex.NewSearcher(loaded)
	results2, err := searcher2.Search("programming", 5)
	if err != nil {
		t.Fatalf("Loaded search error: %v", err)
	}
	if len(results2) != len(results) {
		t.Errorf("Loaded results count = %d, want %d", len(results2), len(results))
	}
}

func TestBM25ConfigVariants(t *testing.T) {
	builder := invertedindex.NewIndexBuilder()
	builder.AddDocument(1, "go go go go")
	builder.AddDocument(2, "go")
	builder.Build()

	index := builder.GetIndex()
	searcher := invertedindex.NewSearcher(index)

	// Different configs should produce different scores
	configs := []invertedindex.BM25Config{
		{K1: 1.0, B: 0.0},
		{K1: 1.5, B: 0.75},
		{K1: 2.0, B: 1.0},
	}

	for _, cfg := range configs {
		searcher.SetConfig(cfg)
		results, err := searcher.Search("go", 5)
		if err != nil {
			t.Fatalf("Search with config %+v error: %v", cfg, err)
		}
		if len(results) != 2 {
			t.Errorf("Config %+v: got %d results, want 2", cfg, len(results))
		}
	}
}

func TestQueryParserCaseInsensitive(t *testing.T) {
	parser := invertedindex.NewQueryParser()

	tests := []string{"GO", "Go", "go", "GO GO"}
	for _, input := range tests {
		query, err := parser.Parse(input)
		if err != nil {
			t.Errorf("Parse(%q) error: %v", input, err)
			continue
		}
		if query.Type == invertedindex.QueryTerm && query.Term != "go" {
			t.Errorf("Parse(%q) term = %q, want 'go'", input, query.Term)
		}
	}
}

func TestSortResultsReverse(t *testing.T) {
	results := invertedindex.Results{
		{DocID: 1, Score: 0.1},
		{DocID: 2, Score: 0.2},
		{DocID: 3, Score: 0.3},
	}

	invertedindex.SortResults(results)

	// Should be sorted descending
	if results[0].Score != 0.3 {
		t.Errorf("First score = %f, want 0.3", results[0].Score)
	}
	if results[2].Score != 0.1 {
		t.Errorf("Last score = %f, want 0.1", results[2].Score)
	}
}

// Benchmark tests
func BenchmarkTokenizeEnglish(b *testing.B) {
	text := "the quick brown fox jumps over the lazy dog"
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		invertedindex.Tokenize(text)
	}
}

func BenchmarkBM25Score(b *testing.B) {
	cfg := invertedindex.DefaultBM25Config()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		invertedindex.BM25Score(5, 100, 10, 1000, 100.0, cfg)
	}
}

func BenchmarkIndexBuild(b *testing.B) {
	docs := []string{
		"go is a fast compiled programming language",
		"python is an easy interpreted programming language",
		"rust is a safe systems programming language",
		"java is an object oriented programming language",
		"go and python are popular languages",
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		builder := invertedindex.NewIndexBuilder()
		for j, doc := range docs {
			builder.AddDocument(j, doc)
		}
		builder.Build()
	}
}

func BenchmarkSearch(b *testing.B) {
	builder := invertedindex.NewIndexBuilder()
	for i := 0; i < 100; i++ {
		builder.AddDocument(i, "go python rust java programming language")
	}
	builder.Build()
	searcher := invertedindex.NewSearcher(builder.GetIndex())

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		searcher.Search("programming", 10)
	}
}
