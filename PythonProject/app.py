from flask import Flask, render_template, request, redirect, url_for, flash
from models import User, Post
from extensions import db
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)
app.config.from_object('config.Config')

# 初始化数据库
db.init_app(app)

# 路由
@app.route('/')
def index():
    return redirect(url_for('log_in'))

@app.route('/log_in', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误！', 'error')

    return render_template('log_in.html')

@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        confirm_password = request.form['confirm_password']

        # 验证密码是否一致
        if password != confirm_password:
            flash("两次输入密码不一致！", "error")
            return render_template('sign_in.html')

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash("用户名已存在！", "error")
            return render_template('sign_in.html')

        # 检查邮箱是否已注册
        if User.query.filter_by(email=email).first():
            flash("邮箱已被注册！", "error")
            return render_template('sign_in.html')

        # 创建新用户
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash("注册成功，请登录！", "success")
            return redirect(url_for('log_in'))
        except Exception as e:
            db.session.rollback()
            flash("注册失败，请重试！", "error")

    return render_template('sign_in.html')

@app.route('/dashboard')
def dashboard():
    return "欢迎来到仪表盘！"

@app.route('/create_tables')
def create_tables():
    db.create_all()
    return "数据库表已创建！"

if __name__ == '__main__':
    # 确保在应用上下文中创建表
    with app.app_context():
        db.create_all()
        print("数据库表已创建")
    app.run(debug=True, port=5000)