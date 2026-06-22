package stream

import "errors"

var (
	// ErrStreamNotFound indicates the stream was not found
	ErrStreamNotFound = errors.New("stream not found")

	// ErrStreamAlreadyPublishing indicates the stream is already being published
	ErrStreamAlreadyPublishing = errors.New("stream is already being published")

	// ErrStreamNotPublishing indicates the stream is not being published
	ErrStreamNotPublishing = errors.New("stream is not being published")

	// ErrBufferFull indicates the media buffer is full
	ErrBufferFull = errors.New("media buffer is full")

	// ErrStreamClosed indicates the stream has been closed
	ErrStreamClosed = errors.New("stream is closed")

	// ErrInvalidStreamKey indicates an invalid stream key
	ErrInvalidStreamKey = errors.New("invalid stream key")

	// ErrMaxStreamsReached indicates the maximum number of streams has been reached
	ErrMaxStreamsReached = errors.New("maximum number of streams reached")
)
