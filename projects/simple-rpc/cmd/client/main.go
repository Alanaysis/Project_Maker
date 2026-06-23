package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"time"

	"github.com/simple-rpc/examples"
	"github.com/simple-rpc/internal/client"
	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/loadbalancer"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/timeout"
)

func main() {
	// 命令行参数
	serviceName := flag.String("service", "Calculator", "service name (Calculator or UserService)")
	balancerName := flag.String("balancer", "round_robin", "load balancer (random, round_robin, weighted, least_connections)")
	flag.Parse()

	// 创建注册中心
	reg := registry.NewMemoryRegistry()

	// 创建负载均衡器
	balancerReg := loadbalancer.NewBalancerRegistry()
	balancer, err := balancerReg.Get(*balancerName)
	if err != nil {
		log.Fatalf("Failed to get balancer: %v", err)
	}

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 创建客户端配置
	config := &client.ClientConfig{
		ServiceName:   *serviceName,
		BalancerName:  *balancerName,
		TimeoutConfig: timeout.DefaultConfig(),
		MaxRetries:    3,
	}

	// 创建客户端
	rpcClient := client.NewClient(reg, balancer, c, config)
	defer rpcClient.Close()

	// 根据服务类型执行不同的调用
	switch *serviceName {
	case "Calculator":
		callCalculator(rpcClient)
	case "UserService":
		callUserService(rpcClient)
	default:
		log.Fatalf("Unknown service: %s", *serviceName)
	}
}

func callCalculator(c *client.Client) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// 调用 Add
	addReq := &examples.AddRequest{A: 10, B: 20}
	addResp := &examples.AddResponse{}
	if err := c.Call(ctx, "Calculator", "Add", addReq, addResp); err != nil {
		log.Printf("Add failed: %v", err)
	} else {
		fmt.Printf("Add: %d + %d = %d\n", addReq.A, addReq.B, addResp.Result)
	}

	// 调用 Multiply
	mulReq := &examples.MultiplyRequest{A: 5, B: 6}
	mulResp := &examples.MultiplyResponse{}
	if err := c.Call(ctx, "Calculator", "Multiply", mulReq, mulResp); err != nil {
		log.Printf("Multiply failed: %v", err)
	} else {
		fmt.Printf("Multiply: %d * %d = %d\n", mulReq.A, mulReq.B, mulResp.Result)
	}
}

func callUserService(c *client.Client) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// 调用 GetUser
	getReq := &examples.GetUserRequest{UserID: "123"}
	getResp := &examples.GetUserResponse{}
	if err := c.Call(ctx, "UserService", "GetUser", getReq, getResp); err != nil {
		log.Printf("GetUser failed: %v", err)
	} else {
		fmt.Printf("GetUser: %+v\n", getResp)
	}

	// 调用 ListUsers
	listReq := &examples.ListUsersRequest{Page: 1, PageSize: 5}
	listResp := &examples.ListUsersResponse{}
	if err := c.Call(ctx, "UserService", "ListUsers", listReq, listResp); err != nil {
		log.Printf("ListUsers failed: %v", err)
	} else {
		fmt.Printf("ListUsers: Total=%d, Users=%+v\n", listResp.Total, listResp.Users)
	}
}
