/**
 * 示例：计算属性
 *
 * 演示 computed() 的惰性求值和缓存特性。
 */

import { reactive, computed, watch } from '../src';

// 购物车示例
const cart = reactive({
  items: [
    { name: '苹果', price: 5, quantity: 3 },
    { name: '香蕉', price: 3, quantity: 5 },
    { name: '橙子', price: 8, quantity: 2 },
  ],
  discount: 0.9, // 9折
});

// 计算总数量
const totalQuantity = computed(() =>
  cart.items.reduce((sum, item) => sum + item.quantity, 0)
);

// 计算原价总金额
const subtotal = computed(() =>
  cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0)
);

// 计算折后总金额（依赖其他 computed）
const total = computed(() => subtotal.value * cart.discount);

// 侦听总金额变化
watch(
  () => total.value,
  (newVal, oldVal) => {
    console.log(`  总金额: ${oldVal?.toFixed(2)} -> ${newVal.toFixed(2)}`);
  }
);

console.log('=== 购物车计算属性示例 ===\n');

console.log('初始状态:');
console.log(`  商品数量: ${totalQuantity.value}`);
console.log(`  原价: ${subtotal.value.toFixed(2)}`);
console.log(`  折后: ${total.value.toFixed(2)}`);

console.log('\n添加一个苹果:');
cart.items[0].quantity += 1;
console.log(`  商品数量: ${totalQuantity.value}`);
console.log(`  原价: ${subtotal.value.toFixed(2)}`);
console.log(`  折后: ${total.value.toFixed(2)}`);

console.log('\n修改折扣为8折:');
cart.discount = 0.8;
console.log(`  折后: ${total.value.toFixed(2)}`);

// 验证缓存：不修改数据时多次访问不重新求值
console.log('\n验证缓存（连续访问3次）:');
let evalCount = 0;
const cached = computed(() => {
  evalCount++;
  return subtotal.value;
});

console.log(`  第1次: ${cached.value} (evalCount: ${evalCount})`);
console.log(`  第2次: ${cached.value} (evalCount: ${evalCount})`);
console.log(`  第3次: ${cached.value} (evalCount: ${evalCount})`);
console.log(`  -> 求值函数只执行了1次，证明缓存生效`);
