from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash

# 初始化Flask应用
app = Flask(__name__)

# 配置跨域（解决前端调用后端接口的跨域问题）
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 配置SQLite数据库路径（指向database文件夹）
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../database/minibloghub.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义用户表模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # 存储加密后的密码

# 定义文章表模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

# 初始化数据库
with app.app_context():
    db.create_all()

# 测试接口
@app.route('/')
def index():
    return "MiniBlogHub后端已启动！数据库连接成功✅"

# 1. 注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 校验参数
    if not username or not email or not password:
        return jsonify({'success': False, 'message': '参数不全'})

    # 检查用户名/邮箱是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'})
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '邮箱已存在'})

    # 加密密码并创建用户
    hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, email=email, password=hashed_pwd)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': '注册成功'})

# 2. 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 校验参数
    if not username or not password:
        return jsonify({'success': False, 'message': '参数不全'})

    # 查找用户
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'success': False, 'message': '用户名或密码错误'})

    return jsonify({
        'success': True,
        'message': '登录成功',
        'data': {'id': user.id, 'username': user.username}
    })

# 3. 获取文章列表接口
@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = Post.query.join(User).all()
    post_list = []
    for post in posts:
        post_list.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'user_id': post.user_id,
            'author_username': post.author.username
        })
    return jsonify({'success': True, 'data': post_list})

# 4. 发布文章接口
@app.route('/api/posts', methods=['POST'])
def add_post():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    user_id = data.get('user_id')

    # 校验参数
    if not title or not content or not user_id:
        return jsonify({'success': False, 'message': '参数不全'})

    # 检查用户是否存在
    if not User.query.get(user_id):
        return jsonify({'success': False, 'message': '用户不存在'})

    # 创建文章
    new_post = Post(title=title, content=content, user_id=user_id)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'success': True, 'message': '发布成功'})

# 启动应用
if __name__ == '__main__':
    app.run(debug=True)