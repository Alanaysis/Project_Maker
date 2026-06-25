package main

import (
	"fmt"
	"os"

	"distributed-transaction/coordinator"
	"distributed-transaction/participant"
	"distributed-transaction/saga"
	"distributed-transaction/tcc"
	"distributed-transaction/transaction"
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		return
	}

	switch os.Args[1] {
	case "2pc":
		run2PC()
	case "3pc":
		run3PC()
	case "saga":
		runSaga()
	case "tcc":
		runTCC()
	case "all":
		run2PC()
		fmt.Println()
		run3PC()
		fmt.Println()
		runSaga()
		fmt.Println()
		runTCC()
	case "help":
		printUsage()
	default:
		fmt.Printf("Unknown command: %s\n", os.Args[1])
		printUsage()
	}
}

func printUsage() {
	fmt.Println("分布式事务演示程序")
	fmt.Println()
	fmt.Println("用法: go run cmd/main.go <command>")
	fmt.Println()
	fmt.Println("命令:")
	fmt.Println("  2pc   - 运行两阶段提交示例")
	fmt.Println("  3pc   - 运行三阶段提交示例")
	fmt.Println("  saga  - 运行 Saga 模式示例")
	fmt.Println("  tcc   - 运行 TCC 模式示例")
	fmt.Println("  all   - 运行所有示例")
	fmt.Println("  help  - 显示帮助信息")
}

// run2PC 演示两阶段提交
func run2PC() {
	fmt.Println("========================================")
	fmt.Println("  两阶段提交 (2PC) 演示")
	fmt.Println("========================================")

	coord := coordinator.NewCoordinator("demo-coordinator")

	// 创建参与者
	p1 := participant.NewDefaultCohort("participant-1")
	p2 := participant.NewDefaultCohort("participant-2")
	p3 := participant.NewDefaultCohort("participant-3")

	_ = coord.RegisterCohort(p1)
	_ = coord.RegisterCohort(p2)
	_ = coord.RegisterCohort(p3)

	// 执行事务
	tx := transaction.NewTransaction("tx-2pc-001")
	result, err := coord.ExecuteTransaction(tx)

	if err != nil {
		fmt.Printf("事务失败: %v\n", err)
	} else {
		fmt.Printf("事务结果: %s\n", result)
	}

	// 演示失败场景
	fmt.Println()
	fmt.Println("--- 失败场景：参与者模拟错误 ---")

	coord2 := coordinator.NewCoordinator("demo-coordinator-2")
	p4 := participant.NewDefaultCohort("participant-4")
	p5 := participant.NewDefaultCohort("participant-5")
	p5.SetSimulateError(true) // 模拟错误

	_ = coord2.RegisterCohort(p4)
	_ = coord2.RegisterCohort(p5)

	tx2 := transaction.NewTransaction("tx-2pc-002")
	result2, err2 := coord2.ExecuteTransaction(tx2)

	if err2 != nil {
		fmt.Printf("事务失败（预期）: %v\n", err2)
	}
	if result2 != nil {
		fmt.Printf("事务结果: %s\n", result2)
	}
}

// run3PC 演示三阶段提交
func run3PC() {
	fmt.Println("========================================")
	fmt.Println("  三阶段提交 (3PC) 演示")
	fmt.Println("========================================")

	coord := coordinator.NewThreePhaseCoordinator("demo-3pc-coordinator")

	p1 := participant.NewDefaultCohort("3pc-participant-1")
	p2 := participant.NewDefaultCohort("3pc-participant-2")
	p3 := participant.NewDefaultCohort("3pc-participant-3")

	_ = coord.RegisterCohort(p1)
	_ = coord.RegisterCohort(p2)
	_ = coord.RegisterCohort(p3)

	tx := transaction.NewTransaction("tx-3pc-001")
	result, err := coord.ExecuteTransaction(tx)

	if err != nil {
		fmt.Printf("事务失败: %v\n", err)
	} else {
		fmt.Printf("事务结果: %s\n", result)
	}
}

