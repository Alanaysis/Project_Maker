"""
网络请求模块 - Network Request Module

本模块模拟 iOS URLSession 网络请求机制：
- URLSession: 网络会话
- URLRequest: 网络请求
- URLSessionDataTask: 数据任务
- 异步回调机制
"""

import time
import json
import threading
from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from urllib.parse import urlencode


class HTTPMethod(Enum):
    """HTTP 请求方法 - 类比 HTTPMethod"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"


class URLRequest:
    """
    URLRequest 模拟器 - 模拟 iOS URLRequest

    URLRequest 封装了 HTTP 请求的所有信息：
    - URL
    - HTTP Method
    - Headers
    - Body
    """

    def __init__(self, url: str, method: HTTPMethod = HTTPMethod.GET):
        self.url = url
        self._method = method
        self._headers: Dict[str, str] = {}
        self._body: Optional[Any] = None
        self._timeout: float = 30.0

    @property
    def method(self) -> str:
        return self._method.value

    @method.setter
    def method(self, value: HTTPMethod):
        self._method = value

    def add_header(self, key: str, value: str):
        """添加请求头 - 模拟 setValue:forHTTPHeaderField:"""
        self._headers[key] = value
        print(f"[URLRequest] 添加请求头: {key} = {value}")

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers.copy()

    @property
    def body(self) -> Optional[Any]:
        return self._body

    @body.setter
    def body(self, value: Any):
        self._body = value

    def set_body_json(self, data: Dict[str, Any]):
        """设置 JSON body"""
        self._body = json.dumps(data)
        self.add_header("Content-Type", "application/json")

    def __repr__(self):
        return (f"<URLRequest {self._method.value} {self.url} "
                f"headers={len(self._headers)} "
                f"body={'[JSON]' if self._body else 'None'}>")


class URLResponse:
    """URLResponse 模拟器 - 模拟 iOS URLResponse"""

    def __init__(self, status_code: int = 200, headers: Optional[Dict[str, str]] = None,
                 url: str = ""):
        self.status_code = status_code
        self._headers = headers or {}
        self.url = url
        self._suggested_filename: str = ""

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers.copy()

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def __repr__(self):
        return f"<URLResponse {self.status_code} {self.url}>"


class URLResponseError(Exception):
    """URLResponse 错误 - 模拟 NSError"""

    def __init__(self, code: int, message: str, domain: str = "NSURLErrorDomain"):
        self.code = code
        self.message = message
        self.domain = domain
        super().__init__(f"[{domain}] {code}: {message}")


class URLSessionDataTask:
    """
    URLSessionDataTask 模拟器 - 模拟 iOS 数据任务

    数据任务处理异步网络请求：
    - start(): 开始请求
    - cancel(): 取消请求
    - 回调: completionHandler(data, response, error)
    """

    def __init__(self, session: "URLSession", request: URLRequest,
                 completion_handler: Optional[Callable] = None):
        self.session = session
        self.request = request
        self._completion_handler = completion_handler
        self._task_id = id(self)
        self._is_cancelled = False
        self._is_suspended = False
        self._priority: float = 0.5

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def is_suspended(self) -> bool:
        return self._is_suspended

    def start(self):
        """
        开始任务 - 模拟 resume()

        异步执行网络请求。
        """
        if self._is_cancelled:
            print(f"[URLSessionDataTask] 任务已取消: {self.request.url}")
            return

        if self._is_suspended:
            self._is_suspended = False

        print(f"[URLSessionDataTask] 开始任务: {self.request.method} {self.request.url}")

        # 模拟网络请求
        response, data, error = self.session._simulate_request(self.request)

        # 执行回调
        if self._completion_handler:
            self._completion_handler(data, response, error)

        if error:
            print(f"[URLSessionDataTask] 任务错误: {error}")
        elif response and response.is_success:
            print(f"[URLSessionDataTask] 任务完成: {response.status_code}")
        else:
            print(f"[URLSessionDataTask] 任务完成: {response.status_code if response else 'No response'}")

    def cancel(self):
        """取消任务 - 模拟 cancel()"""
        self._is_cancelled = True
        print(f"[URLSessionDataTask] 取消任务: {self.request.url}")

    def suspend(self):
        """暂停任务"""
        self._is_suspended = True

    def resume(self):
        """恢复任务"""
        self._is_suspended = False
        self.start()

    def __repr__(self):
        return (f"<URLSessionDataTask {self.request.method} {self.request.url} "
                f"cancelled={self._is_cancelled}>")


class URLSession:
    """
    URLSession 模拟器 - 模拟 iOS URLSession

    URLSession 是 iOS 网络请求的核心类：
    - 管理网络会话配置
    - 创建数据任务
    - 处理并发请求
    - 管理缓存

    在 Python 中，我们模拟 HTTP 请求的响应。
    """

    def __init__(self, base_url: str = "", config: Optional[Dict[str, Any]] = None):
        self.base_url = base_url
        self._config = config or {}
        self._default_headers: Dict[str, str] = {
            "User-Agent": "iOS-App/1.0",
            "Accept": "application/json",
        }
        self._delegate = None
        self._active_tasks: List[URLSessionDataTask] = []
        self._mock_handlers: Dict[str, Callable] = {}

        print(f"[URLSession] 创建会话 (base_url={base_url or 'none'})")

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    def set_default_header(self, key: str, value: str):
        """设置默认请求头"""
        self._default_headers[key] = value
        print(f"[URLSession] 设置默认请求头: {key} = {value}")

    def set_mock_handler(self, url_pattern: str, handler: Callable):
        """设置模拟响应处理器"""
        self._mock_handlers[url_pattern] = handler
        print(f"[URLSession] 设置模拟处理器: {url_pattern}")

    def data_task_with_request(self, request: URLRequest,
                                completion_handler: Optional[Callable] = None) -> URLSessionDataTask:
        """
        创建数据任务 - 模拟 dataTaskWithRequest:completionHandler:

        这是最常用的网络请求方法。
        """
        task = URLSessionDataTask(self, request, completion_handler)
        self._active_tasks.append(task)
        print(f"[URLSession] 创建数据任务: {request.method} {request.url}")
        return task

    def get(self, url: str, headers: Optional[Dict[str, str]] = None,
            completion_handler: Optional[Callable] = None) -> URLSessionDataTask:
        """
        GET 请求 - 模拟常用快捷方法
        """
        full_url = f"{self.base_url}{url}" if self.base_url else url
        request = URLRequest(full_url, HTTPMethod.GET)

        if headers:
            for k, v in headers.items():
                request.add_header(k, v)

        for k, v in self._default_headers.items():
            request.add_header(k, v)

        return self.data_task_with_request(request, completion_handler)

    def post(self, url: str, body: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None,
             completion_handler: Optional[Callable] = None) -> URLSessionDataTask:
        """
        POST 请求 - 模拟常用快捷方法
        """
        full_url = f"{self.base_url}{url}" if self.base_url else url
        request = URLRequest(full_url, HTTPMethod.POST)

        if body:
            request.set_body_json(body)

        if headers:
            for k, v in headers.items():
                request.add_header(k, v)

        for k, v in self._default_headers.items():
            request.add_header(k, v)

        return self.data_task_with_request(request, completion_handler)

    def _simulate_request(self, request: URLRequest):
        """
        模拟网络请求

        检查是否有匹配的 mock handler，否则返回默认响应。
        """
        # 检查 mock handlers
        for pattern, handler in self._mock_handlers.items():
            if pattern in request.url:
                try:
                    result = handler(request)
                    if isinstance(result, tuple) and len(result) == 3:
                        return result
                    elif isinstance(result, dict):
                        return None, result, None
                    else:
                        return None, result, None
                except Exception as e:
                    return None, None, URLResponseError(-1000, str(e))

        # 默认模拟响应
        return self._default_response(request)

    def _default_response(self, request: URLRequest):
        """返回默认模拟响应"""
        response = URLResponse(
            status_code=200,
            headers={
                "Content-Type": "application/json",
                "X-Response-Time": str(round(time.time() * 1000)),
            },
            url=request.url,
        )

        # 模拟不同 URL 的不同响应
        if "api/users" in request.url:
            data = {
                "users": [
                    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
                    {"id": 2, "name": "李四", "email": "lisi@example.com"},
                    {"id": 3, "name": "王五", "email": "wangwu@example.com"},
                ],
                "total": 3,
            }
        elif "api/post" in request.url or "api/posts" in request.url:
            data = {
                "posts": [
                    {"id": 1, "title": "iOS 开发入门", "body": "本文介绍 iOS 开发基础..."},
                    {"id": 2, "title": "SwiftUI 教程", "body": "SwiftUI 是苹果的新 UI 框架..."},
                ],
                "total": 2,
            }
        elif "api/weather" in request.url:
            data = {
                "location": "北京",
                "temperature": 25,
                "condition": "晴",
                "humidity": 45,
            }
        elif "api/status" in request.url:
            data = {"status": "ok", "version": "1.0.0"}
        else:
            data = {"message": "模拟响应", "url": request.url}

        return response, data, None

    def cancel_all_tasks(self):
        """取消所有活跃任务"""
        for task in self._active_tasks:
            task.cancel()
        self._active_tasks.clear()
        print("[URLSession] 取消所有任务")

    def __repr__(self):
        return f"<URLSession base_url={self.base_url} tasks={len(self._active_tasks)}>"


class NetworkManager:
    """
    NetworkManager - 网络管理器

    提供高层网络请求 API，封装 URLSession 的使用。
    类似 Alamofire 或 AFNetworking 的简化版。
    """

    def __init__(self, base_url: str = "", default_headers: Optional[Dict[str, str]] = None):
        self.session = URLSession(base_url)
        self._default_headers = default_headers or {}
        self._request_interceptor: Optional[Callable] = None
        self._response_interceptor: Optional[Callable] = None

        for k, v in self._default_headers.items():
            self.session.set_default_header(k, v)

        print(f"[NetworkManager] 创建网络管理器 (base_url={base_url})")

    def set_interceptor(self, request_handler: Optional[Callable] = None,
                        response_handler: Optional[Callable] = None):
        """设置请求/响应拦截器"""
        self._request_interceptor = request_handler
        self._response_interceptor = response_handler

    def get(self, url: str, params: Optional[Dict[str, str]] = None,
            headers: Optional[Dict[str, str]] = None,
            completion: Optional[Callable] = None) -> URLSessionDataTask:
        """
        GET 请求

        Args:
            url: 请求 URL
            params: 查询参数
            headers: 额外请求头
            completion: 完成回调 (data, response, error)
        """
        full_url = url
        if params:
            query = urlencode(params)
            separator = "&" if "?" in url else "?"
            full_url = f"{url}{separator}{query}"

        return self.session.get(full_url, headers, completion)

    def post(self, url: str, body: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None,
             completion: Optional[Callable] = None) -> URLSessionDataTask:
        """
        POST 请求

        Args:
            url: 请求 URL
            body: 请求体 (Dict)
            headers: 额外请求头
            completion: 完成回调 (data, response, error)
        """
        return self.session.post(url, body, headers, completion)

    def put(self, url: str, body: Optional[Dict[str, Any]] = None,
            completion: Optional[Callable] = None) -> URLSessionDataTask:
        """PUT 请求"""
        full_url = f"{self.session.base_url}{url}" if self.session.base_url else url
        request = URLRequest(full_url, HTTPMethod.PUT)
        if body:
            request.set_body_json(body)
        return self.session.data_task_with_request(request, completion)

    def delete(self, url: str, completion: Optional[Callable] = None) -> URLSessionDataTask:
        """DELETE 请求"""
        full_url = f"{self.session.base_url}{url}" if self.session.base_url else url
        request = URLRequest(full_url, HTTPMethod.DELETE)
        return self.session.data_task_with_request(request, completion)

    def add_mock_handler(self, url_pattern: str, handler: Callable):
        """添加模拟响应处理器"""
        self.session.set_mock_handler(url_pattern, handler)

    def __repr__(self):
        return f"<NetworkManager base_url={self.session.base_url}>"
