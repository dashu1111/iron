from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, enabled=True).first()
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功', 'success')
            # 根据角色跳转
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'leader':
                return redirect(url_for('leader.dashboard'))
            elif user.role == 'group_leader':
                return redirect(url_for('group_leader.dashboard'))
            else:
                return redirect(url_for('worker.dashboard'))
        else:
            flash('用户名或密码错误，或账号已禁用', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pw = request.form['old_password']
        new_pw = request.form['new_password']
        if not current_user.check_password(old_pw):
            flash('原密码错误', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('index'))
    return render_template('auth/change_password.html')