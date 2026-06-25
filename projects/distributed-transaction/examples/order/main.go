package main

import (
	"fmt"

	"distributed-transaction/coordinator"
	"distributed-transaction/participant"
	"distributed-transaction/saga"
	"distributed-transaction/tcc"
	"distributed-transaction/transaction"
)

// ============================================================
// 订单系统示例
//
// 场景：创建订单涉及多个服务：
//   - 库存服务：扣减库存
//   - 订单服务：创建订单
//   - 支付服务：扣款
//
// 演示 2PC、3PC、Saga、TCC 四种模式
// ============================================================

func main() {
	fmt.Println("========================================")
	fmt.Println("  分布式事务 - 订单系统示例")
	fmt.Println("========================================")
	fmt.Println()

	// 示例 1: 2PC 创建订单
	fmt.Println("--- 示例 1: 2PC 模式 ---")
	twoPCOrder()

	fmt.Println()

	// 示例 2: 3PC 创建订单
	fmt.Println("--- 示例 2: 3PC 模式 ---")
	threePCOrder()

	fmt.Println()

	// 示例 3: Saga 创建订单
	fmt.Println("--- 示例 3: Saga 模式 ---")
	sagaOrder()

	fmt.Println()

	// 示例 4: TCC 创建订单
	fmt.Println("--- 示例 4: TCC 模式 ---")
	tccOrder()
}

// twoPCOrder 使用 2PC 模式创建订单
func twoPCOrder() {
	coord := coordinator.NewCoordinator("order-coordinator")

	// 注册参与者
	inventoryCohort := participant.NewDefaultCohort("inventory-service")
	orderCohort := participant.NewDefaultCohort("order-service")
	paymentCohort := participant.NewDefaultCohort("payment-service")

	_ = coord.RegisterCohort(inventoryCohort)
	_ = coord.RegisterCohort(orderCohort)
	_ = coord.RegisterCohort(paymentCohort)

	tx := transaction.NewTransaction("order-2pc-001")
	tx.SetData("product_id", "SKU-12345")
	tx.SetData("quantity", 2)
	tx.SetData("amount", 199.99)

	result, err := coord.ExecuteTransaction(tx)
	if err != nil {
		fmt.Printf("  订单创建失败: %v\n", err)
	} else {
		fmt.Printf("  订单创建成功: %s\n", result)
	}
}

// threePCOrder 使用 3PC 模式创建订单
func threePCOrder() {
	coord := coordinator.NewThreePhaseCoordinator("order-3pc-coordinator")

	inventoryCohort := participant.NewDefaultCohort("inventory-service")
	orderCohort := participant.NewDefaultCohort("order-service")
	paymentCohort := participant.NewDefaultCohort("payment-service")

	_ = coord.RegisterCohort(inventoryCohort)
	_ = coord.RegisterCohort(orderCohort)
	_ = coord.RegisterCohort(paymentCohort)

	tx := transaction.NewTransaction("order-3pc-001")
	tx.SetData("product_id", "SKU-12345")
	tx.SetData("quantity", 2)
	tx.SetData("amount", 199.99)

	result, err := coord.ExecuteTransaction(tx)
	if err != nil {
		fmt.Printf("  订单创建失败: %v\n", err)
	} else {
		fmt.Printf("  订单创建成功: %s\n", result)
	}
}

