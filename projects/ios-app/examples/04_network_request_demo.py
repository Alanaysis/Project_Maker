"""
示例 4: 网络请求演示
Network Request Demo

演示 iOS URLSession 网络请求机制。
"""

import sys
import json
sys.path.insert(0, "/home/siok/project_copyninja/projects/ios-app")

from src.network import (
    URLSession, URLRequest, URLResponse, URLResponseError,
    URLSessionDataTask, NetworkManager, HTTPMethod,
)
from src.binding import Observable, ViewModel


def demo_url_session():
    """演示 URLSession 基本用法"""
    print("=" * 60)
    print("  URLSession 基本用法")
    print("=" * 60 + "\n")

    # 1. 创建会话
    session = URLSession(base_url="https://api.example.com")
    session.set_default_header("Authorization", "Bearer token123")

    print(f"创建会话: {session}")

    # 2. GET 请求
    print("\n--- GET 请求 ---")
    users_data = [None]

    def users_handler(data, response, error):
        if error:
            print(f"  错误: {error}")
        else:
            print(f"  状态码: {response.status_code}")
            print(f"  Headers: {response.headers}")
            if data:
                users_data[0] = data
                print(f"  数据: {json.dumps(data, ensure_ascii=False, indent=4)}")

    get_task = session.get("/api/users", completion_handler=users_handler)
    print(f"创建任务: {get_task}")
    get_task.start()

    # 3. POST 请求
    print("\n--- POST 请求 ---")

    def post_handler(data, response, error):
        if error:
            print(f"  错误: {error}")
        else:
            print(f"  状态码: {response.status_code}")
            if data:
                print(f"  响应: {data}")

    post_body = {"name": "新用户", "email": "new@example.com"}
    post_task = session.post("/api/users", body=post_body, completion_handler=post_handler)
    print(f"创建任务: {post_task}")
    print(f"请求体: {json.dumps(post_body, ensure_ascii=False)}")
    post_task.start()

    # 4. 自定义 URLRequest
    print("\n--- 自定义 URLRequest ---")
    custom_request = URLRequest("/api/status", HTTPMethod.GET)
    custom_request.add_header("Accept", "application/json")
    custom_request.add_header("X-Custom-Header", "test-value")

    def custom_handler(data, response, error):
        if not error and data:
            print(f"  状态: {data.get('status', 'unknown')}")

    custom_task = session.data_task_with_request(custom_request, custom_handler)
    custom_task.start()

    # 5. 模拟错误
    print("\n--- 错误处理 ---")
    error_request = URLRequest("/api/not-found")
    error_request.method = HTTPMethod.GET

    def error_handler(data, response, error):
        if error:
            print(f"  捕获错误: {error}")
        else:
            print(f"  响应: {response}")

    error_task = session.data_task_with_request(error_request, error_handler)
    error_task.start()

    return session


def demo_network_manager():
    """演示 NetworkManager 高层 API"""
    print("\n" + "=" * 60)
    print("  NetworkManager 高层 API")
    print("=" * 60 + "\n")

    # 1. 创建网络管理器
    manager = NetworkManager(base_url="https://api.example.com")
    manager.add_mock_handler("/api/users", lambda req: (
        URLResponse(200, {"Content-Type": "application/json"}, req.url),
        {"users": [{"id": 1, "name": "模拟用户"}], "total": 1},
        None
    ))

    print(f"创建网络管理器: {manager}")

    # 2. GET 请求
    print("\n--- GET /api/users ---")
    manager.get("/api/users",
                headers={"X-Request-ID": "12345"},
                completion=lambda data, response, error: print(
                    f"  响应: {json.dumps(data, ensure_ascii=False, indent=4) if data else 'None'}"
                ))

    # 3. POST 请求
    print("\n--- POST /api/posts ---")
    manager.post("/api/posts",
                 body={"title": "新文章", "content": "文章内容"},
                 completion=lambda data, response, error: print(
                     f"  响应: {json.dumps(data, ensure_ascii=False, indent=4) if data else 'None'}"
                 ))

    # 4. 带查询参数的 GET
    print("\n--- GET /api/users?limit=10&offset=0 ---")
    manager.get("/api/users",
                params={"limit": "10", "offset": "0"},
                completion=lambda data, response, error: print(
                    f"  响应: {json.dumps(data, ensure_ascii=False, indent=4) if data else 'None'}"
                ))

    # 5. PUT 请求
    print("\n--- PUT /api/users/1 ---")
    manager.put("/api/users/1",
                body={"name": "更新后的名字"},
                completion=lambda data, response, error: print(
                    f"  响应: {json.dumps(data, ensure_ascii=False, indent=4) if data else 'None'}"
                ))

    # 6. DELETE 请求
    print("\n--- DELETE /api/users/1 ---")
    manager.delete("/api/users/1",
                   completion=lambda data, response, error: print(
                       f"  响应: {json.dumps(data, ensure_ascii=False, indent=4) if data else 'None'}"
                   ))

    return manager


