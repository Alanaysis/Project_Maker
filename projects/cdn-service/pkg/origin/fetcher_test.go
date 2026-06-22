package origin

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestFetcher_Fetch(t *testing.T) {
	// Create a test origin server
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("<html><body>Hello World</body></html>"))
	}))
	defer origin.Close()

	// Create fetcher
	fetcher := NewFetcher(origin.URL)

	// Fetch content
	resp, err := fetcher.Fetch("/test", nil)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if string(resp.Body) != "<html><body>Hello World</body></html>" {
		t.Errorf("Unexpected body: %s", string(resp.Body))
	}

	if resp.Headers.Get("Content-Type") != "text/html" {
		t.Errorf("Expected Content-Type text/html, got %s", resp.Headers.Get("Content-Type"))
	}
}

func TestFetcher_FetchWithHeaders(t *testing.T) {
	// Create a test origin server that echoes headers
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Echo the custom header
		customHeader := r.Header.Get("X-Custom-Header")
		w.Header().Set("X-Echo-Header", customHeader)
		w.WriteHeader(http.StatusOK)
	}))
	defer origin.Close()

	// Create fetcher
	fetcher := NewFetcher(origin.URL)

	// Create headers
	headers := http.Header{}
	headers.Set("X-Custom-Header", "test-value")

	// Fetch content
	resp, err := fetcher.Fetch("/test", headers)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.Headers.Get("X-Echo-Header") != "test-value" {
		t.Errorf("Expected header 'test-value', got '%s'", resp.Headers.Get("X-Echo-Header"))
	}
}

func TestFetcher_FetchNotFound(t *testing.T) {
	// Create a test origin server that returns 404
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		w.Write([]byte("Not Found"))
	}))
	defer origin.Close()

	// Create fetcher
	fetcher := NewFetcher(origin.URL)

	// Fetch content
	resp, err := fetcher.Fetch("/not-found", nil)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", resp.StatusCode)
	}
}

func TestFetcher_FetchWithRetry(t *testing.T) {
	attempts := 0

	// Create a test origin server that fails twice then succeeds
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts < 3 {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Success"))
	}))
	defer origin.Close()

	// Create fetcher with retries
	fetcher := NewFetcher(origin.URL,
		WithRetries(3),
		WithRetryDelay(10*time.Millisecond),
	)

	// Fetch content
	resp, err := fetcher.FetchWithRetry("/test", nil)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	if attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", attempts)
	}
}

func TestFetcher_FetchWithRetryExhausted(t *testing.T) {
	// Create a test origin server that always fails
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer origin.Close()

	// Create fetcher with retries
	fetcher := NewFetcher(origin.URL,
		WithRetries(2),
		WithRetryDelay(10*time.Millisecond),
	)

	// Fetch content (should fail after retries)
	_, err := fetcher.FetchWithRetry("/test", nil)
	if err == nil {
		t.Error("Expected error after retries exhausted")
	}
}

func TestFetcher_Timeout(t *testing.T) {
	// Create a slow origin server
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer origin.Close()

	// Create fetcher with short timeout
	fetcher := NewFetcher(origin.URL,
		WithTimeout(50*time.Millisecond),
		WithRetries(0),
	)

	// Fetch content (should timeout)
	_, err := fetcher.Fetch("/test", nil)
	if err == nil {
		t.Error("Expected timeout error")
	}
}

func TestFetcher_InvalidURL(t *testing.T) {
	// Create fetcher with invalid URL
	fetcher := NewFetcher("http://invalid.localhost:12345",
		WithTimeout(100*time.Millisecond),
		WithRetries(0),
	)

	// Fetch content (should fail)
	_, err := fetcher.Fetch("/test", nil)
	if err == nil {
		t.Error("Expected error for invalid URL")
	}
}

func TestIsHopByHopHeader(t *testing.T) {
	tests := []struct {
		header   string
		expected bool
	}{
		{"Connection", true},
		{"Keep-Alive", true},
		{"Transfer-Encoding", true},
		{"Upgrade", true},
		{"Content-Type", false},
		{"Authorization", false},
		{"X-Custom", false},
	}

	for _, test := range tests {
		result := isHopByHopHeader(test.header)
		if result != test.expected {
			t.Errorf("isHopByHopHeader(%s) = %v, want %v", test.header, result, test.expected)
		}
	}
}

func TestNewFetcher_DefaultOptions(t *testing.T) {
	fetcher := NewFetcher("http://example.com")

	if fetcher.baseURL != "http://example.com" {
		t.Errorf("Expected baseURL 'http://example.com', got '%s'", fetcher.baseURL)
	}

	if fetcher.retries != 3 {
		t.Errorf("Expected 3 retries, got %d", fetcher.retries)
	}

	if fetcher.client.Timeout != 10*time.Second {
		t.Errorf("Expected 10s timeout, got %v", fetcher.client.Timeout)
	}
}

func TestNewFetcher_CustomOptions(t *testing.T) {
	fetcher := NewFetcher("http://example.com",
		WithTimeout(5*time.Second),
		WithRetries(5),
		WithRetryDelay(200*time.Millisecond),
	)

	if fetcher.client.Timeout != 5*time.Second {
		t.Errorf("Expected 5s timeout, got %v", fetcher.client.Timeout)
	}

	if fetcher.retries != 5 {
		t.Errorf("Expected 5 retries, got %d", fetcher.retries)
	}

	if fetcher.retryDelay != 200*time.Millisecond {
		t.Errorf("Expected 200ms retry delay, got %v", fetcher.retryDelay)
	}
}