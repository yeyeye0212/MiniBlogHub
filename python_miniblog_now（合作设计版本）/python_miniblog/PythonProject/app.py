from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import User, Post
from extensions import db
import random  # 生成随机数
import string  # 提供字母/数字字符集
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
            session['username'] = username
            return redirect(url_for('page'))
        else:
            flash('用户名或密码错误！', 'error')

    return render_template('log_in.html')


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    def generate():
        chars = string.ascii_letters + string.digits
        code = ''.join(random.choice(chars) for _ in range(4))
        return code

    if request.method == 'GET':
        verification_code = generate()
        session['verification_code'] = verification_code
        return render_template('sign_in.html', verification_code=verification_code)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        confirm_password = request.form['confirm_password']
        user_verification_code = request.form['verification_code']
        real_code = session.get('verification_code')

        # ====== 新增：打印所有表单数据，方便排查 ======
        print("===== 表单数据 =====")
        print(f"用户名：{username}，邮箱：{email}")
        print(f"用户输入验证码：{user_verification_code}，后端正确验证码：{real_code}")
        print(f"密码是否一致：{password == confirm_password}")

        # 检查参数是否为空
        if not username or not password or not email or not confirm_password:
            print("❌ 错误：参数不全")  # 新增打印
            flash("参数不全！", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 验证密码是否一致
        if password != confirm_password:
            print("❌ 错误：两次密码不一致")  # 新增打印
            flash("两次输入密码不一致！", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            print("❌ 错误：用户名已存在")  # 新增打印
            flash("用户名已存在！", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查邮箱是否已注册
        if User.query.filter_by(email=email).first():
            print("❌ 错误：邮箱已存在")  # 新增打印
            flash("邮箱已被注册！", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查验证码
        if not user_verification_code:
            print("❌ 错误：未输入验证码")  # 新增打印
            flash("请输入验证码！", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        if not real_code or user_verification_code.upper() != real_code.upper():
            print(f"❌ 错误：验证码错误（用户输入{user_verification_code}，正确{real_code}）")  # 新增打印
            flash(f"验证码错误！正确验证码是：{real_code}", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 创建新用户
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            print("✅ 注册成功，准备跳转登录页")  # 新增打印
            flash("注册成功，请登录！", "success")
            return redirect(url_for('log_in'))
        except Exception as e:
            print(f"❌ 错误：注册失败 {str(e)}")  # 新增打印
            db.session.rollback()
            flash(f"注册失败：{str(e)}", "error")
            new_code = generate()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

    return render_template('sign_in.html')

# 修改现有的page路由
@app.route('/page')
def page():
    posts = Post.query.filter_by(category='技术求助').all()  # 默认显示技术求助
    return render_template('page.html', posts=posts, username=session.get('username'))
@app.route('/page2')
def page2():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    posts=Post.query.filter_by(category='日常休闲').all()
    return render_template('page2.html',posts=posts,username=session.get('username'))
@app.route('/page3')
def page3():
    if 'username' not in session:
        return redirect(url_for('log_in'))
    posts=Post.query.filter_by(category='组队请求').all()
    return render_template('page3.html',posts=posts,username=session.get('username'))

# @app.route('/create_tables')
# def create_tables():
#     with app.app_context():  # 修复：加应用上下文，避免创建表失败
#         db.create_all()
#     return "数据库表已创建！"
#

@app.route('/forget')
def forget():
    # 生成验证码
    def generate():
        chars = string.ascii_letters + string.digits
        code = ''.join(random.choice(chars) for _ in range(4))
        return code

    verification_code = generate()
    session['verification_code'] = verification_code
    return render_template('forget.html', verification_code=verification_code)

#密码重置forget.html
@app.route('/reset_password',methods=['GET','POST'])
def reset_password():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        new_password=request.form['password']
        # 验证用户信息
        user = User.query.filter_by(username=username, email=email).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('密码重置成功！', 'success')
            return redirect(url_for('log_in'))
        else:
            flash('用户名或邮箱不匹配！', 'error')

        # 生成验证码（复用注册页逻辑）
    def generate():
        chars = string.ascii_letters + string.digits
        code = ''.join(random.choice(chars) for _ in range(4))
        return code

    verification_code = generate()
    session['verification_code'] = verification_code
    return render_template('forget.html', verification_code=verification_code)
#发帖页面路由
@app.route('/post')
def post():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))
    return render_template('post.html')
#post.html帖子提交
@app.route('/submit_post', methods=['POST'])
def submit_post():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    # 从session获取用户名，而不是表单
    username = session['username']

    # 使用get方法避免KeyError
    title = request.form.get('title', '')
    intro = request.form.get('intro', '')
    content = request.form.get('content', '')
    category = request.form.get('category', '技术求助')

    # 验证必填字段
    if not title or not content:
        flash('标题和内容不能为空！', 'error')
        return redirect(url_for('post'))

    user = User.query.filter_by(username=username).first()
    if user:
        new_post = Post(
            title=title,
            content=content,
            user_id=user.id,
            category=category
        )
        db.session.add(new_post)
        db.session.commit()
        flash('帖子发布成功！', 'success')
        return redirect(url_for('page'))
    else:
        flash('用户不存在！', 'error')
        return redirect(url_for('log_in'))
#myimformation.html
@app.route('/my_information')
def my_information():
    if 'username' not in session:
        flash('请先登录！','error')
        return redirect(url_for('log_in'))
    username=session['username']
    user=User.query.filter_by(username=username).first()

    if user:
        return render_template(
            'my_information.html',
            email=user.email,
            reg_time=user.created_at.strftime('%Y-%m-%d'),
            #需要在user模型添加signature字段
            signature=getattr(user,'signature','未设置个性签名'))
    else:
       flash('用户信息获取失败！', 'error')
       return redirect(url_for('page'))

#登出功能
@app.route('/logout')
def logout():
    session.clear()
    flash('已成功退出登录！', 'success')
    return redirect(url_for('log_in'))
#帖子详情页面
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)

#个人信息更新
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if user:
        new_signature = request.form.get('signature')
        if new_signature:
            user.signature = new_signature
            db.session.commit()
            flash('个人信息更新成功！', 'success')

    return redirect(url_for('my_information'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("数据库表已创建")
    app.run(debug=True, port=5000)