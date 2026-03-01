#配置文件
import os

class Config:
    SECRET_KEY = 'elab-blog-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///elab-blog-system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False