from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, Post, Comment, Like, Collect
from extensions import db,login_manager  
import random  # 生成随机数
import string  # 提供字母/数字字符集
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user 
from extensions import csrf
from flask_wtf.csrf import generate_csrf

# 创建Flask应用
app = Flask(__name__)
app.config.from_object('config.Config')

# ====== 头像上传配置 ======
UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化数据库
db.init_app(app)
csrf.init_app(app)
# 初始化 LoginManager
login_manager.init_app(app)
login_manager.login_view = 'log_in'          # 未登录时跳转到登录页
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 通用生成验证码函数
def generate_verification_code():
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(4))
    return code

# 路由
@app.route('/')
def index():
    return redirect(url_for('log_in'))


# 登录路由
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
            login_user(user)     
            flash('登录成功！', 'success')
            session['username'] = user.username
            return redirect(url_for('page'))
        else:
            flash('用户名/邮箱或密码错误！', 'error')

    return render_template('log_in.html')

# 【唯一登出路由】使用 logout_user 正确清除 Flask-Login 会话
@app.route('/logout')
def logout():
    logout_user()
    session.clear()          # 额外清除 session 中的数据
    flash('您已退出登录', 'info')
    return redirect(url_for('log_in'))
# 注册路由
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

        # 检查参数是否为空
        if not username or not password or not email or not confirm_password:
            flash("参数不全！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)
        # 验证密码是否一致
        if password != confirm_password:
            flash("两次输入密码不一致！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash("用户名已存在！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查邮箱是否已注册
        if User.query.filter_by(email=email).first():
            flash("邮箱已被注册！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        # 检查验证码
        if not user_verification_code:
            flash("请输入验证码！", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

        if not real_code or user_verification_code.upper() != real_code.upper():
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

            flash("注册成功，请登录！", "success")
            return redirect(url_for('log_in'))
        except Exception as e:
            db.session.rollback()
            flash(f"注册失败：{str(e)}", "error")
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('sign_in.html', verification_code=new_code)

    return render_template('sign_in.html')


# page路由
@app.route('/page')
def page():
    posts = Post.query.filter_by(category='技术求助').order_by(Post.created_at.desc()).all()

    # 为每个帖子添加作者头像信息
    posts_with_avatars = []
    for post in posts:
        author = User.query.get(post.user_id)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'intro': post.intro,
            'content': post.content,
            'created_at': post.created_at,
            'author': post.author,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        posts_with_avatars.append(post_dict)

    # 获取当前登录用户信息
    signature = '未设置个性签名'
    avatar = '/static/image/look.jpg'
    group = '极创组'

    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            if user.avatar:
                avatar = user.avatar
            if user.group:
                group = user.group
            if user.signature:
                signature = user.signature

    return render_template('page.html',
                           posts=posts_with_avatars,
                           username=session.get('username'),
                           avatar=avatar,
                           group=group,
                           signature=signature)


@app.route('/page2')
def page2():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    posts = Post.query.filter_by(category='日常休闲').order_by(Post.created_at.desc()).all()

    # 为每个帖子添加作者头像信息
    posts_with_avatars = []
    for post in posts:
        author = User.query.get(post.user_id)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'intro': post.intro,
            'content': post.content,
            'created_at': post.created_at,
            'author': post.author,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        posts_with_avatars.append(post_dict)

    # 获取当前登录用户信息
    signature = '未设置个性签名'
    avatar = '/static/image/look.jpg'
    group = '极创组'

    user = User.query.filter_by(username=session['username']).first()
    if user:
        if user.avatar:
            avatar = user.avatar
        if user.group:
            group = user.group
        if user.signature:
            signature = user.signature

    return render_template('page2.html',
                           posts=posts_with_avatars,
                           username=session.get('username'),
                           avatar=avatar,
                           group=group,
                           signature=signature)


@app.route('/page3')
def page3():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    posts = Post.query.filter_by(category='组队寻人').order_by(Post.created_at.desc()).all()

    # 为每个帖子添加作者头像信息
    posts_with_avatars = []
    for post in posts:
        author = User.query.get(post.user_id)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'intro': post.intro,
            'content': post.content,
            'created_at': post.created_at,
            'author': post.author,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        posts_with_avatars.append(post_dict)

    # 获取当前登录用户信息
    signature = '未设置个性签名'
    avatar = '/static/image/look.jpg'
    group = '极创组'

    user = User.query.filter_by(username=session['username']).first()
    if user:
        if user.avatar:
            avatar = user.avatar
        if user.group:
            group = user.group
        if user.signature:
            signature = user.signature

    return render_template('page3.html',
                           posts=posts_with_avatars,
                           username=session.get('username'),
                           avatar=avatar,
                           group=group,
                           signature=signature)


# 个人博客路由
@app.route('/my_blog1')
def my_blog1():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('用户信息不存在，请重新登录！', 'error')
        session.clear()
        return redirect(url_for('log_in'))

    posts = Post.query.filter_by(
        category='技术求助',
        user_id=user.id
    ).order_by(Post.created_at.desc()).all()

    # 为每个帖子添加作者头像信息
    posts_with_avatars = []
    for post in posts:
        author = User.query.get(post.user_id)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'intro': post.intro,
            'content': post.content,
            'created_at': post.created_at,
            'author': post.author,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        posts_with_avatars.append(post_dict)

    # 获取用户信息
    avatar = user.avatar if user.avatar else '/static/image/look.jpg'
    group = user.group if user.group else '极创组'
    signature = user.signature if user.signature else '未设置个性签名'

    return render_template('my_blog1.html',
                           posts=posts_with_avatars,
                           username=username,
                           avatar=avatar,
                           group=group,
                           signature=signature)


@app.route('/my_blog2')
def my_blog2():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('用户信息不存在，请重新登录！', 'error')
        session.clear()
        return redirect(url_for('log_in'))

    posts = Post.query.filter_by(
        category='日常休闲',
        user_id=user.id
    ).order_by(Post.created_at.desc()).all()

    # 为每个帖子添加作者头像信息
    posts_with_avatars = []
    for post in posts:
        author = User.query.get(post.user_id)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'intro': post.intro,
            'content': post.content,
            'created_at': post.created_at,
            'author': post.author,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        posts_with_avatars.append(post_dict)

    # 获取用户信息
    avatar = user.avatar if user.avatar else '/static/image/look.jpg'
    group = user.group if user.group else '极创组'
    signature = user.signature if user.signature else '未设置个性签名'

    return render_template('my_blog2.html',
                           posts=posts_with_avatars,
                           username=username,
                           avatar=avatar,
                           group=group,
                           signature=signature)


@app.route('/my_blog3')
def my_blog3():
    if 'username' not in session:
        return redirect(url_for('log_in'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('用户信息不存在，请重新登录！', 'error')
        session.clear()
        return redirect(url_for('log_in'))

    posts = Post.query.filter_by(
        category='组队寻人',
        user_id=user.id
    ).order_by(Post.created_at.desc()).all()

    # 为每个帖子添加作者头像信息
    posts_with_avatars = []
    for post in posts:
        author = User.query.get(post.user_id)
        post_dict = {
            'id': post.id,
            'title': post.title,
            'intro': post.intro,
            'content': post.content,
            'created_at': post.created_at,
            'author': post.author,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        posts_with_avatars.append(post_dict)

    # 获取用户信息
    avatar = user.avatar if user.avatar else '/static/image/look.jpg'
    group = user.group if user.group else '极创组'
    signature = user.signature if user.signature else '未设置个性签名'

    return render_template('my_blog3.html',
                           posts=posts_with_avatars,
                           username=username,
                           avatar=avatar,
                           group=group,
                           signature=signature)


# 忘记密码
@app.route('/forget')
def forget():
    return redirect(url_for('reset_password'))


# 重置密码
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        verification_code = generate_verification_code()
        session['verification_code'] = verification_code
        return render_template('forget.html', verification_code=verification_code)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        user_verification_code = request.form.get('verification_code', '').strip().upper()
        real_code = session.get('verification_code', '').upper()

        if not all([username, email, new_password, confirm_password, user_verification_code]):
            flash('请填写所有必填字段！', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        if new_password != confirm_password:
            flash('两次输入的新密码不一致！', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        if not real_code or user_verification_code != real_code:
            flash(f'验证码错误！正确验证码是：{real_code}', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        user = User.query.filter(
            User.username == username,
            User.email.ilike(email)
        ).first()

        if not user:
            flash('用户名或邮箱不匹配！', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

        try:
            user.set_password(new_password)
            db.session.commit()
            session.pop('verification_code', None)
            flash('密码重置成功！请使用新密码登录', 'success')
            return redirect(url_for('log_in'))
        except Exception as e:
            db.session.rollback()
            flash(f'密码重置失败：{str(e)}', 'error')
            new_code = generate_verification_code()
            session['verification_code'] = new_code
            return render_template('forget.html', verification_code=new_code)

    verification_code = generate_verification_code()
    session['verification_code'] = verification_code
    return render_template('forget.html', verification_code=verification_code)


# 发帖页面
@app.route('/post')
def post():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    username = session.get('username')

    # 获取用户信息
    signature = '未设置个性签名'
    avatar = '/static/image/look.jpg'
    group = '极创组'

    user = User.query.filter_by(username=username).first()
    if user:
        if user.avatar:
            avatar = user.avatar
        if user.group:
            group = user.group
        if user.signature:
            signature = user.signature

    return render_template('post.html',
                           username=username,
                           avatar=avatar,
                           group=group,
                           signature=signature)


# 提交帖子
@app.route('/submit_post', methods=['POST'])
def submit_post():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    username = session['username']
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    category = request.form.get('category', '技术求助')

    if not title or not content:
        flash('标题和内容不能为空！', 'error')
        return redirect(url_for('post'))

    user = User.query.filter_by(username=username).first()
    if user:
        new_post = Post(
            title=title,
            content=content,
            user_id=user.id,
            category=category,
            like_count=0,
            collect_count=0
        )
        db.session.add(new_post)
        db.session.commit()
        flash('帖子发布成功！', 'success')
        return redirect(url_for('page'))
    else:
        flash('用户不存在！', 'error')
        return redirect(url_for('log_in'))


# 提交评论
@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if 'username' not in session:
        if is_ajax:
            return jsonify({'success': False, 'msg': '请先登录'})
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    post_id = request.form.get('post_id')
    username = session['username']
    content = request.form.get('content', '')

    if not content or not post_id:
        if is_ajax:
            return jsonify({'success': False, 'msg': '评论内容不能为空'})
        flash('评论内容不能为空！', 'error')
        return redirect(url_for('post_detail', post_id=post_id))

    user = User.query.filter_by(username=username).first()
    if not user:
        if is_ajax:
            return jsonify({'success': False, 'msg': '用户不存在'})
        flash('用户不存在！', 'error')
        return redirect(url_for('log_in'))

    try:
        new_comment = Comment(
            content=content,
            post_id=post_id,
            user_id=user.id,
            created_at=datetime.now()
        )
        db.session.add(new_comment)
        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'msg': '评论成功',
                'comment': {
                    'id': new_comment.id,
                    'content': new_comment.content,
                    'author': new_comment.user.username,
                    'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        flash('评论成功！', 'success')
        return redirect(url_for('post_detail', post_id=post_id))
    except Exception as e:
        db.session.rollback()
        if is_ajax:
            return jsonify({'success': False, 'msg': f'评论失败：{str(e)}'})
        flash(f'评论失败：{str(e)}', 'error')
        return redirect(url_for('post_detail', post_id=post_id))


# 删除评论
@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    if 'username' not in session:
        return jsonify({'success': False, 'msg': '请先登录'})

    comment_id = request.form.get('comment_id')
    post_id = request.form.get('post_id')

    if not comment_id or not post_id:
        return jsonify({'success': False, 'msg': '参数不全'})

    username = session['username']
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'msg': '用户不存在'})

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'success': False, 'msg': '评论不存在'})

    if comment.user_id != user.id:
        return jsonify({'success': False, 'msg': '无权删除该评论'})

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True, 'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'msg': f'删除失败：{str(e)}'})


# 个人信息页面
@app.route('/my_information')
def my_information():
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))
    username = session['username']
    user = User.query.filter_by(username=username).first()

    if user:
        return render_template(
            'my_information.html',
            username=username,
            group=user.group,
            email=user.email,
            reg_time=user.created_at.strftime('%Y-%m-%d'),
            signature=user.signature,
            avatar=user.avatar
        )
    else:
        flash('用户信息获取失败！', 'error')
        return redirect(url_for('page'))



# 帖子详情
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id).first()
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()

    # 为每个评论添加作者头像信息
    comments_with_avatars = []
    for comment in comments:
        author = User.query.get(comment.user_id)
        comment_dict = {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at,
            'user': comment.user,
            'author_avatar': author.avatar if author and author.avatar else '/static/image/look.jpg'
        }
        comments_with_avatars.append(comment_dict)

    is_liked = False
    is_collected = False

    # 获取当前登录用户信息
    signature = '未设置个性签名'
    avatar = '/static/image/look.jpg'
    group = '极创组'

    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            is_liked = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
            is_collected = Collect.query.filter_by(user_id=user.id, post_id=post_id).first()
            if user.avatar:
                avatar = user.avatar
            if user.group:
                group = user.group
            if user.signature:
                signature = user.signature

    return render_template('show.html',
                           post=post,
                           comments=comments_with_avatars,
                           username=session.get('username'),
                           is_liked=is_liked,
                           is_collected=is_collected,
                           avatar=avatar,
                           group=group,
                           signature=signature)


# 更新个性签名
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


# 点赞
@app.route('/post/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'username' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'msg': '请先登录'})
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    user = User.query.filter_by(username=session['username']).first()
    post = Post.query.get(post_id)

    if not post:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'msg': '帖子不存在'})
        flash('帖子不存在！', 'error')
        return redirect(url_for('page'))

    existing_like = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
    if existing_like:
        db.session.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'new_count': post.like_count, 'action': 'unlike'})
        flash('取消点赞成功！', 'success')
    else:
        new_like = Like(user_id=user.id, post_id=post_id)
        db.session.add(new_like)
        post.like_count += 1
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'new_count': post.like_count, 'action': 'like'})
        flash('点赞成功！', 'success')

    return redirect(url_for('post_detail', post_id=post_id))


