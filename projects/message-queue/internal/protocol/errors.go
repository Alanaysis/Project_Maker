package protocol

import "errors"

var (
	// ErrTopicNotFound is returned when a referenced topic does not exist.
	ErrTopicNotFound = errors.New("topic not found")
	// ErrTopicAlreadyExists is returned when trying to create a duplicate topic.
	ErrTopicAlreadyExists = errors.New("topic already exists")
	// ErrMessageNotFound is returned when a message ID cannot be resolved.
	ErrMessageNotFound = errors.New("message not found")
	// ErrConsumerNotFound is returned when a consumer ID is unknown.
	ErrConsumerNotFound = errors.New("consumer not found")
	// ErrQueueFull is returned when the message buffer is at capacity.
	ErrQueueFull = errors.New("queue is full")
	// ErrAlreadyAcknowledged is returned when a message is acked twice.
	ErrAlreadyAcknowledged = errors.New("message already acknowledged")
	// ErrSubscriptionExists is returned for duplicate subscription attempts.
	ErrSubscriptionExists = errors.New("subscription already exists")
	// ErrConsumerGroupNotFound is returned when a consumer group does not exist.
	ErrConsumerGroupNotFound = errors.New("consumer group not found")
	// ErrConsumerGroupExists is returned when trying to create a duplicate group.
	ErrConsumerGroupExists = errors.New("consumer group already exists")
	// ErrNoAvailableConsumer is returned when no consumer in a group is available.
	ErrNoAvailableConsumer = errors.New("no available consumer in group")
	// ErrMessageNotReady is returned when a delayed message is not yet ready.
	ErrMessageNotReady = errors.New("message not ready for delivery")
	// ErrInvalidPriority is returned for an invalid priority value.
	ErrInvalidPriority = errors.New("invalid priority value")
	// ErrMaxRetriesExceeded is returned when a message exceeds max retries.
	ErrMaxRetriesExceeded = errors.New("max retries exceeded")
)
