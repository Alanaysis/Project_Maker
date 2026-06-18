package models

// WSRequest 客户端发送到服务器的 WebSocket 消息
type WSRequest struct {
	Type    string      `json:"type"`    // message, typing, read, status, ping
	ID      string      `json:"id"`      // 请求 ID，用于匹配响应
	Payload interface{} `json:"payload"` // 具体数据
}

// WSResponse 服务器发送到客户端的 WebSocket 消息
type WSResponse struct {
	Type      string      `json:"type"`      // message, ack, error, status, pong
	ID        string      `json:"id"`        // 对应请求的 ID
	Payload   interface{} `json:"payload"`   // 具体数据
	Timestamp int64       `json:"timestamp"` // 服务器时间戳
}

// MessagePayload 消息请求的 Payload
type MessagePayload struct {
	To      string `json:"to"`      // 接收者 ID
	Content string `json:"content"` // 消息内容
	MsgType string `json:"msg_type"` // text, image, file
}

// TypingPayload 输入状态的 Payload
type TypingPayload struct {
	To string `json:"to"` // 接收者 ID
}

// ReadPayload 已读回执的 Payload
type ReadPayload struct {
	MessageID string `json:"message_id"` // 消息 ID
}

// StatusPayload 状态更新的 Payload
type StatusPayload struct {
	Status string `json:"status"` // online, offline, busy, away
}

// WSError 错误响应的 Payload
type WSError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// WSType WebSocket 消息类型常量
const (
	WSTypeMessage = "message"
	WSTypeTyping  = "typing"
	WSTypeRead    = "read"
	WSTypeStatus  = "status"
	WSTypePing    = "ping"
	WSTypePong    = "pong"
	WSTypeAck     = "ack"
	WSTypeError   = "error"
)