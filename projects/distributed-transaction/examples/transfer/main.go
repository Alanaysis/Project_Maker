package main

import (
	"fmt"

	"distributed-transaction/saga"
	"distributed-transaction/tcc"
)

// ============================================================
// 转账系统示例
//
// 场景：从账户 A 转账 100 元到账户 B
// 涉及两个服务：扣款服务、加款服务
// ============================================================

func main() {
	fmt.Println("========================================")
	fmt.Println("  分布式事务 - 转账系统示例")
	fmt.Println("========================================")
	fmt.Println()

	// 模拟账户余额
	accounts := map[string]int{
		"A": 500,
		"B": 200,
	}

	fmt.Printf("初始余额: A=%d, B=%d\n\n", accounts["A"], accounts["B"])

	// 示例 1: 使用 Saga 模式转账
	fmt.Println("--- 示例 1: Saga 模式转账 ---")
	sagaTransfer(accounts)

	fmt.Printf("\nSaga 后余额: A=%d, B=%d\n\n", accounts["A"], accounts["B"])

	// 重置余额
	accounts["A"] = 500
	accounts["B"] = 200

	// 示例 2: 使用 TCC 模式转账
	fmt.Println("--- 示例 2: TCC 模式转账 ---")
	tccTransfer(accounts)

	fmt.Printf("\nTCC 后余额: A=%d, B=%d\n", accounts["A"], accounts["B"])
}

// sagaTransfer 使用 Saga 模式执行转账
func sagaTransfer(accounts map[string]int) {
	s := saga.NewSaga("transfer-001")

	// Step 1: 从 A 扣款
	s.AddStep("Debit A",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := 100
			if accounts["A"] < amount {
				return nil, fmt.Errorf("insufficient balance: A has %d, need %d", accounts["A"], amount)
			}
			accounts["A"] -= amount
			data["amount"] = amount
			fmt.Printf("  [Debit A] A 余额: %d -> %d\n", accounts["A"]+amount, accounts["A"])
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(int)
			accounts["A"] += amount
			fmt.Printf("  [补偿 Debit A] A 余额恢复: %d\n", accounts["A"])
			return nil, nil
		},
	)

	// Step 2: 向 B 加款
	s.AddStep("Credit B",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(int)
			accounts["B"] += amount
			fmt.Printf("  [Credit B] B 余额: %d -> %d\n", accounts["B"]-amount, accounts["B"])
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(int)
			accounts["B"] -= amount
			fmt.Printf("  [补偿 Credit B] B 余额恢复: %d\n", accounts["B"])
			return nil, nil
		},
	)

	if err := s.Execute(); err != nil {
		fmt.Printf("  转账失败: %v\n", err)
	} else {
		fmt.Println("  转账成功!")
	}
}

// tccTransfer 使用 TCC 模式执行转账
func tccTransfer(accounts map[string]int) {
	tx := tcc.NewTCCTransaction("transfer-tcc-001")

	amount := 100

	// Participant 1: 扣款服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "DebitService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			if accounts["A"] < amount {
				return nil, fmt.Errorf("insufficient balance")
			}
			// 冻结金额
			accounts["A"] -= amount
			data["frozen_a"] = amount
			fmt.Printf("  [Try-Debit] A 冻结 %d, 余额: %d\n", amount, accounts["A"])
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			// 确认扣款，删除冻结记录
			delete(data, "frozen_a")
			fmt.Printf("  [Confirm-Debit] A 扣款确认\n")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			// 取消，解冻金额
			if frozen, ok := data["frozen_a"]; ok {
				accounts["A"] += frozen.(int)
				delete(data, "frozen_a")
				fmt.Printf("  [Cancel-Debit] A 解冻 %d, 余额: %d\n", frozen, accounts["A"])
			}
			return nil, nil
		},
	})

	// Participant 2: 加款服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "CreditService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			// 预留加款（记录待加金额）
			data["pending_b"] = amount
			fmt.Printf("  [Try-Credit] B 预留加款 %d\n", amount)
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			// 确认加款
			if pending, ok := data["pending_b"]; ok {
				accounts["B"] += pending.(int)
				delete(data, "pending_b")
				fmt.Printf("  [Confirm-Credit] B 加款确认, 余额: %d\n", accounts["B"])
			}
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			// 取消加款
			delete(data, "pending_b")
			fmt.Printf("  [Cancel-Credit] B 加款取消\n")
			return nil, nil
		},
	})

	if err := tx.Execute(); err != nil {
		fmt.Printf("  转账失败: %v\n", err)
	} else {
		fmt.Println("  转账成功!")
	}
}
