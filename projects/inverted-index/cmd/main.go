package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/copyninja/inverted-index/internal/index"
)

func main() {
	idx := index.NewIndexer()

	// Load sample documents
	loadSampleDocuments(idx)

	fmt.Println("=== Inverted Index Search Engine ===")
	fmt.Printf("Indexed %d documents, %d unique terms\n\n",
		idx.GetStats().NumDocuments, idx.GetStats().NumTerms)

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("search> ")
		if !scanner.Scan() {
			break
		}
		query := strings.TrimSpace(scanner.Text())
		if query == "" {
			continue
		}
		if query == "quit" || query == "exit" {
			fmt.Println("Bye!")
			break
		}
		if query == "stats" {
			stats := idx.GetStats()
			fmt.Printf("Documents: %d\n", stats.NumDocuments)
			fmt.Printf("Terms: %d\n", stats.NumTerms)
			fmt.Printf("Total tokens: %d\n", stats.TotalTokens)
			continue
		}

		results := idx.Search(query)
		if len(results) == 0 {
			fmt.Println("No results found.")
		} else {
			fmt.Printf("Found %d results:\n\n", len(results))
			for i, r := range results {
				fmt.Printf("  %d. [%s] %s (score: %.2f)\n",
					i+1, r.DocID, r.Title, r.Score)
				fmt.Printf("     %s\n\n", r.Snippet)
			}
		}
	}
}

func loadSampleDocuments(idx *index.Indexer) {
	docs := []index.Document{
		{
			ID:      "doc1",
			Title:   "Introduction to Go Programming",
			Content: "Go is a statically typed compiled programming language designed at Google. Go is syntactically similar to C, but with memory safety, garbage collection, and structural typing. Go is widely used for building web servers, microservices, and cloud-native applications.",
		},
		{
			ID:      "doc2",
			Title:   "Web Development with JavaScript",
			Content: "JavaScript is the programming language of the web. It enables interactive web pages and is an essential part of web applications. Modern JavaScript frameworks like React, Angular, and Vue.js have revolutionized front-end development.",
		},
		{
			ID:      "doc3",
			Title:   "Data Structures and Algorithms",
			Content: "Data structures are fundamental building blocks of computer science. Common data structures include arrays, linked lists, trees, graphs, hash tables, and heaps. Algorithms like sorting, searching, and graph traversal are essential for efficient programming.",
		},
		{
			ID:      "doc4",
			Title:   "Cloud Computing and Microservices",
			Content: "Cloud computing provides on-demand computing resources over the internet. Microservices architecture decomposes applications into small, independent services. Technologies like Docker, Kubernetes, and serverless computing enable scalable cloud-native applications.",
		},
		{
			ID:      "doc5",
			Title:   "Machine Learning Fundamentals",
			Content: "Machine learning is a subset of artificial intelligence that enables systems to learn from data. Common algorithms include linear regression, decision trees, random forests, and neural networks. Python and Go are popular languages for machine learning applications.",
		},
		{
			ID:      "doc6",
			Title:   "Database Systems and SQL",
			Content: "Database systems store and manage structured data efficiently. SQL is the standard language for relational databases like PostgreSQL, MySQL, and SQLite. NoSQL databases like MongoDB and Redis handle unstructured data and provide high performance for specific use cases.",
		},
		{
			ID:      "doc7",
			Title:   "Operating Systems Concepts",
			Content: "Operating systems manage computer hardware and software resources. Key concepts include process management, memory management, file systems, and device drivers. Linux, Windows, and macOS are the most widely used operating systems today.",
		},
		{
			ID:      "doc8",
			Title:   "Network Programming in Go",
			Content: "Go provides excellent support for network programming with its standard library. The net package provides portable interfaces for network I/O including TCP/IP, UDP, and Unix domain sockets. Go is commonly used for building network servers and distributed systems.",
		},
	}

	for _, doc := range docs {
		if err := idx.AddDocument(doc); err != nil {
			fmt.Fprintf(os.Stderr, "Error indexing %s: %v\n", doc.ID, err)
		}
	}
}
