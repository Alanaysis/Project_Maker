"""
HTTP API 使用示例
演示如何使用REST API
"""

import requests
import json

BASE_URL = 'http://localhost:8765'


def register(username, email, password, nickname=''):
    """注册用户"""
    response = requests.post(f'{BASE_URL}/api/register', json={
        'username': username,
        'email': email,
        'password': password,
        'nickname': nickname
    })
    return response.json()


def login(username, password):
    """登录"""
    response = requests.post(f'{BASE_URL}/api/login', json={
        'username': username,
        'password': password
    })
    return response.json()


def search_users(token, query):
    """搜索用户"""
    response = requests.get(
        f'{BASE_URL}/api/users/search',
        params={'q': query},
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()


def main():
    """主函数"""
    print("=" * 50)
    print("社交聊天 API 使用示例")
    print("=" * 50)

    # 1. 注册用户
    print("\n1. 注册用户")
    result = register('testuser', 'test@example.com', 'password123', '测试用户')
    print(f"注册结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    if 'token' in result:
        token = result['token']
    else:
        # 如果注册失败（可能已存在），尝试登录
        print("\n尝试登录...")
        result = login('testuser', 'password123')
        print(f"登录结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        token = result.get('token')

    if not token:
        print("无法获取令牌")
        return

    # 2. 注册更多用户
    print("\n2. 注册更多用户")
    users = [
        ('alice', 'alice@example.com', 'password123', 'Alice'),
        ('bob', 'bob@example.com', 'password123', 'Bob'),
        ('charlie', 'charlie@example.com', 'password123', 'Charlie'),
    ]

    for username, email, password, nickname in users:
        result = register(username, email, password, nickname)
        print(f"注册 {username}: {'成功' if 'token' in result else result.get('error', '失败')}")

    # 3. 搜索用户
    print("\n3. 搜索用户")
    result = search_users(token, 'a')
    print(f"搜索结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    print("\n" + "=" * 50)
    print("API 示例完成")
    print("=" * 50)


if __name__ == '__main__':
    main()
