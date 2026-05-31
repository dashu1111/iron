from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from models import db, User, Overtime, Leave, Bonus
from datetime import datetime
from utils import role_required, export_excel

group_leader_bp = Blueprint('group_leader', __name__)

def get_my_group():
    """返回当前班组长的作业区+班组"""
    return current_user.department, current_user.group

@group_leader_bp.route('/dashboard')
@login_required
@role_required('group_leader')
def dashboard():
    dept, group = get_my_group()
    # 统计本班组待审批加班/请假数量（由班组长代填但尚未被作业长审批的）
    ot_pending = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, User.group == group,
                Overtime.status == 'pending').count()
    lv_pending = Leave.query.join(User, Leave.user_id == User.id) \
        .filter(User.department == dept, User.group == group,
                Leave.status == 'pending').count()
    return render_template('group_leader/dashboard.html',
                           ot_pending=ot_pending, lv_pending=lv_pending)

@group_leader_bp.route('/batch_overtime', methods=['GET', 'POST'])
@login_required
@role_required('group_leader')
def batch_overtime():
    dept, group = get_my_group()
    # 获取本班组的所有在职员工
    workers = User.query.filter_by(department=dept, group=group,
                                   role='worker', enabled=True).order_by(User.name).all()

    if request.method == 'POST':
        date_str = request.form['date']
        shift = request.form['shift']
        ot_type = request.form['ot_type']
        base_start = request.form['start_time']
        base_end = request.form['end_time']
        base_reason = request.form.get('reason', '')

        selected_ids = request.form.getlist('selected_workers')
        count = 0
        for wid in selected_ids:
            # 支持个性化时间/事由，如果前端提供了则覆盖默认值
            start = request.form.get(f'start_{wid}', base_start)
            end = request.form.get(f'end_{wid}', base_end)
            reason = request.form.get(f'reason_{wid}', base_reason)

            ot = Overtime(
                user_id=int(wid),
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                shift=shift,
                ot_type=ot_type,
                start_time=datetime.strptime(start, '%H:%M').time(),
                end_time=datetime.strptime(end, '%H:%M').time(),
                reason=reason,
                status='pending'  # 等待作业长审批
            )
            db.session.add(ot)
            count += 1
        db.session.commit()
        flash(f'已为 {count} 名员工提交加班申请', 'success')
        return redirect(url_for('group_leader.dashboard'))
    return render_template('group_leader/batch_overtime.html', workers=workers)

@group_leader_bp.route('/batch_leave', methods=['GET', 'POST'])
@login_required
@role_required('group_leader')
def batch_leave():
    dept, group = get_my_group()
    workers = User.query.filter_by(department=dept, group=group,
                                   role='worker', enabled=True).order_by(User.name).all()

    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        leave_type = request.form['leave_type']
        reason = request.form.get('reason', '')

        selected_ids = request.form.getlist('selected_workers')
        count = 0
        for wid in selected_ids:
            lv = Leave(
                user_id=int(wid),
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                leave_type=leave_type,
                reason=reason,
                status='pending'
            )
            db.session.add(lv)
            count += 1
        db.session.commit()
        flash(f'已为 {count} 名员工提交请假申请', 'success')
        return redirect(url_for('group_leader.dashboard'))
    return render_template('group_leader/batch_leave.html', workers=workers)

@group_leader_bp.route('/records')
@login_required
@role_required('group_leader')
def records():
    dept, group = get_my_group()
    # 查看本班组所有人的加班和请假记录（最近100条）
    ots = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, User.group == group) \
        .order_by(Overtime.date.desc()).limit(100).all()
    leaves = Leave.query.join(User, Leave.user_id == User.id) \
        .filter(User.department == dept, User.group == group) \
        .order_by(Leave.start_date.desc()).limit(100).all()
    return render_template('group_leader/records.html', ots=ots, leaves=leaves)