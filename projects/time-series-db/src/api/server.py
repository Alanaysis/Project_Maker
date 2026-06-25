"""
HTTP API 服务器

提供 REST API 接口，支持数据写入和查询。
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from aiohttp import web
import asyncio

from ..db import TimeSeriesDB
from ..query.executor import QueryRequest, BatchQueryRequest

logger = logging.getLogger(__name__)


class APIHandler:
    """API 处理器"""

    def __init__(self, db: TimeSeriesDB):
        self.db = db
        self.start_time = time.time()

    async def handle_write(self, request: web.Request) -> web.Response:
        """
        处理写入请求

        POST /write
        Content-Type: application/json

        {
            "metric": "cpu_usage",
            "tags": {"host": "server1"},
            "points": [
                {"timestamp": 1625097600, "value": 45.2}
            ]
        }
        """
        try:
            data = await request.json()
            metric = data.get('metric')
            tags = data.get('tags', {})
            points = data.get('points', [])

            if not metric:
                return web.json_response(
                    {'error': 'metric is required'},
                    status=400
                )

            if not points:
                return web.json_response(
                    {'error': 'points is required'},
                    status=400
                )

            # 转换为批量写入格式
            write_points = []
            for point in points:
                write_points.append({
                    'metric': metric,
                    'tags': tags,
                    'timestamp': point['timestamp'],
                    'value': point['value']
                })

            # 写入
            written = self.db.write_batch(write_points)

            return web.json_response({
                'status': 'ok',
                'written': written
            })

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON'},
                status=400
            )
        except KeyError as e:
            return web.json_response(
                {'error': f'Missing field: {e}'},
                status=400
            )
        except Exception as e:
            logger.error(f"Write error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_query(self, request: web.Request) -> web.Response:
        """
        处理查询请求

        GET /query?metric=cpu_usage&start=1625097600&end=1625098600
        """
        try:
            metric = request.query.get('metric')
            start = request.query.get('start')
            end = request.query.get('end')
            tags_str = request.query.get('tags')
            aggregation = request.query.get('agg')
            downsample = request.query.get('downsample')
            fill = request.query.get('fill')
            limit = request.query.get('limit')
            order = request.query.get('order', 'asc')

            if not metric:
                return web.json_response(
                    {'error': 'metric is required'},
                    status=400
                )

            if not start or not end:
                return web.json_response(
                    {'error': 'start and end are required'},
                    status=400
                )

            # 解析标签
            tags = None
            if tags_str:
                try:
                    tags = json.loads(tags_str)
                except json.JSONDecodeError:
                    # 尝试解析 key=value 格式
                    tags = {}
                    for pair in tags_str.split(','):
                        k, v = pair.split('=')
                        tags[k.strip()] = v.strip()

            # 构建查询请求
            query_request = QueryRequest(
                metric=metric,
                start=int(start),
                end=int(end),
                tags=tags,
                aggregation=aggregation,
                downsample=downsample,
                fill=fill,
                limit=int(limit) if limit else None,
                order=order
            )

            # 执行查询
            response = self.db.query_with_request(query_request)

            # 转换响应格式
            points = [
                {'timestamp': ts, 'value': val}
                for ts, val in response.points
            ]

            return web.json_response({
                'metric': response.metric,
                'points': points,
                'count': response.count,
                'aggregation': response.aggregation,
                'downsample': response.downsample,
                'execution_time': response.execution_time
            })

        except ValueError as e:
            return web.json_response(
                {'error': str(e)},
                status=400
            )
        except Exception as e:
            logger.error(f"Query error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_batch_query(self, request: web.Request) -> web.Response:
        """
        处理批量查询请求

        POST /query/batch
        Content-Type: application/json

        {
            "queries": [
                {"metric": "cpu_usage", "start": 1625097600, "end": 1625098600}
            ]
        }
        """
        try:
            data = await request.json()
            queries = data.get('queries', [])

            if not queries:
                return web.json_response(
                    {'error': 'queries is required'},
                    status=400
                )

            # 构建批量查询请求
            query_requests = []
            for q in queries:
                query_requests.append(QueryRequest(
                    metric=q['metric'],
                    start=int(q['start']),
                    end=int(q['end']),
                    tags=q.get('tags'),
                    aggregation=q.get('aggregation'),
                    downsample=q.get('downsample'),
                    fill=q.get('fill'),
                    limit=int(q['limit']) if 'limit' in q else None,
                    order=q.get('order', 'asc')
                ))

            batch_request = BatchQueryRequest(queries=query_requests)

            # 执行批量查询
            batch_response = self.db.query_batch(batch_request)

            # 转换响应格式
            results = []
            for response in batch_response.results:
                points = [
                    {'timestamp': ts, 'value': val}
                    for ts, val in response.points
                ]
                results.append({
                    'metric': response.metric,
                    'points': points,
                    'count': response.count,
                    'aggregation': response.aggregation,
                    'downsample': response.downsample
                })

            return web.json_response({
                'results': results,
                'total_execution_time': batch_response.total_execution_time
            })

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON'},
                status=400
            )
        except Exception as e:
            logger.error(f"Batch query error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_latest(self, request: web.Request) -> web.Response:
        """
        处理最新值查询

        GET /latest?metric=cpu_usage
        """
        try:
            metric = request.query.get('metric')
            tags_str = request.query.get('tags')

            if not metric:
                return web.json_response(
                    {'error': 'metric is required'},
                    status=400
                )

            # 解析标签
            tags = None
            if tags_str:
                try:
                    tags = json.loads(tags_str)
                except json.JSONDecodeError:
                    tags = {}
                    for pair in tags_str.split(','):
                        k, v = pair.split('=')
                        tags[k.strip()] = v.strip()

            # 查询最新值
            result = self.db.latest(metric, tags)

            if result:
                return web.json_response({
                    'metric': metric,
                    'timestamp': result[0],
                    'value': result[1]
                })
            else:
                return web.json_response({
                    'metric': metric,
                    'timestamp': None,
                    'value': None
                })

        except Exception as e:
            logger.error(f"Latest query error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_metrics(self, request: web.Request) -> web.Response:
        """
        处理指标列表查询

        GET /metrics
        """
        try:
            metrics = self.db.metrics()
            return web.json_response({'metrics': metrics})
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_health(self, request: web.Request) -> web.Response:
        """
        处理健康检查

        GET /health
        """
        uptime = time.time() - self.start_time
        stats = self.db.get_stats()

        return web.json_response({
            'status': 'ok',
            'version': '1.0.0',
            'uptime': uptime,
            'stats': stats
        })

    async def handle_ttl_set(self, request: web.Request) -> web.Response:
        """
        设置 TTL

        POST /ttl
        Content-Type: application/json

        {
            "metric": "cpu_usage",
            "ttl": 86400
        }
        """
        try:
            data = await request.json()
            metric = data.get('metric')
            ttl = data.get('ttl')

            if not metric:
                return web.json_response(
                    {'error': 'metric is required'},
                    status=400
                )

            if ttl is None:
                return web.json_response(
                    {'error': 'ttl is required'},
                    status=400
                )

            self.db.set_ttl(metric, ttl)

            return web.json_response({
                'status': 'ok',
                'metric': metric,
                'ttl': ttl
            })

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON'},
                status=400
            )
        except Exception as e:
            logger.error(f"TTL set error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_ttl_get(self, request: web.Request) -> web.Response:
        """
        获取 TTL 配置

        GET /ttl
        """
        try:
            metric = request.query.get('metric')

            if metric:
                ttl = self.db.get_ttl(metric)
                return web.json_response({
                    'metric': metric,
                    'ttl': ttl
                })
            else:
                configs = self.db.list_ttl_configs()
                return web.json_response({'configs': configs})

        except Exception as e:
            logger.error(f"TTL get error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def handle_cleanup(self, request: web.Request) -> web.Response:
        """
        手动触发清理

        POST /cleanup
        """
        try:
            metric = request.query.get('metric')
            cleaned = self.db.cleanup(metric)

            return web.json_response({
                'status': 'ok',
                'cleaned': cleaned
            })

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )


def create_app(db: TimeSeriesDB) -> web.Application:
    """
    创建 HTTP 应用

    Args:
        db: TimeSeriesDB 实例

    Returns:
        web.Application: aiohttp 应用
    """
    app = web.Application()
    handler = APIHandler(db)

    # 注册路由
    app.router.add_post('/write', handler.handle_write)
    app.router.add_get('/query', handler.handle_query)
    app.router.add_post('/query/batch', handler.handle_batch_query)
    app.router.add_get('/latest', handler.handle_latest)
    app.router.add_get('/metrics', handler.handle_metrics)
    app.router.add_get('/health', handler.handle_health)
    app.router.add_post('/ttl', handler.handle_ttl_set)
    app.router.add_get('/ttl', handler.handle_ttl_get)
    app.router.add_post('/cleanup', handler.handle_cleanup)

    # CORS 中间件
    @web.middleware
    async def cors_middleware(request, handler):
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    app.middlewares.append(cors_middleware)

    return app


def run_server(
    db: TimeSeriesDB,
    host: str = '0.0.0.0',
    port: int = 8080
) -> None:
    """
    运行 HTTP 服务器

    Args:
        db: TimeSeriesDB 实例
        host: 监听地址
        port: 监听端口
    """
    app = create_app(db)
    logger.info(f"Starting server on {host}:{port}")
    web.run_app(app, host=host, port=port)
