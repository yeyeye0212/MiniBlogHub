# db_utils.py - 数据库工具函数
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect('minibloghub.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def create_user(username, password, email):
    """创建新用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, email) 
            VALUES (?, ?, ?)
        ''', (username, password, email))
        conn.commit()
        return cursor.lastrowid

def get_user_by_username(username):
    """根据用户名获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()

def get_user_by_email(email):
    """根据邮箱获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()