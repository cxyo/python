# scf_bootstrap.py
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from app import app

def main_handler(event, context):
    """SCF入口函数"""
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import run_simple
    
    # 将Flask应用包装成WSGI应用
    return DispatcherMiddleware(app)