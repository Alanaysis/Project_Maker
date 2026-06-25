// 代码编辑器演示代码

// 1. 基础类型定义
interface Position {
  line: number;
  column: number;
}

interface Range {
  start: Position;
  end: Position;
}

// 2. 用户管理示例
interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

class UserManager {
  private users: User[] = [];

  constructor() {
    // 初始化示例数据
    this.users = [
      { id: 1, name: 'Alice', email: 'alice@example.com', role: 'admin' },
      { id: 2, name: 'Bob', email: 'bob@example.com', role: 'user' },
      { id: 3, name: 'Charlie', email: 'charlie@example.com', role: 'guest' }
    ];
  }

  // 添加用户
  addUser(user: Omit<User, 'id'>): User {
    const newUser: User = {
      ...user,
      id: this.users.length + 1
    };
    this.users.push(newUser);
    return newUser;
  }

  // 查找用户
  findUser(id: number): User | undefined {
    return this.users.find(u => u.id === id);
  }

  // 按角色筛选
  getUsersByRole(role: User['role']): User[] {
    return this.users.filter(u => u.role === role);
  }

  // 获取所有用户
  getAllUsers(): User[] {
    return [...this.users];
  }
}

// 3. 数学工具函数
function fibonacci(n: number): number {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

function factorial(n: number): number {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// 4. 字符串处理
function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function camelCase(str: string): string {
  return str
    .split(/[-_\s]+/)
    .map((word, index) =>
      index === 0 ? word.toLowerCase() : capitalize(word)
    )
    .join('');
}

// 5. 异步操作示例
async function fetchUserData(userId: number): Promise<User | null> {
  // 模拟 API 调用
  return new Promise((resolve) => {
    setTimeout(() => {
      const userManager = new UserManager();
      const user = userManager.findUser(userId);
      resolve(user || null);
    }, 100);
  });
}

// 6. 使用示例
async function main() {
  // 用户管理
  const userManager = new UserManager();

  console.log('所有用户:', userManager.getAllUsers());
  console.log('管理员:', userManager.getUsersByRole('admin'));

  // 添加新用户
  const newUser = userManager.addUser({
    name: 'David',
    email: 'david@example.com',
    role: 'user'
  });
  console.log('新用户:', newUser);

  // 数学计算
  console.log('Fibonacci(10):', fibonacci(10));
  console.log('Factorial(5):', factorial(5));

  // 字符串处理
  console.log('Capitalize:', capitalize('hello world'));
  console.log('CamelCase:', camelCase('hello-world-example'));

  // 异步操作
  const user = await fetchUserData(1);
  console.log('获取用户:', user);
}

// 运行示例
main().catch(console.error);
