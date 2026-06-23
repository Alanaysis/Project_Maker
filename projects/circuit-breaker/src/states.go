package src

// State 熔断器状态
type State int

const (
    // StateClosed 关闭状态 - 正常处理请求
    StateClosed State = iota
    // StateOpen 打开状态 - 直接拒绝请求
    StateOpen
    // StateHalfOpen 半开状态 - 允许部分请求测试
    StateHalfOpen
)

// String 返回状态的字符串表示
func (s State) String() string {
    switch s {
    case StateClosed:
        return "Closed"
    case StateOpen:
        return "Open"
    case StateHalfOpen:
        return "HalfOpen"
    default:
        return "Unknown"
    }
}

// IsValid 检查状态是否有效
func (s State) IsValid() bool {
    return s >= StateClosed && s <= StateHalfOpen
}

// CanExecute 检查当前状态是否允许执行请求
func (s State) CanExecute() bool {
    return s == StateClosed || s == StateHalfOpen
}