def demo_network_with_binding():
    """演示网络请求与数据绑定结合"""
    print("\n" + "=" * 60)
    print("  网络请求 + 数据绑定")
    print("=" * 60 + "\n")

    # 创建 ViewModel
    class UserViewModel(ViewModel):
        def __init__(self):
            super().__init__("UserViewModel")
            self.set_value("userName", "")
            self.set_value("userEmail", "")
            self.set_value("isLoading", False)
            self.set_value("errorMessage", "")

        def load_user(self, user_id: int):
            """加载用户数据"""
            self.set_value("isLoading", True)
            self.set_value("errorMessage", "")

            session = URLSession("https://api.example.com")

            def completion(data, response, error):
                if error:
                    self.set_value("errorMessage", str(error))
                    self.set_value("isLoading", False)
                elif data and "users" in data:
                    user = data["users"][0]
                    self.set_value("userName", user.get("name", ""))
                    self.set_value("userEmail", user.get("email", ""))
                    self.set_value("isLoading", False)
                else:
                    self.set_value("errorMessage", "数据加载失败")
                    self.set_value("isLoading", False)

            session.get(f"/api/users", completion_handler=completion)

    # 创建 ViewModel
    vm = UserViewModel()

    # 添加观察者
    print("添加观察者:")
    vm.add_observer("userName", lambda obs, old, new:
                    print(f"  [观察者] userName: {old!r} -> {new!r}"))
    vm.add_observer("isLoading", lambda obs, old, new:
                    print(f"  [观察者] isLoading: {old!r} -> {new!r}"))
    vm.add_observer("errorMessage", lambda obs, old, new:
                    print(f"  [观察者] errorMessage: {old!r} -> {new!r}"))

    # 加载用户
    print("\n加载用户 (ID=1):")
    vm.load_user(1)

    # 展示结果
    print(f"\n最终状态:")
    print(f"  userName: {vm.get_value('userName')}")
    print(f"  userEmail: {vm.get_value('userEmail')}")
    print(f"  isLoading: {vm.get_value('isLoading')}")
    print(f"  errorMessage: {vm.get_value('errorMessage')}")

    return vm


def demo_url_session_task_lifecycle():
    """演示任务生命周期"""
    print("\n" + "=" * 60)
    print("  URLSessionTask 生命周期")
    print("=" * 60 + "\n")

    session = URLSession()

    # 创建任务
    request = URLRequest("/api/status", HTTPMethod.GET)
    task = session.data_task_with_request(
        request,
        completion=lambda data, response, error: print(f"  回调: status={response.status_code if response else 'None'}")
    )

    print(f"创建任务: {task}")
    print(f"  已取消: {task.is_cancelled}")
    print(f"  已暂停: {task.is_suspended}")

    # 暂停
    print("\n暂停任务...")
    task.suspend()
    print(f"  已暂停: {task.is_suspended}")

    # 恢复
    print("\n恢复任务...")
    task.resume()

    # 取消
    print("\n取消任务...")
    task.cancel()
    print(f"  已取消: {task.is_cancelled}")

    # 创建新任务并取消
    request2 = URLRequest("/api/other", HTTPMethod.GET)
    task2 = session.data_task_with_request(request2)
    print(f"\n创建新任务: {task2}")
    task2.cancel()
    print(f"  已取消: {task2.is_cancelled}")

    # 取消所有任务
    session.cancel_all_tasks()

    return session


def main():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("  iOS 基础应用 - 网络请求演示")
    print("  iOS Basic Application - Network Request Demo")
    print("=" * 60 + "\n")

    session = demo_url_session()
    manager = demo_network_manager()
    vm = demo_network_with_binding()
    task_session = demo_url_session_task_lifecycle()

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("  Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
