from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from models import db, User, Overtime, Leave, Bonus
from datetime import datetime
from utils import role_required, export_excel

leader_bp = Blueprint('leader', __name__)

def get_dept():
    return current_user.department

@leader_bp.route('/dashboard')
@login_required
@role_required('leader')
def dashboard():
    dept = get_dept()
    ot_pending = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, Overtime.status == 'pending').count()
    lv_pending = Leave.query.join(User, Leave.user_id == User.id) \
        .filter(User.department == dept, Leave.status == 'pending').count()
    return render_template('leader/dashboard.html', ot_pending=ot_pending, lv_pending=lv_pending)

@leader_bp.route('/overtime/approve')
@login_required
@role_required('leader')
def ot_approve():
    dept = get_dept()
    ots = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, Overtime.status == 'pending').all()
    return render_template('leader/ot_approve.html', ots=ots)

@leader_bp.route('/overtime/approve/<int:id>/<action>')
@login_required
@role_required('leader')
def handle_ot(id, action):
    ot = db.session.get(Overtime, id)
    if not ot:
        flash('记录不存在', 'danger')
        return redirect(url_for('leader.ot_approve'))
    if ot.user.department != current_user.department:
        flash('无权操作', 'danger')
        return redirect(url_for('leader.ot_approve'))
    if action == 'approve':
        ot.status = 'approved'
    elif action == 'reject':
        ot.status = 'rejected'
    ot.reviewer_id = current_user.id
    db.session.commit()
    flash('操作成功', 'success')
    return redirect(url_for('leader.ot_approve'))

@leader_bp.route('/leave/approve')
@login_required
@role_required('leader')
def leave_approve():
    dept = get_dept()
    leaves = Leave.query.join(User, Leave.user_id == User.id) \
        .filter(User.department == dept, Leave.status == 'pending').all()
    return render_template('leader/leave_approve.html', leaves=leaves)

@leader_bp.route('/leave/approve/<int:id>/<action>')
@login_required
@role_required('leader')
def handle_leave(id, action):
    lv = db.session.get(Leave, id)
    if not lv:
        flash('记录不存在', 'danger')
        return redirect(url_for('leader.leave_approve'))
    if lv.user.department != current_user.department:
        flash('无权操作', 'danger')
        return redirect(url_for('leader.leave_approve'))
    if action == 'approve':
        lv.status = 'approved'
    else:
        lv.status = 'rejected'
    lv.reviewer_id = current_user.id
    db.session.commit()
    flash('审批完成', 'success')
    return redirect(url_for('leader.leave_approve'))

@leader_bp.route('/overtime/add', methods=['GET', 'POST'])
@login_required
@role_required('leader')
def ot_add():
    dept = get_dept()
    workers = User.query.filter_by(department=dept, role='worker', enabled=True).all()
    if request.method == 'POST':
        ot = Overtime(
            user_id=request.form['user_id'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            shift=request.form['shift'],
            ot_type=request.form['ot_type'],
            start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
            reason=request.form.get('reason', ''),
            status='approved',
            reviewer_id=current_user.id
        )
        db.session.add(ot)
        db.session.commit()
        flash('代报加班成功', 'success')
        return redirect(url_for('leader.dashboard'))
    return render_template('leader/ot_add.html', workers=workers)

@leader_bp.route('/bonus/assign', methods=['GET', 'POST'])
@login_required
@role_required('leader')
def bonus_assign():
    dept = get_dept()
    workers = User.query.filter_by(department=dept, role='worker').all()
    if request.method == 'POST':
        year_month = request.form['year_month']
        for w in workers:
            amount = request.form.get(f'amount_{w.id}', 0)
            reason = request.form.get(f'reason_{w.id}', '')
            if float(amount) > 0:
                bonus = Bonus(
                    user_id=w.id,
                    year_month=year_month,
                    amount=float(amount),
                    reason=reason,
                    assigned_by=current_user.id
                )
                db.session.add(bonus)
        db.session.commit()
        flash('奖金分配完成', 'success')
        return redirect(url_for('leader.dashboard'))
    return render_template('leader/bonus_assign.html', workers=workers)

@leader_bp.route('/records')
@login_required
@role_required('leader')
def records():
    dept = get_dept()
    ots = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept).all()
    return render_template('leader/records.html', ots=ots)

@leader_bp.route('/records/export')
@login_required
@role_required('leader')
def export_ot():
    dept = get_dept()
    ots = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, Overtime.status == 'approved').all()
    data = []
    for ot in ots:
        user = db.session.get(User, ot.user_id)
        if not user:
            continue
        hours = round(
            (datetime.combine(datetime.today(), ot.end_time) -
             datetime.combine(datetime.today(), ot.start_time)).seconds / 3600,
            1
        )
        data.append([
            user.name,
            user.department,
            ot.date.strftime('%Y-%m-%d'),
            ot.shift,
            ot.ot_type,
            ot.start_time.strftime('%H:%M'),
            ot.end_time.strftime('%H:%M'),
            hours,
            ot.reason
        ])
    output = export_excel(
        ['姓名', '作业区', '日期', '班次', '类型', '开始', '结束', '小时', '事由'],
        data,
        sheet_name='加班记录',
        col_widths=[10, 12, 15, 8, 12, 12, 12, 8, 30]
    )
    return send_file(output, as_attachment=True, download_name='加班统计.xlsx')

@leader_bp.route('/reset_password', methods=['GET', 'POST'])
@login_required
@role_required('leader')
def reset_password():
    dept = get_dept()
    workers = User.query.filter_by(department=dept, role='worker').all()
    if request.method == 'POST':
        user_id = request.form['user_id']
        user = db.session.get(User, int(user_id))
        if not user or user.department != current_user.department:
            flash('无权限', 'danger')
            return redirect(url_for('leader.reset_password'))
        user.set_password('123456')
        db.session.commit()
        flash(f'{user.name} 的密码已重置为 123456', 'success')
        return redirect(url_for('leader.dashboard'))
    return render_template('leader/reset_pwd.html', workers=workers)