// sagaOrder 使用 Saga 模式创建订单
func sagaOrder() {
	inventory := map[string]int{"SKU-12345": 10}
	orders := make([]string, 0)
	balance := 1000.0

	s := saga.NewSaga("order-saga-001")

	// Step 1: 扣减库存
	s.AddStep("ReserveInventory",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			sku := data["product_id"].(string)
			qty := data["quantity"].(int)
			if inventory[sku] < qty {
				return nil, fmt.Errorf("insufficient inventory: %s has %d, need %d", sku, inventory[sku], qty)
			}
			inventory[sku] -= qty
			fmt.Printf("  [库存] %s 库存扣减 %d, 剩余: %d\n", sku, qty, inventory[sku])
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			sku := data["product_id"].(string)
			qty := data["quantity"].(int)
			inventory[sku] += qty
			fmt.Printf("  [补偿-库存] %s 库存恢复: %d\n", sku, inventory[sku])
			return nil, nil
		},
	)

	// Step 2: 创建订单
	s.AddStep("CreateOrder",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			orderID := "ORD-001"
			orders = append(orders, orderID)
			data["order_id"] = orderID
			fmt.Printf("  [订单] 创建订单: %s\n", orderID)
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			if len(orders) > 0 {
				orders = orders[:len(orders)-1]
			}
			fmt.Printf("  [补偿-订单] 订单取消\n")
			return nil, nil
		},
	)

	// Step 3: 扣款
	s.AddStep("ProcessPayment",
		func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(float64)
			if balance < amount {
				return nil, fmt.Errorf("insufficient balance: have %.2f, need %.2f", balance, amount)
			}
			balance -= amount
			fmt.Printf("  [支付] 扣款 %.2f, 余额: %.2f\n", amount, balance)
			return nil, nil
		},
		func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(float64)
			balance += amount
			fmt.Printf("  [补偿-支付] 退款 %.2f, 余额: %.2f\n", amount, balance)
			return nil, nil
		},
	)

	s.Data["product_id"] = "SKU-12345"
	s.Data["quantity"] = 2
	s.Data["amount"] = 199.99

	if err := s.Execute(); err != nil {
		fmt.Printf("  订单创建失败: %v\n", err)
	} else {
		fmt.Println("  订单创建成功!")
	}
}

// tccOrder 使用 TCC 模式创建订单
func tccOrder() {
	inventory := map[string]int{"SKU-12345": 10}
	orders := make([]string, 0)
	balance := 1000.0

	tx := tcc.NewTCCTransaction("order-tcc-001")
	tx.Data["product_id"] = "SKU-12345"
	tx.Data["quantity"] = 2
	tx.Data["amount"] = 199.99

	// 库存服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "InventoryService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			sku := data["product_id"].(string)
			qty := data["quantity"].(int)
			if inventory[sku] < qty {
				return nil, fmt.Errorf("insufficient inventory")
			}
			inventory[sku] -= qty
			data["reserved_qty"] = qty
			fmt.Printf("  [Try-库存] %s 预留 %d, 剩余: %d\n", sku, qty, inventory[sku])
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			delete(data, "reserved_qty")
			fmt.Printf("  [Confirm-库存] 库存确认扣减\n")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			if qty, ok := data["reserved_qty"]; ok {
				sku := data["product_id"].(string)
				inventory[sku] += qty.(int)
				delete(data, "reserved_qty")
				fmt.Printf("  [Cancel-库存] %s 库存恢复: %d\n", sku, inventory[sku])
			}
			return nil, nil
		},
	})

	// 订单服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "OrderService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			orderID := "ORD-TCC-001"
			data["pending_order"] = orderID
			fmt.Printf("  [Try-订单] 预创建订单: %s\n", orderID)
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			if orderID, ok := data["pending_order"]; ok {
				orders = append(orders, orderID.(string))
				delete(data, "pending_order")
				data["order_id"] = orderID
				fmt.Printf("  [Confirm-订单] 订单确认: %s\n", orderID)
			}
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			delete(data, "pending_order")
			fmt.Printf("  [Cancel-订单] 订单取消\n")
			return nil, nil
		},
	})

	// 支付服务
	tx.RegisterParticipant(&tcc.TCCParticipant{
		Name: "PaymentService",
		Try: func(data map[string]interface{}) (map[string]interface{}, error) {
			amount := data["amount"].(float64)
			if balance < amount {
				return nil, fmt.Errorf("insufficient balance")
			}
			balance -= amount
			data["frozen_amount"] = amount
			fmt.Printf("  [Try-支付] 冻结 %.2f, 余额: %.2f\n", amount, balance)
			return nil, nil
		},
		Confirm: func(data map[string]interface{}) (map[string]interface{}, error) {
			delete(data, "frozen_amount")
			fmt.Printf("  [Confirm-支付] 支付确认\n")
			return nil, nil
		},
		Cancel: func(data map[string]interface{}) (map[string]interface{}, error) {
			if amount, ok := data["frozen_amount"]; ok {
				balance += amount.(float64)
				delete(data, "frozen_amount")
				fmt.Printf("  [Cancel-支付] 退款 %.2f, 余额: %.2f\n", amount, balance)
			}
			return nil, nil
		},
	})

	if err := tx.Execute(); err != nil {
		fmt.Printf("  订单创建失败: %v\n", err)
	} else {
		fmt.Println("  订单创建成功!")
	}
}
