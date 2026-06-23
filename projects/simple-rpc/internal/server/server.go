package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"reflect"
	"sync"
	"time"

	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/transport"
)

// ServiceMethod 服务方法
type ServiceMethod struct {
	Name    string
	Method  reflect.Method
	ArgType reflect.Type
	ReplyType reflect.Type
}

// Service 服务定义
type Service struct {
	Name    string
	Type    reflect.Type
	Methods map[string]*ServiceMethod
	Inst    reflect.Value // 服务实例
}

// Server RPC 服务器
type Server struct {
	mu        sync.RWMutex
	services  map[string]*Service
	transport transport.Transport
	codec     codec.Codec
	registry  registry.Registry
	instance  *registry.ServiceInstance
}

// NewServer 创建 RPC 服务器
func NewServer(addr string, codec codec.Codec, reg registry.Registry) *Server {
	return &Server{
		services:  make(map[string]*Service),
		transport: transport.NewTCPTransport(),
		codec:     codec,
		registry:  reg,
		instance: &registry.ServiceInstance{
			InstanceID: fmt.Sprintf("instance-%d", time.Now().UnixNano()),
			Address:    addr,
			Status:     "healthy",
		},
	}
}

// Register 注册服务
func (s *Server) Register(rcvr interface{}) error {
	// 获取服务名称（处理指针类型）
	rcvrType := reflect.TypeOf(rcvr)
	if rcvrType.Kind() == reflect.Ptr {
		rcvrType = rcvrType.Elem()
	}
	svcName := rcvrType.Name()

	svc := &Service{
		Name:    svcName,
		Type:    reflect.TypeOf(rcvr),
		Methods: make(map[string]*ServiceMethod),
		Inst:    reflect.ValueOf(rcvr),
	}

	// 设置服务实例的服务名称
	s.instance.ServiceName = svcName

	// 注册所有导出的方法
	for i := 0; i < svc.Type.NumMethod(); i++ {
		method := svc.Type.Method(i)
		mtype := method.Type

		// 方法必须有 4 个参数: receiver, context, args, reply
		// 返回 1 个值: error
		if mtype.NumIn() != 4 || mtype.NumOut() != 1 {
			continue
		}

		// 检查第二个参数是否为 context.Context
		contextType := reflect.TypeOf((*context.Context)(nil)).Elem()
		if !mtype.In(1).Implements(contextType) {
			continue
		}

		// 检查返回类型是否为 error
		if !mtype.Out(0).Implements(reflect.TypeOf((*error)(nil)).Elem()) {
			continue
		}

		svc.Methods[method.Name] = &ServiceMethod{
			Name:      method.Name,
			Method:    method,
			ArgType:   mtype.In(2),
			ReplyType: mtype.In(3),
		}
	}

	if len(svc.Methods) == 0 {
		return fmt.Errorf("service %s has no valid methods", svc.Name)
	}

	s.mu.Lock()
	s.services[svc.Name] = svc
	s.mu.Unlock()

	return nil
}

// RegisterWithName 注册服务（指定名称）
func (s *Server) RegisterWithName(name string, rcvr interface{}) error {
	svc := &Service{
		Name:    name,
		Type:    reflect.TypeOf(rcvr),
		Methods: make(map[string]*ServiceMethod),
		Inst:    reflect.ValueOf(rcvr),
	}

	// 注册所有导出的方法
	for i := 0; i < svc.Type.NumMethod(); i++ {
		method := svc.Type.Method(i)
		mtype := method.Type

		// 方法必须有 4 个参数: receiver, context, args, reply
		// 返回 1 个值: error
		if mtype.NumIn() != 4 || mtype.NumOut() != 1 {
			continue
		}

		// 检查第二个参数是否为 context.Context
		contextType := reflect.TypeOf((*context.Context)(nil)).Elem()
		if !mtype.In(1).Implements(contextType) {
			continue
		}

		// 检查返回类型是否为 error
		if !mtype.Out(0).Implements(reflect.TypeOf((*error)(nil)).Elem()) {
			continue
		}

		svc.Methods[method.Name] = &ServiceMethod{
			Name:      method.Name,
			Method:    method,
			ArgType:   mtype.In(2),
			ReplyType: mtype.In(3),
		}
	}

	if len(svc.Methods) == 0 {
		return fmt.Errorf("service %s has no valid methods", svc.Name)
	}

	s.mu.Lock()
	s.services[svc.Name] = svc
	s.mu.Unlock()

	return nil
}

