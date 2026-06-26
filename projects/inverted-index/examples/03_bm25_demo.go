// Package main demonstrates BM25 scoring algorithm.
//
// This example shows:
//   1. How BM25 scores documents for a query term
//   2. Comparison of different BM25 parameter settings
//   3. Effect of document length normalization
//   4. Effect of term frequency saturation
//
// Run with: go run main.go
package main

import (
	"fmt"
	"math"

	"inverted-index/src"
)

func main() {
	fmt.Println("=== Inverted Index - BM25 Scoring Demo ===")
	fmt.Println()

	// Create index builder
	builder := invertedindex.NewIndexBuilder()

	// Add documents with varying lengths and term frequencies
	docs := []struct {
		id      int
		content string
	}{
		{1, "Go is a compiled programming language. Go compiles to machine code. Go is fast."},
		{2, "Python is an interpreted programming language. Python is easy to read."},
		{3, "Go and Python are both programming languages. They are popular in web development."},
		{4, "Rust programming language focuses on memory safety without garbage collection."},
		{5, "Java programming language is widely used for enterprise applications and Android development."},
		{6, "Go language Go language Go language. Go has many Go features."}, // High TF for "go"
	}

	for _, doc := range docs {
		builder.AddDocument(doc.id, doc.content)
	}

	builder.Build()
	index := builder.GetIndex()

	avgDocLen := invertedindex.AverageDocLen(index)
	totalDocs := index.TotalDocCount()

	fmt.Printf("Total documents: %d\n", totalDocs)
	fmt.Printf("Average document length: %.2f tokens\n", avgDocLen)
	fmt.Println()

	// Show term statistics
	fmt.Println("=== Term Statistics ===")
	terms := []string{"go", "programming", "language", "python"}
	for _, term := range terms {
		entry := index.GetEntry(term)
		if entry != nil {
			fmt.Printf("  '%s': DF=%d, terms in index\n", term, entry.DocumentFreq)
			for docID, tf := range entry.TF {
				fmt.Printf("    Doc %d: TF=%d, docLen=%d\n", docID, tf, index.DocLength(docID))
			}
		}
	}
	fmt.Println()

	// Demo BM25 scoring with different configurations
	fmt.Println("=== BM25 Scoring for term 'go' ===")
	fmt.Printf("%-10s | %-8s | %-10s | %-10s | %-10s | %-10s\n", "Config", "Doc", "TF", "DocLen", "Score", "Explanation")
	fmt.Println("-" + "-----------+" + "--------+" + "----------+" + "----------+" + "----------+" + "------------")

	// Standard BM25
	scoreDemo(index, "Standard (k1=1.5,b=0.75)", 1.5, 0.75, "go")

	// Higher k1 (less saturation)
	scoreDemo(index, "High k1 (k1=2.5,b=0.75)", 2.5, 0.75, "go")

	// Lower k1 (more saturation)
	scoreDemo(index, "Low k1 (k1=1.0,b=0.75)", 1.0, 0.75, "go")

	// No length normalization
	scoreDemo(index, "No norm (k1=1.5,b=0.0)", 1.5, 0.0, "go")

	// Full length normalization
	scoreDemo(index, "Full norm (k1=1.5,b=1.0)", 1.5, 1.0, "go")

	// Show BM25 formula components
	fmt.Println("\n=== BM25 Formula Components ===")
	showBM25Components(index, "go")

	// Compare BM25 with simple TF-IDF
	fmt.Println("\n=== BM25 vs Simple TF-IDF Comparison ===")
	compareBM25vsTFIDF(index, "go")
}

// scoreDemo shows BM25 scores for a term with given parameters.
func scoreDemo(index *invertedindex.InvertedIndex, label string, k1, b float64, term string) {
	entry := index.GetEntry(term)
	if entry == nil {
		return
	}

	avgDocLen := invertedindex.AverageDocLen(index)
	totalDocs := index.TotalDocCount()
	cfg := invertedindex.BM25Config{K1: k1, B: b}

	fmt.Printf("%-25s | ", label)

	for _, p := range entry.Postings.Items {
		tf := entry.TF[p.DocID]
		docLen := index.DocLength(p.DocID)
		df := entry.DocumentFreq
		score := invertedindex.BM25Score(tf, docLen, df, totalDocs, avgDocLen, cfg)
		fmt.Printf(" %8.4f |", score)
	}
	fmt.Println()
}

// showBM25Components shows the IDF and TF components separately.
func showBM25Components(index *invertedindex.InvertedIndex, term string) {
	entry := index.GetEntry(term)
	if entry == nil {
		return
	}

	avgDocLen := invertedindex.AverageDocLen(index)
	totalDocs := index.TotalDocCount()

	fmt.Printf("Term: '%s'\n", term)
	fmt.Printf("DF: %d, Total docs: %d\n", entry.DocumentFreq, totalDocs)
	fmt.Printf("IDF = log((%d - %d + 0.5) / (%d + 0.5) + 1) = %.4f\n",
		totalDocs, entry.DocumentFreq, entry.DocumentFreq,
		math.Log(float64(totalDocs-entry.DocumentFreq+0.5)/float64(entry.DocumentFreq+0.5)+1))
	fmt.Println()

	for _, p := range entry.Postings.Items {
		tf := entry.TF[p.DocID]
		docLen := index.DocLength(p.DocID)
		df := entry.DocumentFreq

		// IDF
		idf := math.Log(float64(totalDocs-df+0.5)/float64(df+0.5) + 1)

		// TF component
		k1 := 1.5
		b := 0.75
		docLenNorm := 1.0 - float64(b) + float64(b)*(float64(docLen)/avgDocLen)
		tfScore := float64(k1+1) * float64(tf) / (float64(tf) + float64(k1)*docLenNorm)

		// Final score
		score := tfScore * idf

		fmt.Printf("  Doc %d: TF=%d, docLen=%d\n", p.DocID, tf, docLen)
		fmt.Printf("    IDF = %.4f\n", idf)
		fmt.Printf("    docLenNorm = %.4f\n", docLenNorm)
		fmt.Printf("    TF_score = %.4f\n", tfScore)
		fmt.Printf("    BM25 = %.4f\n", score)
	}
}

// compareBM25vsTFIDF compares BM25 with simple TF-IDF.
func compareBM25vsTFIDF(index *invertedindex.InvertedIndex, term string) {
	entry := index.GetEntry(term)
	if entry == nil {
		return
	}

	avgDocLen := invertedindex.AverageDocLen(index)
	totalDocs := index.TotalDocCount()

	fmt.Printf("%-10s | %-6s | %-6s | %-10s | %-10s\n", "Term", "TF", "DocLen", "BM25", "TF-IDF")
	fmt.Println("-" + "----------+" + "------+" + "------+" + "----------+" + "----------")

	for _, p := range entry.Postings.Items {
		tf := entry.TF[p.DocID]
		docLen := index.DocLength(p.DocID)
		df := entry.DocumentFreq

		// BM25
		cfg := invertedindex.DefaultBM25Config()
		bm25 := invertedindex.BM25Score(tf, docLen, df, totalDocs, avgDocLen, cfg)

		// Simple TF-IDF (unnormalized)
		idf := math.Log(float64(totalDocs) / float64(df))
		tfidf := float64(tf) * idf

		fmt.Printf("%-10s | %-6d | %-6d | %-10.4f | %-10.4f\n",
			term, tf, docLen, bm25, tfidf)
	}
}
