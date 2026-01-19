# test_api.py - 改进版本
import requests
import json


def test_api():
    base_url = "http://127.0.0.1:5000"

    # 测试注册
    print("=== 测试注册接口 ===")
    register_data = {
        "username": "testuser",
        "password": "123456",
        "password2": "123456",
        "email": "test@example.com"
    }

    try:
        response = requests.post(
            f"{base_url}/auth/register",
            json=register_data,
            timeout=5
        )

        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"原始响应内容: {response.text[:200]}...")  # 只显示前200个字符

        if response.status_code == 200:
            try:
                json_data = response.json()
                print("JSON解析成功:", json_data)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
        else:
            print(f"请求失败，状态码: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")

    print("\n=== 测试登录接口 ===")
    # 测试登录
    login_data = {
        "username": "testuser",
        "password": "123456"
    }

    try:
        response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            timeout=5
        )

        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")

        if response.status_code == 200:
            try:
                json_data = response.json()
                print("JSON解析成功:", json_data)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")

    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")


if __name__ == "__main__":
    test_api()