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

# 通用生成验证码函数（抽离出来，避免重复定义）
def generate_verification_code():
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(4))
    return code

# 路由
@app.route('/')
def index():
    return redirect(url_for('log_in'))

# 修复登录路由：支持用户名/邮箱登录
@app.route('/log_in', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        # 获取用户输入（用户名/邮箱）
        login_input = request.form['username'].strip()
        password = request.form['password'].strip()

        # 先按用户名查，再按邮箱查（支持两种登录方式）
        user = User.query.filter_by(username=login_input).first()
        if not user:
            user = User.query.filter_by(email=login_input).first()

        # 验证用户和密码
        if user and user.check_password(password):
            flash('登录成功！', 'success')
            session['username'] = user.username  # 存用户名，不是输入的邮箱
            return redirect(url_for('page'))
        else:
            flash('用户名/邮箱或密码错误！', 'error')

    return render_template('log_in.html')

# 保留注册路由
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'GET':
        verification_code = generate_verification_code()
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
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 验证密码是否一致
        if password != confirm_password:
            print("❌ 错误：两次密码不一致")  # 新增打印
            flash("两次输入密码不一致！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            print("❌ 错误：用户名已存在")  # 新增打印
            flash("用户名已存在！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查邮箱是否已注册
        if User.query.filter_by(email=email).first():
            print("❌ 错误：邮箱已存在")  # 新增打印
            flash("邮箱已被注册！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查验证码
        if not user_verification_code:
            print("❌ 错误：未输入验证码")  # 新增打印
            flash("请输入验证码！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        if not real_code or user_verification_code.upper() != real_code.upper():
            print(f"❌ 错误：验证码错误（用户输入{user_verification_code}，正确{real_code}）")  # 新增打印
            flash(f"验证码错误！正确验证码是：{real_code}", "error")
            new_code = generate_verification_code()
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
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

    return render_template('sign_in.html')


# 保留page/page2/page3路由（无需修改）
@app.route('/page')
def page():
    #按发布时间倒序
    posts = Post.query.filter_by(category='技术求助').order_by(Post.created_at.desc()).all()
    return render_template('page.html', posts=posts, username=session.get('username'))

@app.route('/page2')
def page2():
    if 'username' not in session:
        return redirect(url_for('log_in'))
    posts=Post.query.filter_by(category='日常休闲').order_by(Post.created_at.desc()).all()
    return render_template('page2.html',posts=posts,username=session.get('username'))

@app.route('/page3')
def page3():
    if 'username' not in session:
        return redirect(url_for('log_in'))
    posts=Post.query.filter_by(category='组队寻人').order_by(Post.created_at.desc()).all()
    return render_template('page3.html',posts=posts,username=session.get('username'))



#个人博客的后端（修复：加用户不存在兜底）
@app.route('/my_blog1')
def my_blog1():
    # 1. 先校验用户是否登录（没登录跳登录页）
    if 'username' not in session:
        return redirect(url_for('log_in'))

    # 2. 获取当前登录用户的信息
    username = session['username']
    user = User.query.filter_by(username=username).first()

    # 新增：兜底处理——用户不存在则清空session并跳转
    if not user:
        flash('用户信息不存在，请重新登录！', 'error')
        session.clear()
        return redirect(url_for('log_in'))

    # 3. 只查：当前用户 + 技术求助分类 + 按时间倒序
    posts = Post.query.filter_by(
        category='技术求助',
        user_id=user.id  # 核心：只显示当前用户的帖子
    ).order_by(Post.created_at.desc()).all()

    return render_template('my_blog1.html', posts=posts, username=username)


@app.route('/my_blog2')
def my_blog2():
    # 1. 校验登录
    if 'username' not in session:
        return redirect(url_for('log_in'))

    # 2. 获取当前用户
    username = session['username']
    user = User.query.filter_by(username=username).first()

    # 新增：兜底处理
    if not user:
        flash('用户信息不存在，请重新登录！', 'error')
        session.clear()
        return redirect(url_for('log_in'))

    # 3. 只查：当前用户 + 日常休闲分类 + 按时间倒序
    posts = Post.query.filter_by(
        category='日常休闲',
        user_id=user.id
    ).order_by(Post.created_at.desc()).all()

    return render_template('my_blog2.html', posts=posts, username=username)


@app.route('/my_blog3')
def my_blog3():
    # 1. 校验登录
    if 'username' not in session:
        return redirect(url_for('log_in'))

    # 2. 获取当前用户
    username = session['username']
    user = User.query.filter_by(username=username).first()

    # 新增：兜底处理
    if not user:
        flash('用户信息不存在，请重新登录！', 'error')
        session.clear()
        return redirect(url_for('log_in'))

    # 3. 只查：当前用户 + 组队寻人分类 + 按时间倒序
    posts = Post.query.filter_by(
        category='组队寻人',
        user_id=user.id
    ).order_by(Post.created_at.desc()).all()

    return render_template('my_blog3.html', posts=posts, username=username)




# 修复忘记密码路由：只做跳转，不重复生成验证码
@app.route('/forget')
def forget():
    return redirect(url_for('reset_password'))  # 跳转到reset_password的GET路由

# 修复重置密码路由（删除重复定义，保留完整逻辑）
@app.route('/reset_password',methods=['GET','POST'])
def reset_password():
    if request.method == 'GET':
        # GET请求：展示重置页面，生成验证码
        verification_code = generate_verification_code()
        session['verification_code'] = verification_code
        return render_template('forget.html', verification_code=verification_code)

    # POST请求：处理重置密码
    if request.method == 'POST':
        # 1. 获取表单数据（去空格，转小写避免大小写问题）
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        user_verification_code = request.form.get('verification_code', '').strip().upper()
        real_code = session.get('verification_code', '').upper()

        # 2. 验证必填项
        if not all([username, email, new_password, confirm_password, user_verification_code]):
            flash('请填写所有必填字段！', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        # 3. 验证密码一致性
        if new_password != confirm_password:
            flash('两次输入的新密码不一致！', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        # 4. 验证验证码
        if not real_code or user_verification_code != real_code:
            flash(f'验证码错误！正确验证码是：{real_code}', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        # 5. 验证用户信息（邮箱转小写，避免大小写问题）
        user = User.query.filter(
            User.username == username,
            User.email.ilike(email)  # ilike：大小写不敏感匹配
        ).first()

        if not user:
            flash('用户名或邮箱不匹配！', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        # 6. 重置密码
        try:
            user.set_password(new_password)
            db.session.commit()
            # 清除验证码session，避免复用
            session.pop('verification_code', None)
            flash('密码重置成功！请使用新密码登录', 'success')
            return redirect(url_for('log_in'))
        except Exception as e:
            db.session.rollback()
            flash(f'密码重置失败：{str(e)}', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

    # 兜底：GET请求展示页面
    verification_code = generate_verification_code()
    session['verification_code'] = verification_code
    return render_template('forget.html', verification_code=new_code)

# 保留其他路由（post/submit_post/my_information/logout/post_detail/update_profile）
@app.route('/post')
def post():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))
    username = session.get('username')
    return render_template('post.html', username=username)

@app.route('/submit_post', methods=['POST'])
def submit_post():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    # 从session获取用户名，而不是表单
    username = session['username']

    # 使用get方法避免KeyError
    title = request.form.get('title', '')
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
            username=username,
            group='极创组',
            email=user.email,
            reg_time=user.created_at.strftime('%Y-%m-%d'),
            #需要在user模型添加signature字段
            signature=getattr(user,'signature','未设置个性签名'))
    else:
       flash('用户信息获取失败！', 'error')
       return redirect(url_for('page'))

@app.route('/logout')
def logout():
    # 1. 清空所有session（关键：移除登录态）
    session.clear()
    # 2. 清除所有残留的flash消息（避免串提示）
    session.pop('_flashes', None)
    # 3. 添加“退出成功”的flash提示（可选）
    flash('已成功退出登录！', 'success')
    # 4. 跳回登录页
    return redirect(url_for('log_in'))

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('show.html', post=post)

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


@app.route('/delete_post', methods=['POST'])
def delete_post():
    # 1. 简单校验（根据你的实际登录逻辑改，比如session里的user_id）
    if 'username' not in session:
        return {'success': False, 'msg': '请先登录'}

    # 2. 获取帖子ID
    post_id = request.form.get('post_id')

    # 3. 删帖（直接删，最简版，你可根据模型调整）
    try:
        post = Post.query.get(post_id)
        db.session.delete(post)
        db.session.commit()
        return {'success': True}
    except:
        return {'success': False, 'msg': '帖子不存在或无权删除'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("数据库表已创建")
    app.run(debug=True, port=5000)