// runSaga 演示 Saga 模式
func runSaga() {
	fmt.Println("========================================")
	fmt.Println("  Saga 模式演示")
	fmt.Println("========================================")

	// 成功场景
	fmt.Println("--- 成功场景 ---")
	s := saga.NewSaga("demo-saga-001")

	s.AddStep("Step1-CreateOrder",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  Step1: 创建订单...")
			data["order_id"] = "ORD-001"
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  补偿 Step1: 取消订单...")
			return nil, nil
		},
	)

	s.AddStep("Step2-ReserveInventory",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  Step2: 预留库存...")
			data["reserved"] = true
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  补偿 Step2: 释放库存...")
			return nil, nil
		},
	)

	s.AddStep("Step3-ProcessPayment",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  Step3: 处理支付...")
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  补偿 Step3: 退款...")
			return nil, nil
		},
	)

	if err := s.Execute(); err != nil {
		fmt.Printf("  Saga 失败: %v\n", err)
	} else {
		fmt.Println("  Saga 成功!")
	}

	// 失败场景
	fmt.Println()
	fmt.Println("--- 失败场景（触发补偿） ---")
	s2 := saga.NewSaga("demo-saga-002")

	s2.AddStep("Step1",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  Step1: 成功")
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  补偿 Step1")
			return nil, nil
		},
	)

	s2.AddStep("Step2",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  Step2: 成功")
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  补偿 Step2")
			return nil, nil
		},
	)

	s2.AddStep("Step3-WillFail",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  Step3: 失败!")
			return nil, fmt.Errorf("simulated failure")
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  补偿 Step3")
			return nil, nil
		},
	)

	if err := s2.Execute(); err != nil {
		fmt.Printf("  Saga 失败（预期）: %v\n", err)
	}
}

// runTCC 演示 TCC 模式
func runTCC() {
	fmt.Println("========================================")
	fmt.Println("  TCC 模式演示")
	fmt.Println("========================================")

	tx := tcc.NewTCCTransaction("demo-tcc-001")
	tx.Data["amount"] = 100

	// 参与者 1: 账户服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "AccountService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(int)
			fmt.Printf("  [Try-账户] 冻结金额: %d\n", amount)
			data["frozen"] = amount
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Confirm-账户] 确认扣款")
			delete(data, "frozen")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Cancel-账户] 解冻金额")
			delete(data, "frozen")
			return nil, nil
		},
	})

	// 参与者 2: 库存服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "InventoryService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Try-库存] 预留库存")
			data["reserved"] = true
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Confirm-库存] 确认扣减库存")
			delete(data, "reserved")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Cancel-库存] 释放库存")
			delete(data, "reserved")
			return nil, nil
		},
	})

	if err := tx.Execute(); err != nil {
		fmt.Printf("  TCC 事务失败: %v\n", err)
	} else {
		fmt.Println("  TCC 事务成功!")
	}

	// 失败场景
	fmt.Println()
	fmt.Println("--- TCC 失败场景 ---")
	tx2 := tcc.NewTCCTransaction("demo-tcc-002")
	tx2.Data["amount"] = 1000

	tx2.RegisterParticipant(&tcc.TCCParticipant{
		Name: "AccountService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Try-账户] 冻结金额: 1000")
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Confirm-账户]")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Cancel-账户] 解冻金额")
			return nil, nil
		},
	})

	tx2.RegisterParticipant(&tcc.TCCParticipant{
		Name: "InventoryService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			fmt.Println("  [Try-库存] 库存不足，失败!")
			return nil, fmt.Errorf("insufficient inventory")
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			return nil, nil
		},
	})

	if err := tx2.Execute(); err != nil {
		fmt.Printf("  TCC 事务失败（预期）: %v\n", err)
	}
}
