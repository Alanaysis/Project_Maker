package utils

import "fmt"

// ErrorType 错误类型
type ErrorType int

const (
	ErrTimeout    ErrorType = iota // 超时错误
	ErrNetwork                     // 网络错误
	ErrParticipant                 // 参与者错误
	ErrCoordinator                 // 协调者错误
	ErrTransaction                 // 事务错误
)

// TransactionError 事务错误
type TransactionError struct {
	Type    ErrorType
	Message string
	Err     error
}

// Error 实现error接口
func (e *TransactionError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("%s: %v", e.Message, e.Err)
	}
	return e.Message
}

// Unwrap 返回包装的错误
func (e *TransactionError) Unwrap() error {
	return e.Err
}

// NewTimeoutError 创建超时错误
func NewTimeoutError(message string) *TransactionError {
	return &TransactionError{
		Type:    ErrTimeout,
		Message: message,
	}
}

// NewParticipantError 创建参与者错误
func NewParticipantError(message string, err error) *TransactionError {
	return &TransactionError{
		Type:    ErrParticipant,
		Message: message,
		Err:     err,
	}
}

// NewCoordinatorError 创建协调者错误
func NewCoordinatorError(message string, err error) *TransactionError {
	return &TransactionError{
		Type:    ErrCoordinator,
		Message: message,
		Err:     err,
	}
}
