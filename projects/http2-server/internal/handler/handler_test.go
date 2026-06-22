package handler

import (
	"testing"

	"github.com/anthropic/http2-server/internal/connection"
	"github.com/anthropic/http2-server/internal/frame"
)

func TestRouterGet(t *testing.T) {
	router := NewRouter()
	called := false

	router.Get("/test", func(stream *connection.Stream) error {
		called = true
		stream.ResponseCode = 200
		stream.ResponseHeaders = []frame.HeaderField{
			{Name: ":status", Value: "200"},
		}
		stream.ResponseBody = []byte("OK")
		return nil
	})

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":path", Value: "/test"},
		},
	}

	err := router.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if !called {
		t.Error("Handler was not called")
	}
	if stream.ResponseCode != 200 {
		t.Errorf("Expected status 200, got %d", stream.ResponseCode)
	}
}

func TestRouterPost(t *testing.T) {
	router := NewRouter()
	called := false

	router.Post("/echo", func(stream *connection.Stream) error {
		called = true
		stream.ResponseCode = 200
		stream.ResponseBody = stream.Body
		return nil
	})

	stream := &connection.Stream{
		ID:   1,
		Body: []byte("hello"),
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "POST"},
			{Name: ":path", Value: "/echo"},
		},
	}

	err := router.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if !called {
		t.Error("Handler was not called")
	}
	if string(stream.ResponseBody) != "hello" {
		t.Errorf("Expected body 'hello', got %q", stream.ResponseBody)
	}
}

func TestRouterNotFound(t *testing.T) {
	router := NewRouter()
	// Register a GET route so the method is known
	router.Get("/exists", func(stream *connection.Stream) error {
		return nil
	})

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":path", Value: "/nonexistent"},
		},
	}

	err := router.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 404 {
		t.Errorf("Expected status 404, got %d", stream.ResponseCode)
	}
}

func TestRouterMethodNotAllowed(t *testing.T) {
	router := NewRouter()
	router.Get("/test", func(stream *connection.Stream) error {
		return nil
	})

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "DELETE"},
			{Name: ":path", Value: "/test"},
		},
	}

	err := router.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 405 {
		t.Errorf("Expected status 405, got %d", stream.ResponseCode)
	}
}

func TestRouterBadRequest(t *testing.T) {
	router := NewRouter()

	// Missing method
	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":path", Value: "/test"},
		},
	}

	err := router.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 400 {
		t.Errorf("Expected status 400, got %d", stream.ResponseCode)
	}
}

func TestDefaultHandler(t *testing.T) {
	handler := NewDefaultHandler()

	// Test root endpoint
	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":path", Value: "/"},
		},
	}

	err := handler.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 200 {
		t.Errorf("Expected status 200, got %d", stream.ResponseCode)
	}
	if string(stream.ResponseBody) == "" {
		t.Error("Response body should not be empty")
	}
}

func TestDefaultHandlerHealth(t *testing.T) {
	handler := NewDefaultHandler()

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":path", Value: "/health"},
		},
	}

	err := handler.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 200 {
		t.Errorf("Expected status 200, got %d", stream.ResponseCode)
	}
}

func TestDefaultHandlerInfo(t *testing.T) {
	handler := NewDefaultHandler()

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "GET"},
			{Name: ":path", Value: "/info"},
		},
	}

	err := handler.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 200 {
		t.Errorf("Expected status 200, got %d", stream.ResponseCode)
	}
}

func TestDefaultHandlerEcho(t *testing.T) {
	handler := NewDefaultHandler()

	stream := &connection.Stream{
		ID:   1,
		Body: []byte("test body"),
		Headers: []frame.HeaderField{
			{Name: ":method", Value: "POST"},
			{Name: ":path", Value: "/echo"},
		},
	}

	err := handler.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 200 {
		t.Errorf("Expected status 200, got %d", stream.ResponseCode)
	}
	if string(stream.ResponseBody) != "test body" {
		t.Errorf("Expected body 'test body', got %q", stream.ResponseBody)
	}
}

func TestStaticFileHandler(t *testing.T) {
	handler := NewStaticFileHandler("/var/www")

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":path", Value: "/index.html"},
		},
	}

	err := handler.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 200 {
		t.Errorf("Expected status 200, got %d", stream.ResponseCode)
	}
}

func TestStaticFileHandlerDirectoryTraversal(t *testing.T) {
	handler := NewStaticFileHandler("/var/www")

	stream := &connection.Stream{
		ID: 1,
		Headers: []frame.HeaderField{
			{Name: ":path", Value: "/../../../etc/passwd"},
		},
	}

	err := handler.Handle(stream)
	if err != nil {
		t.Fatalf("Handle failed: %v", err)
	}

	if stream.ResponseCode != 403 {
		t.Errorf("Expected status 403, got %d", stream.ResponseCode)
	}
}
