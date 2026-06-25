/**
 * 条件字段示例
 *
 * 演示：
 * - dependsOn 条件字段显示
 * - 动态字段可见性
 * - 条件验证
 */

import { FormEngine, FormRenderer, rules, FormSchema } from '../src';

// 定义带条件字段的表单
const conditionalSchema: FormSchema = {
  title: '支付信息',
  description: '请选择支付方式并填写相关信息',
  submitText: '确认支付',
  fields: [
    {
      name: 'paymentMethod',
      type: 'radio',
      label: '支付方式',
      options: [
        { label: '信用卡', value: 'credit_card' },
        { label: '支付宝', value: 'alipay' },
        { label: '银行转账', value: 'bank_transfer' }
      ],
      defaultValue: 'credit_card'
    },
    // 信用卡字段 - 依赖 paymentMethod === 'credit_card'
    {
      name: 'cardNumber',
      type: 'text',
      label: '卡号',
      placeholder: '请输入16位卡号',
      dependsOn: {
        field: 'paymentMethod',
        value: 'credit_card'
      },
      validation: [
        rules.required('请输入卡号'),
        rules.pattern(/^\d{16}$/, '卡号必须为16位数字')
      ]
    },
    {
      name: 'cardExpiry',
      type: 'text',
      label: '有效期',
      placeholder: 'MM/YY',
      dependsOn: {
        field: 'paymentMethod',
        value: 'credit_card'
      },
      validation: [
        rules.required('请输入有效期'),
        rules.pattern(/^\d{2}\/\d{2}$/, '格式: MM/YY')
      ]
    },
    {
      name: 'cardCvv',
      type: 'password',
      label: 'CVV',
      placeholder: '3位安全码',
      dependsOn: {
        field: 'paymentMethod',
        value: 'credit_card'
      },
      validation: [
        rules.required('请输入CVV'),
        rules.pattern(/^\d{3}$/, 'CVV必须为3位数字')
      ]
    },
    // 支付宝字段 - 依赖 paymentMethod === 'alipay'
    {
      name: 'alipayAccount',
      type: 'text',
      label: '支付宝账号',
      placeholder: '手机号或邮箱',
      dependsOn: {
        field: 'paymentMethod',
        value: 'alipay'
      },
      validation: [
        rules.required('请输入支付宝账号')
      ]
    },
    // 银行转账字段 - 依赖 paymentMethod === 'bank_transfer'
    {
      name: 'bankName',
      type: 'select',
      label: '银行',
      options: [
        { label: '请选择', value: '' },
        { label: '工商银行', value: 'icbc' },
        { label: '建设银行', value: 'ccb' },
        { label: '农业银行', value: 'abc' },
        { label: '中国银行', value: 'boc' }
      ],
      dependsOn: {
        field: 'paymentMethod',
        value: 'bank_transfer'
      },
      validation: [
        rules.custom(v => v !== '', '请选择银行')
      ]
    },
    {
      name: 'bankAccount',
      type: 'text',
      label: '银行卡号',
      placeholder: '请输入银行卡号',
      dependsOn: {
        field: 'paymentMethod',
        value: 'bank_transfer'
      },
      validation: [
        rules.required('请输入银行卡号'),
        rules.pattern(/^\d{16,19}$/, '卡号必须为16-19位数字')
      ]
    },
    // 通用字段 - 不依赖任何条件
    {
      name: 'amount',
      type: 'number',
      label: '支付金额',
      placeholder: '请输入金额',
      validation: [
        rules.required('请输入金额'),
        rules.min(0.01, '金额必须大于0')
      ]
    },
    {
      name: 'note',
      type: 'textarea',
      label: '备注',
      placeholder: '可选备注信息',
      validation: [
        rules.maxLength(200, '备注最多200个字符')
      ]
    }
  ]
};

// 创建表单引擎
const engine = new FormEngine(conditionalSchema);
const renderer = new FormRenderer();

// 注册提交回调
engine.onSubmit(async (values) => {
  console.log('\n[提交] 支付信息:');
  console.log(`  支付方式: ${values.paymentMethod}`);
  console.log(`  金额: ¥${values.amount}`);
  if (values.paymentMethod === 'credit_card') {
    console.log(`  卡号: ${values.cardNumber}`);
  } else if (values.paymentMethod === 'alipay') {
    console.log(`  支付宝: ${values.alipayAccount}`);
  } else if (values.paymentMethod === 'bank_transfer') {
    console.log(`  银行: ${values.bankName}`);
    console.log(`  卡号: ${values.bankAccount}`);
  }
  console.log('\n支付处理中...');
  await new Promise(resolve => setTimeout(resolve, 500));
  console.log('支付成功!');
});

// 模拟完整流程
console.log('=== 条件字段示例 - 支付信息 ===\n');

// 场景 1: 信用卡支付
console.log('--- 场景 1: 信用卡支付 ---\n');

console.log('1. 选择信用卡支付:');
console.log('可见字段:');
for (const field of conditionalSchema.fields) {
  const visible = engine.isFieldVisible(field);
  if (visible) console.log(`  - ${field.label}`);
}

console.log('\n2. 填写信用卡信息:');
engine.setValue('cardNumber', '4111111111111111');
engine.setValue('cardExpiry', '12/25');
engine.setValue('cardCvv', '123');
engine.setValue('amount', 99.99);
engine.setValue('note', '购买会员');

console.log('\n3. 验证:');
engine.validate();
for (const field of conditionalSchema.fields) {
  if (!engine.isFieldVisible(field)) continue;
  const fieldState = engine.getFieldState(field.name);
  if (fieldState) {
    const status = fieldState.valid ? '✓' : '✗';
    console.log(`  ${status} ${field.label}: ${fieldState.value}`);
    if (!fieldState.valid) {
      console.log(`    错误: ${fieldState.errors.map(e => e.message).join(', ')}`);
    }
  }
}

console.log('\n4. 提交:');
engine.submit().then(() => {
  // 场景 2: 切换到支付宝
  console.log('\n\n--- 场景 2: 切换到支付宝 ---\n');

  engine.reset();
  engine.setValue('paymentMethod', 'alipay');

  console.log('1. 选择支付宝:');
  console.log('可见字段:');
  for (const field of conditionalSchema.fields) {
    const visible = engine.isFieldVisible(field);
    if (visible) console.log(`  - ${field.label}`);
  }

  console.log('\n2. 填写支付宝信息:');
  engine.setValue('alipayAccount', 'user@example.com');
  engine.setValue('amount', 50);

  console.log('\n3. 提交:');
  engine.submit().then(() => {
    // 场景 3: 渲染为 HTML
    console.log('\n\n--- 场景 3: HTML 渲染 ---\n');

    const engine3 = new FormEngine(conditionalSchema);
    engine3.setValue('paymentMethod', 'credit_card');
    engine3.setValue('cardNumber', '4111111111111111');
    engine3.setValue('cardExpiry', '12/25');
    engine3.setValue('cardCvv', '123');
    engine3.setValue('amount', 100);

    const htmlResult = renderer.render(conditionalSchema, engine3.getState());
    console.log('HTML 输出:');
    console.log(htmlResult.content);
  });
});
