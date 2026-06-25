"""
主程序入口
启动WebSocket服务器
"""

import asyncio
import logging
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server import WebSocketServer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # 配置参数
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8765'))
    db_path = os.getenv('DB_PATH', 'social_chat.db')

    logger.info(f"启动社交聊天服务器...")
    logger.info(f"监听地址: {host}:{port}")
    logger.info(f"数据库路径: {db_path}")

    # 创建并启动服务器
    server = WebSocketServer(host=host, port=port, db_path=db_path)

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("服务器正在关闭...")
        await server.db.close()
        logger.info("服务器已关闭")


if __name__ == '__main__':
    asyncio.run(main())
