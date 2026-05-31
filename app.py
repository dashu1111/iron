from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from models import db, User
from flask_migrate import Migrate
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 注册蓝图
    from auth.routes import auth_bp
    from worker.routes import worker_bp
    from leader.routes import leader_bp
    from admin.routes import admin_bp
    from group_leader.routes import group_leader_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(worker_bp, url_prefix='/worker')
    app.register_blueprint(group_leader_bp, url_prefix='/group_leader')
    app.register_blueprint(leader_bp, url_prefix='/leader')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 首页跳转
    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        role = current_user.role
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'leader':
            return redirect(url_for('leader.dashboard'))
        elif role == 'group_leader':
            return redirect(url_for('group_leader.dashboard'))
        else:
            return redirect(url_for('worker.dashboard'))

    return app

if __name__ == '__main__':
    app = create_app()
    # 创建 instance 目录
    os.makedirs(app.instance_path, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)