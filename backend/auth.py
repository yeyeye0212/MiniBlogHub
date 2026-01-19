from flask import Flask, request, jsonify, Blueprint
import sqlite3
import hashlib
from datetime import datetime

auth = Blueprint('auth', __name__)


# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect("minibloghub.db")
    conn.row_factory = sqlite3.Row
    return conn


# 加密密码函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 注册接口 - 修正响应格式匹配前端
@auth.route('/register', methods=['POST'])
def register():
    data = request.json

    if not data:
        return jsonify({
            "success": False,
            "message": "请提供JSON数据",
            "data": None
        }), 400

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    # 数据验证
    if not all([username, password, email]):
        return jsonify({
            "success": False,
            "message": "请填写所有字段",
            "data": None
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "密码长度至少六位！",
            "data": None
        }), 400

    if '@' not in email or '.' not in email:
        return jsonify({
            "success": False,
            "message": "邮箱格式不正确",
            "data": None
        }), 400

    # 密码加密
    hashed_password = hash_password(password)

    # 连接数据库
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "用户名已存在",
                "data": None
            }), 400

        # 检查邮箱是否已注册
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "邮箱已被注册",
                "data": None
            }), 400

        # 插入新用户到数据库
        cursor.execute('''
            INSERT INTO users (username, password, email) 
            VALUES (?, ?, ?)
        ''', (username, hashed_password, email))

        conn.commit()
        user_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "注册成功！",
            "data": {
                "id": user_id,
                "username": username,
                "email": email
            }
        }), 200

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "注册失败，请重试",
            "data": None
        }), 400
    finally:
        conn.close()


# 登录接口 - 修正响应格式匹配前端
@auth.route('/login', methods=['POST'])
def sign_in():
    data = request.json

    if not data:
        return jsonify({
            "success": False,
            "message": "请提供JSON数据",
            "data": None
        }), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "用户名和密码不能为空",
            "data": None
        }), 400

    # 密码加密
    hashed_password = hash_password(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 查询用户
        cursor.execute('''
            SELECT id, username, email, password, created_at 
            FROM users 
            WHERE username = ?
        ''', (username,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "用户名或密码错误",
                "data": None
            }), 401

        # 验证密码
        if user["password"] != hashed_password:
            return jsonify({
                "success": False,
                "message": "用户名或密码错误",
                "data": None
            }), 401

        # 登录成功
        return jsonify({
            "success": True,
            "message": "登录成功！",
            "data": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "created_at": user["created_at"]
            }
        }), 200

    finally:
        conn.close()


# 添加文章相关接口
@auth.route('/posts', methods=['GET'])
def get_posts():
    """获取文章列表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT p.*, u.username as author_username 
            FROM posts p 
            JOIN users u ON p.author_id = u.id 
            ORDER BY p.created_at DESC
        ''')
        posts = cursor.fetchall()

        posts_list = []
        for post in posts:
            posts_list.append(dict(post))

        return jsonify({
            "success": True,
            "message": "获取文章列表成功",
            "data": posts_list
        }), 200

    finally:
        conn.close()


@auth.route('/posts', methods=['POST'])
def create_post():
    """创建新文章"""
    data = request.json

    if not data:
        return jsonify({
            "success": False,
            "message": "请提供JSON数据",
            "data": None
        }), 400

    title = data.get('title')
    content = data.get('content')
    author_id = data.get('user_id')

    if not all([title, content, author_id]):
        return jsonify({
            "success": False,
            "message": "请填写完整信息",
            "data": None
        }), 400

    # 获取作者用户名
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT username FROM users WHERE id = ?', (author_id,))
        author = cursor.fetchone()

        if not author:
            return jsonify({
                "success": False,
                "message": "用户不存在",
                "data": None
            }), 400

        # 插入文章
        cursor.execute('''
            INSERT INTO posts (title, content, author_id, author_username) 
            VALUES (?, ?, ?, ?)
        ''', (title, content, author_id, author['username']))

        conn.commit()
        post_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "发布成功",
            "data": {
                "id": post_id,
                "title": title,
                "content": content,
                "author_id": author_id,
                "author_username": author['username']
            }
        }), 200

    finally:
        conn.close()