// Start 启动服务器
func (s *Server) Start(addr string) error {
	// 注册到注册中心
	if s.registry != nil {
		s.instance.Address = addr
		s.instance.Port = extractPort(addr)
		if err := s.registry.Register(s.instance); err != nil {
			log.Printf("Failed to register service: %v", err)
		}
	}

	// 监听连接
	if err := s.transport.Listen(addr); err != nil {
		return err
	}

	log.Printf("Server started on %s", addr)

	// 接受连接
	for {
		conn, err := s.transport.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		go s.handleConn(conn)
	}
}

// Stop 停止服务器
func (s *Server) Stop() error {
	// 从注册中心注销
	if s.registry != nil && s.instance != nil {
		if err := s.registry.Deregister(s.instance.InstanceID); err != nil {
			log.Printf("Failed to deregister service: %v", err)
		}
	}

	return s.transport.Close()
}

func (s *Server) handleConn(conn transport.Conn) {
	defer conn.Close()

	for {
		msg, err := conn.Receive()
		if err != nil {
			log.Printf("Failed to receive message: %v", err)
			return
		}

		// 解析请求
		var request RpcRequest
		if err := json.Unmarshal(msg.Payload, &request); err != nil {
			log.Printf("Failed to unmarshal request: %v", err)
			continue
		}

		// 处理请求
		response := s.handleRequest(&request)

		// 发送响应
		respBytes, err := json.Marshal(response)
		if err != nil {
			log.Printf("Failed to marshal response: %v", err)
			continue
		}

		respMsg := &transport.Message{
			Payload: respBytes,
		}

		if err := conn.Send(respMsg); err != nil {
			log.Printf("Failed to send response: %v", err)
			return
		}
	}
}

func (s *Server) handleRequest(request *RpcRequest) *RpcResponse {
	s.mu.RLock()
	svc, ok := s.services[request.ServiceName]
	s.mu.RUnlock()

	if !ok {
		return &RpcResponse{
			RequestID: request.RequestID,
			Error:     fmt.Sprintf("service not found: %s", request.ServiceName),
		}
	}

	method, ok := svc.Methods[request.MethodName]
	if !ok {
		return &RpcResponse{
			RequestID: request.RequestID,
			Error:     fmt.Sprintf("method not found: %s", request.MethodName),
		}
	}

	// 创建参数
	arg := reflect.New(method.ArgType)
	if err := json.Unmarshal(request.Args, arg.Interface()); err != nil {
		return &RpcResponse{
			RequestID: request.RequestID,
			Error:     fmt.Sprintf("failed to unmarshal args: %v", err),
		}
	}

	// 创建 reply
	reply := reflect.New(method.ReplyType.Elem())

	// 调用方法
	ctx := context.Background()
	results := method.Method.Func.Call([]reflect.Value{
		svc.Inst, // 使用实际的服务实例
		reflect.ValueOf(ctx),
		arg.Elem(),
		reply,
	})

	// 检查返回值
	if len(results) > 0 && !results[0].IsNil() {
		err := results[0].Interface().(error)
		return &RpcResponse{
			RequestID: request.RequestID,
			Error:     err.Error(),
		}
	}

	// 序列化结果
	resultBytes, err := json.Marshal(reply.Interface())
	if err != nil {
		return &RpcResponse{
			RequestID: request.RequestID,
			Error:     fmt.Sprintf("failed to marshal result: %v", err),
		}
	}

	return &RpcResponse{
		RequestID: request.RequestID,
		Result:    resultBytes,
	}
}

func extractPort(addr string) int {
	_, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		return 0
	}
	port := 0
	fmt.Sscanf(portStr, "%d", &port)
	return port
}

// RpcRequest RPC 请求
type RpcRequest struct {
	ServiceName string          `json:"service_name"`
	MethodName  string          `json:"method_name"`
	Args        json.RawMessage `json:"args"`
	RequestID   string          `json:"request_id"`
}

// RpcResponse RPC 响应
type RpcResponse struct {
	RequestID string          `json:"request_id"`
	Result    json.RawMessage `json:"result"`
	Error     string          `json:"error"`
}
