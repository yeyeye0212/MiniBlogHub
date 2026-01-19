# init_db.py - 初始化数据库表
import sqlite3


def init_database():
    # 连接到数据库文件（如果不存在会自动创建）
    conn = sqlite3.connect('minibloghub.db')
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("数据库初始化完成！")


if __name__ == '__main__':
    init_database()