# 收藏
@app.route('/post/collect/<int:post_id>', methods=['POST'])
def collect_post(post_id):
    if 'username' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'msg': '请先登录'})
        flash('请先登录！', 'error')
        return redirect(url_for('log_in'))

    user = User.query.filter_by(username=session['username']).first()
    post = Post.query.get(post_id)

    if not post:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'msg': '帖子不存在'})
        flash('帖子不存在！', 'error')
        return redirect(url_for('page'))

    existing_collect = Collect.query.filter_by(user_id=user.id, post_id=post_id).first()
    if existing_collect:
        db.session.delete(existing_collect)
        post.collect_count = max(0, post.collect_count - 1)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'new_count': post.collect_count, 'action': 'uncollect'})
        flash('取消收藏成功！', 'success')
    else:
        new_collect = Collect(user_id=user.id, post_id=post_id)
        db.session.add(new_collect)
        post.collect_count += 1
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'new_count': post.collect_count, 'action': 'collect'})
        flash('收藏成功！', 'success')

    return redirect(url_for('post_detail', post_id=post_id))


# 【修复安全漏洞】删除帖子时检查作者权限
@app.route('/delete_post', methods=['POST'])
def delete_post():
    if 'username' not in session:
        return {'success': False, 'msg': '请先登录'}

    post_id = request.form.get('post_id')
    if not post_id:
        return {'success': False, 'msg': '缺少帖子ID'}
 
    # 获取当前用户
    current_user_obj = User.query.filter_by(username=session['username']).first()
    if not current_user_obj:
        return {'success': False, 'msg': '用户不存在'}
    
    # 获取帖子
    post = Post.query.get(post_id)
    if not post:
        return {'success': False, 'msg': '帖子不存在'}
    
    # ★★★ 关键权限检查：只有作者才能删除自己的帖子 ★★★
    if post.user_id != current_user_obj.id:
        return {'success': False, 'msg': '无权删除此帖子'}
    
    try:
        Comment.query.filter_by(post_id=post_id).delete()
        Like.query.filter_by(post_id=post_id).delete()
        Collect.query.filter_by(post_id=post_id).delete()

        db.session.delete(post)
        db.session.commit()
        return {'success': True}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'msg': f'删帖失败：{str(e)}'}


