"""
网络请求模拟 - Network Request Simulation

模拟 Android 中的网络请求流程。
包括 HTTP 请求、响应处理、错误处理等。

Simulates network request flow in Android.
Includes HTTP requests, response handling, error handling, etc.

Android 中常用的网络库：
- OkHttp (推荐)
- Retrofit (基于 OkHttp)
- HttpURLConnection (原生)

Common networking libraries in Android:
- OkHttp (recommended)
- Retrofit (built on OkHttp)
- HttpURLConnection (native)
"""

import time
import logging
import random
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class HttpMethod(Enum):
    """HTTP 方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class HttpStatus(Enum):
    """HTTP 状态码"""
    OK = (200, "OK")
    CREATED = (201, "Created")
    NO_CONTENT = (204, "No Content")
    BAD_REQUEST = (400, "Bad Request")
    UNAUTHORIZED = (401, "Unauthorized")
    FORBIDDEN = (403, "Forbidden")
    NOT_FOUND = (404, "Not Found")
    INTERNAL_ERROR = (500, "Internal Server Error")
    BAD_GATEWAY = (502, "Bad Gateway")
    SERVICE_UNAVAILABLE = (503, "Service Unavailable")

    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason

    @property
    def is_success(self) -> bool:
        return 200 <= self.code < 300

    @property
    def is_client_error(self) -> bool:
        return 400 <= self.code < 500

    @property
    def is_server_error(self) -> bool:
        return 500 <= self.code < 600


@dataclass
class NetworkRequest:
    """网络请求"""
    url: str
    method: HttpMethod = HttpMethod.GET
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    query_params: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    request_id: str = field(default_factory=lambda: f"req_{int(time.time() * 1000) % 100000:05d}")

    def add_header(self, key: str, value: str) -> "NetworkRequest":
        self.headers[key] = value
        return self

    def add_query_param(self, key: str, value: str) -> "NetworkRequest":
        self.query_params[key] = value
        return self

    def __str__(self) -> str:
        return (f"Request({self.method.value} {self.url}, "
                f"headers={len(self.headers)}, body={'yes' if self.body else 'no'})")


@dataclass
class NetworkResponse:
    """网络响应"""
    status: HttpStatus
    body: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    request_id: str = ""
    elapsed_time: float = 0.0
    timestamp: float = field(default_factory=time.time)

    @property
    def is_success(self) -> bool:
        return self.status.is_success

    @property
    def is_error(self) -> bool:
        return not self.is_success

    def __str__(self) -> str:
        return (f"Response({self.status.code} {self.status.reason}, "
                f"time={self.elapsed_time:.3f}s, body_len={len(self.body or '')})")


class NetworkError(Exception):
    """网络错误"""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 request: Optional[NetworkRequest] = None):
        super().__init__(message)
        self.status_code = status_code
        self.request = request


class NetworkInterceptor:
    """
    网络拦截器 - Network Interceptor

    在请求/响应过程中执行拦截逻辑。
    用于日志记录、认证、缓存等。

    Intercepts requests/responses for logging, auth, caching, etc.
    """

    def __init__(self, name: str):
        self.name = name

    def intercept(self, request: NetworkRequest, chain: "InterceptorChain") -> NetworkResponse:
        """拦截请求"""
        start_time = time.time()
        response = chain.proceed(request)
        response.elapsed_time = time.time() - start_time
        return response


class InterceptorChain:
    """拦截器链"""

    def __init__(self, interceptors: List[NetworkInterceptor], request: NetworkRequest):
        self._interceptors = interceptors
        self._request = request
        self._index = 0

    def proceed(self, request: Optional[NetworkRequest] = None) -> NetworkResponse:
        if self._index >= len(self._interceptors):
            # 所有拦截器处理完毕，执行实际请求
            return NetworkRequestExecutor().execute(request or self._request)

        interceptor = self._interceptors[self._index]
        self._index += 1
        return interceptor.intercept(request or self._request, self)


class NetworkRequestExecutor:
    """
    网络请求执行器 - 模拟 HTTP 请求执行

    模拟网络请求的完整流程。
    """

    def __init__(self):
        self._request_log: List[str] = []
        self._response_log: List[str] = []
        self._request_count = 0
        self._error_count = 0

    def execute(self, request: NetworkRequest) -> NetworkResponse:
        """执行网络请求"""
        self._request_count += 1
        start_time = time.time()

        # 模拟网络延迟 (0.01 ~ 0.5 秒)
        delay = random.uniform(0.01, 0.5)
        time.sleep(delay)

        # 模拟响应
        response = self._simulate_response(request, delay)
        response.elapsed_time = time.time() - start_time
        response.request_id = request.request_id

        self._request_log.append(f"{request.method.value} {request.url} -> {response.status.code}")
        self._response_log.append(str(response))

        logger.debug(f"Executed {request.method.value} {request.url}: "
                      f"{response.status.code} ({response.elapsed_time:.3f}s)")

        return response

    def _simulate_response(self, request: NetworkRequest, delay: float) -> NetworkResponse:
        """模拟响应"""
        # 根据 URL 模拟不同的响应
        if "/error" in request.url:
            return NetworkResponse(
                status=HttpStatus.INTERNAL_ERROR,
                body='{"error": "Internal Server Error"}',
                elapsed_time=delay,
            )
        elif "/notfound" in request.url:
            return NetworkResponse(
                status=HttpStatus.NOT_FOUND,
                body='{"error": "Not Found"}',
                elapsed_time=delay,
            )
        elif "/unauthorized" in request.url:
            return NetworkResponse(
                status=HttpStatus.UNAUTHORIZED,
                body='{"error": "Unauthorized"}',
                elapsed_time=delay,
            )

        # 成功响应
        if request.method == HttpMethod.GET:
            body = f'{{"data": "response from {request.url}", "delay": {delay:.3f}}}'
        elif request.method == HttpMethod.POST:
            body = f'{{"status": "created", "url": "{request.url}", "delay": {delay:.3f}}}'
        elif request.method == HttpMethod.DELETE:
            body = f'{{"status": "deleted", "url": "{request.url}"}}'
        else:
            body = f'{{"status": "ok", "url": "{request.url}"}}'

        return NetworkResponse(
            status=HttpStatus.OK,
            body=body,
            headers={"Content-Type": "application/json", "X-Response-Time": f"{delay:.3f}s"},
            elapsed_time=delay,
        )

    @property
    def request_log(self) -> List[str]:
        return list(self._request_log)

    @property
    def response_log(self) -> List[str]:
        return list(self._response_log)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "success_rate": (self._request_count - self._error_count) / max(self._request_count, 1),
        }


class NetworkClient:
    """
    网络客户端 - Network Client

    模拟 Android 中的网络客户端（类似 OkHttp/Retrofit）。

    Simulates a network client in Android (similar to OkHttp/Retrofit).
    """

    def __init__(self, base_url: str = "https://api.example.com"):
        self.base_url = base_url
        self._default_headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._interceptors: List[NetworkInterceptor] = []
        self._executor = NetworkRequestExecutor()

    def get(self, path: str, query_params: Optional[Dict[str, str]] = None) -> NetworkResponse:
        """GET 请求"""
        request = NetworkRequest(
            url=f"{self.base_url}{path}",
            method=HttpMethod.GET,
            headers=dict(self._default_headers),
            query_params=query_params or {},
        )
        return self._execute(request)

    def post(self, path: str, body: Optional[str] = None) -> NetworkResponse:
        """POST 请求"""
        request = NetworkRequest(
            url=f"{self.base_url}{path}",
            method=HttpMethod.POST,
            headers=dict(self._default_headers),
            body=body,
        )
        return self._execute(request)

    def put(self, path: str, body: Optional[str] = None) -> NetworkResponse:
        """PUT 请求"""
        request = NetworkRequest(
            url=f"{self.base_url}{path}",
            method=HttpMethod.PUT,
            headers=dict(self._default_headers),
            body=body,
        )
        return self._execute(request)

    def delete(self, path: str) -> NetworkResponse:
        """DELETE 请求"""
        request = NetworkRequest(
            url=f"{self.base_url}{path}",
            method=HttpMethod.DELETE,
            headers=dict(self._default_headers),
        )
        return self._execute(request)

    def add_interceptor(self, interceptor: NetworkInterceptor) -> None:
        """添加拦截器"""
        self._interceptors.append(interceptor)

    def _execute(self, request: NetworkRequest) -> NetworkResponse:
        """执行请求"""
        if self._interceptors:
            chain = InterceptorChain(self._interceptors, request)
            return chain.proceed(request)
        return self._executor.execute(request)

    @property
    def request_log(self) -> List[str]:
        return self._executor.request_log

    @property
    def response_log(self) -> List[str]:
        return self._executor.response_log

    def get_stats(self) -> Dict[str, Any]:
        return self._executor.get_stats()

    def clear_log(self) -> None:
        self._executor._request_log.clear()
        self._executor._response_log.clear()
