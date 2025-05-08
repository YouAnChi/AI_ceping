from flask import Flask
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # 创建实例文件夹
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # 配置日志
    log_file = app.config['LOG_FILE']
    handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app