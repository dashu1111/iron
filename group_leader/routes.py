from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from models import db, User, Overtime, Leave, Bonus
from datetime import datetime
from utils import role_required, export_excel, calculate_overtime_amount

group_leader_bp = Blueprint('group_leader', __name__)

def get_my_group():
    """返回当前班组长的作业区+班组"""
    return current_user.department, current_user.group

@group_leader_bp.route('/dashboard')
@login_required
@role_required('group_leader')
def dashboard():
    dept, group = get_my_group()
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
    workers = User.query.filter_by(department=dept, role='worker', enabled=True) \
                         .order_by(User.group, User.name).all()

    if request.method == 'POST':
        date_str = request.form['date']
        shift = request.form['shift']
        ot_type = request.form['ot_type']

        selected_ids = request.form.getlist('selected_workers')
        if not selected_ids:
            flash('未选中人员', 'warning')
            return redirect(url_for('group_leader.batch_overtime'))
        count = 0
        for wid in selected_ids:
            qty = float(request.form.get(f'quantity_{wid}', 0) or 0)
            manual_amt = float(request.form.get(f'manual_amount_{wid}', 0) or 0)
            amount = calculate_overtime_amount(
                ot_type, shift, qty,
                manual_amt if ot_type == '支撑检修' else None
            )
            ot = Overtime(
                user_id=int(wid),
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                shift=shift,
                ot_type=ot_type,
                start_time=datetime.strptime(request.form.get(f'start_time_{wid}', '18:00'), '%H:%M').time(),
                end_time=datetime.strptime(request.form.get(f'end_time_{wid}', '21:00'), '%H:%M').time(),
                reason=request.form.get(f'reason_{wid}', ''),
                quantity=qty if ot_type == '离线' else None,
                amount=amount,
                status='pending',
                submitter_id=current_user.id
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
    ots = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, User.group == group) \
        .order_by(Overtime.date.desc()).limit(100).all()
    leaves = Leave.query.join(User, Leave.user_id == User.id) \
        .filter(User.department == dept, User.group == group) \
        .order_by(Leave.start_date.desc()).limit(100).all()
    return render_template('group_leader/records.html', ots=ots, leaves=leaves)
