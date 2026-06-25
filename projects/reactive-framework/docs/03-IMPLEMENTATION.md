# 03 - 实现细节

## 1. Proxy Handler 实现

### 1.1 get 拦截器

```typescript
get(target, key, receiver) {
  const value = Reflect.get(target, key, receiver);

  // 依赖收集
  if (Dep.target) {
    const dep = getDep(target, key);
    dep.depend();
  }

  // 递归代理嵌套对象
  if (isPlainObject(value)) {
    return reactive(value);
  }

  return value;
}
```

关键点：
- `Dep.target` 检查：只有在 Watcher 求值过程中才收集依赖
- `getDep()`：获取或创建该属性的 Dep 实例
- 惰性代理：嵌套对象在首次访问时才转为响应式

### 1.2 set 拦截器

```typescript
set(target, key, value, receiver) {
  const oldValue = (target as any)[key];
  const result = Reflect.set(target, key, value, receiver);

  // 值变化时通知
  if (oldValue !== value) {
    const dep = getDep(target, key);
    dep.notify();
  }

  return result;
}
```

关键点：
- 先取旧值再设置新值
- 值比较：只有真正变化才触发更新（避免无限循环）
- `Reflect.set`：正确处理原型链和 receiver

### 1.3 deleteProperty 拦截器

```typescript
deleteProperty(target, key) {
  const hadKey = key in target;
  const result = Reflect.deleteProperty(target, key);

  if (hadKey && result) {
    const dep = getDep(target, key);
    dep.notify();
  }

  return result;
}
```

## 2. 依赖收集机制

### 2.1 Dep 类

```typescript
class Dep {
  static target: Watcher | null;  // 全局唯一活跃 Watcher
  subs: Set<Watcher>;             // 订阅者集合

  depend(): void {
    if (Dep.target) {
      this.subs.add(Dep.target);
    }
  }

  notify(): void {
    for (const sub of this.subs) {
      sub.update();
    }
  }
}
```

### 2.2 Watcher 栈

```typescript
const targetStack: Watcher[] = [];

function pushTarget(target: Watcher): void {
  targetStack.push(target);
  Dep.target = target;
}

function popTarget(): void {
  targetStack.pop();
  Dep.target = targetStack[targetStack.length - 1] || null;
}
```

为什么需要栈？—— 支持嵌套求值场景：
- computed A 依赖 computed B
- 求值 A 时，需要先求值 B
- B 求值完成后，Dep.target 需要恢复为 A

### 2.3 收集流程图

```
Watcher.get()
    │
    ├─ pushTarget(this)     // 将自己设为活跃 Watcher
    │
    ├─ 执行 getter()        // 触发 proxy.get
    │     │
    │     ├─ 读取 propA ──► depA.depend() ──► depA.subs.add(this)
    │     ├─ 读取 propB ──► depB.depend() ──► depB.subs.add(this)
    │     └─ 返回值
    │
    └─ popTarget()          // 恢复上一个 Watcher
```

## 3. 计算属性实现

```typescript
function computed<T>(getter: () => T): ComputedRef<T> {
  const watcher = new Watcher(getter, null, { lazy: true });

  return {
    get value(): T {
      if (watcher.dirty) {
        watcher.evaluate();  // 重新求值
      }
      if (Dep.target) {
        watcher.depend();    // 依赖传递
      }
      return watcher.value;
    },
  };
}
```

### 3.1 惰性求值原理

```
初始状态: dirty = true

访问 computed.value:
  if (dirty) {
    watcher.evaluate()   // 执行 getter，收集新依赖
    dirty = false        // 标记为已求值
  }
  return cached value

依赖变化时:
  watcher.update()
    → dirty = true       // 标记为脏，下次访问重新求值
```

### 3.2 依赖传递

```
watcher X 依赖 computed A
computed A 依赖 state.x 和 state.y

问题：state.x 变化时，watcher X 也需要被通知

解决：computed.value 的 getter 中调用 watcher.depend()
  → 将 computed 自身的依赖（state.x, state.y）也收集到 watcher X 中
```

## 4. Watch API 实现

```typescript
function watch<T>(
  source: () => T,
  callback: (newVal: T, oldVal: T) => void,
  options: WatchOptions = {}
): () => void {
  const watcher = new Watcher(source, callback, options);
  return () => watcher.teardown();  // 返回取消函数
}
```

### 4.1 immediate 选项

```typescript
// 在 Watcher 构造函数中
if (options.immediate && this.callback) {
  this.callback(this.value, undefined);
}
```

### 4.2 异步更新队列

```typescript
const queue: Watcher[] = [];
let waiting = false;

function queueWatcher(watcher: Watcher): void {
  if (!has.has(watcher)) {
    has.add(watcher);
    queue.push(watcher);
    if (!waiting) {
      waiting = true;
      Promise.resolve().then(flushQueue);  // 微任务
    }
  }
}
```

为什么要异步？—— 合并多次同步更新：
```typescript
state.a = 1;  // 触发 watcher.update()
state.b = 2;  // 触发 watcher.update()
state.c = 3;  // 触发 watcher.update()
// 同步代码结束，微任务执行，只更新一次
```

## 5. WeakMap 缓存策略

```typescript
// 避免重复代理
const proxyMap: WeakMap<object, object> = new WeakMap();  // raw → proxy
const rawMap: WeakMap<object, object> = new WeakMap();    // proxy → raw
const depsMap: WeakMap<object, Map<string, Dep>> = new WeakMap(); // 依赖
```

为什么用 WeakMap？
- 键是弱引用：当原始对象被回收时，对应的缓存也会被回收
- 避免内存泄漏
- 自动清理不需要的代理和依赖

## 6. 性能优化

### 6.1 惰性代理
嵌套对象只在访问时才代理，避免初始化时的性能开销。

### 6.2 Set 去重
使用 Set 存储订阅者，自动去重。

### 6.3 值比较
set 拦截器中比较新旧值，相同值不触发更新。

### 6.4 更新队列
将多个同步更新合并为一次异步更新。