# ====== 头像上传相关路由 ======

# 更新头像的路由
@app.route('/update_avatar', methods=['POST'])
def update_avatar():
    if 'username' not in session:
        return jsonify({'success': False, 'msg': '请先登录'})

    if 'avatar' not in request.files:
        return jsonify({'success': False, 'msg': '没有上传文件'})

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'msg': '没有选择文件'})

    if file and allowed_file(file.filename):
        username = session['username']
        filename = secure_filename(
            f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        user = User.query.filter_by(username=username).first()
        if user:
            avatar_url = f'/static/uploads/avatars/{filename}'
            user.avatar = avatar_url
            db.session.commit()
            return jsonify({'success': True, 'avatar_url': avatar_url})

    return jsonify({'success': False, 'msg': '文件类型不允许'})


# 更新所有个人信息的路由
@app.route('/update_profile_full', methods=['POST'])
def update_profile_full():
    if 'username' not in session:
        return jsonify({'success': False, 'msg': '请先登录'})

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'success': False, 'msg': '用户不存在'})

    try:
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(
                    f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                avatar_url = f'/static/uploads/avatars/{filename}'
                user.avatar = avatar_url

        new_username = request.form.get('username')
        new_group = request.form.get('group')
        new_email = request.form.get('email')
        new_signature = request.form.get('signature')

        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return jsonify({'success': False, 'msg': '用户名已存在'})
            user.username = new_username
            session['username'] = new_username

        if new_group:
            user.group = new_group

        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                return jsonify({'success': False, 'msg': '邮箱已被注册'})
            user.email = new_email

        if new_signature:
            user.signature = new_signature

        db.session.commit()
        return jsonify({'success': True, 'msg': '更新成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'msg': str(e)})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("数据库表已创建")
    app.run(debug=True, port=5000)
#4/8 16:30
# 删除帖子权限漏洞：/delete_post 路由只检查了登录状态，未验证当前用户是否为帖子作者。现已添加作者身份校验，确保只有作者本人能删除自己的帖子。

# 重复的登出路由：原代码中有两个 /logout 路由，第二个覆盖了第一个且未正确清除 Flask-Login 会话。现已合并为一个，使用 logout_user() 并清理 session。

# 缺失的导入：补充了 flask_login 中的 login_user, logout_user, login_required, current_user 导入，确保登录相关功能正常。

# 删除评论权限：原有逻辑已正确校验，无需修改。

# 其他安全增强：头像上传使用了 secure_filename，密码哈希使用 werkzeug，SQL 查询使用参数化，无注入风险。