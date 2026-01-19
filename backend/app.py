from flask import Flask,jsonify
from auth import auth
from flask_cors import CORS

app = Flask(__name__)
CORS(app)   #启用CORS，允许前端跨域访问

app.register_blueprint(auth,url_prefix='/api')


# 初始化数据库
def init_database():
    import sqlite3
    conn = sqlite3.connect('minibloghub.db')
    cursor = conn.cursor()

    # 创建表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 创建文章表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            author_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return jsonify({"message": "MiniBlogHub API 服务运行正常"})

if __name__ == '__main__':
    init_database()
    print("数据库已经初始化")
    print("服务器启动：http://127.0.0.1:5000/")
    app.run(debug=True)





