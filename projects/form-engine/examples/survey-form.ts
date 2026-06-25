/**
 * 调查问卷示例
 *
 * 演示：
 * - 复杂表单结构
 * - 多种字段类型组合
 * - 条件验证
 */

import { FormEngine, FormRenderer, rules, FormSchema } from '../src';

// 定义调查问卷 Schema
const surveySchema: FormSchema = {
  title: '开发者调查问卷',
  description: '帮助我们了解开发者的工作习惯',
  submitText: '提交问卷',
  fields: [
    {
      name: 'name',
      type: 'text',
      label: '姓名',
      placeholder: '请输入您的姓名',
      validation: [rules.required()]
    },
    {
      name: 'experience',
      type: 'select',
      label: '开发经验',
      options: [
        { label: '请选择', value: '' },
        { label: '0-1 年', value: '0-1' },
        { label: '1-3 年', value: '1-3' },
        { label: '3-5 年', value: '3-5' },
        { label: '5-10 年', value: '5-10' },
        { label: '10 年以上', value: '10+' }
      ],
      validation: [rules.custom(v => v !== '', '请选择开发经验')]
    },
    {
      name: 'languages',
      type: 'checkbox',
      label: '常用编程语言（可多选）',
      description: 'JavaScript/TypeScript, Python, Java, Go, Rust 等'
    },
    {
      name: 'workStyle',
      type: 'radio',
      label: '工作方式',
      options: [
        { label: '远程办公', value: 'remote' },
        { label: '现场办公', value: 'onsite' },
        { label: '混合办公', value: 'hybrid' }
      ],
      defaultValue: 'hybrid'
    },
    {
      name: 'satisfaction',
      type: 'number',
      label: '工作满意度 (1-10)',
      placeholder: '请输入 1-10 的数字',
      defaultValue: 5,
      validation: [
        rules.min(1, '最低分为 1'),
        rules.max(10, '最高分为 10')
      ]
    },
    {
      name: 'feedback',
      type: 'textarea',
      label: '其他建议',
      placeholder: '请分享您的想法...',
      validation: [
        rules.maxLength(500, '最多500个字符')
      ]
    },
    {
      name: 'contact',
      type: 'checkbox',
      label: '愿意接受后续访谈',
      defaultValue: false
    },
    {
      name: 'email',
      type: 'email',
      label: '联系邮箱',
      placeholder: '请输入邮箱',
      description: '如果您愿意接受访谈，请填写邮箱',
      dependsOn: {
        field: 'contact',
        value: true
      },
      validation: [
        rules.email('请输入有效的邮箱地址')
      ]
    }
  ]
};

// 创建表单引擎实例
const engine = new FormEngine(surveySchema);
const renderer = new FormRenderer();

// 注册提交回调
engine.onSubmit(async (values) => {
  console.log('\n[提交] 问卷结果:');
  console.log(`  姓名: ${values.name}`);
  console.log(`  开发经验: ${values.experience} 年`);
  console.log(`  工作方式: ${values.workStyle}`);
  console.log(`  满意度: ${values.satisfaction}/10`);
  console.log(`  愿意访谈: ${values.contact ? '是' : '否'}`);
  if (values.contact) {
    console.log(`  联系邮箱: ${values.email}`);
  }
  console.log('\n感谢您的参与!');
});

// 模拟用户操作
console.log('=== 开发者调查问卷示例 ===\n');

// 1. 显示初始表单
console.log('1. 初始表单 (JSON):');
const initialJson = renderer.renderAsJson(surveySchema, engine.getState());
console.log(initialJson.content);

// 2. 用户填写
console.log('\n2. 用户填写:');
engine.setValue('name', '张三');
engine.setValue('experience', '3-5');
engine.setValue('satisfaction', 8);
engine.setValue('feedback', '希望有更多学习资源');
engine.setValue('contact', true);
engine.setValue('email', 'zhangsan@example.com');

// 3. 显示字段可见性
console.log('\n3. 字段可见性:');
for (const field of surveySchema.fields) {
  const visible = engine.isFieldVisible(field);
  console.log(`  ${visible ? '✓' : '✗'} ${field.label}`);
}

// 4. 验证并显示结果
console.log('\n4. 验证结果:');
const isValid = engine.validate();
console.log(`表单有效: ${isValid}`);

for (const field of surveySchema.fields) {
  if (!engine.isFieldVisible(field)) continue;

  const fieldState = engine.getFieldState(field.name);
  if (fieldState) {
    const status = fieldState.valid ? '✓' : '✗';
    console.log(`  ${status} ${field.label}: ${JSON.stringify(fieldState.value)}`);
  }
}

// 5. 提交
console.log('\n5. 提交问卷:');
engine.submit().then(success => {
  console.log(`提交结果: ${success ? '成功' : '失败'}`);
});

// 6. 测试条件字段隐藏
console.log('\n6. 取消访谈意愿:');
engine.setValue('contact', false);

console.log('字段可见性:');
for (const field of surveySchema.fields) {
  const visible = engine.isFieldVisible(field);
  console.log(`  ${visible ? '✓' : '✗'} ${field.label}`);
}

// 7. 重置表单
console.log('\n7. 重置表单:');
engine.reset();
const resetState = engine.getState();
console.log(`姓名: ${resetState.values['name']}`);
console.log(`满意度: ${resetState.values['satisfaction']}`);
