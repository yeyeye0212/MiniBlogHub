#数据库扩展文件
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()