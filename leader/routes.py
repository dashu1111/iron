from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from models import db, User, Overtime, Leave, Bonus
from datetime import datetime
from utils import role_required, export_excel, calculate_overtime_amount

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

@leader_bp.route('/overtime/approve/all', methods=['POST'])
@login_required
@role_required('leader')
def approve_all_ot():
    dept = get_dept()
    ots = Overtime.query.join(User, Overtime.user_id == User.id) \
        .filter(User.department == dept, Overtime.status == 'pending').all()
    if not ots:
        flash('暂无待审批记录', 'info')
        return redirect(url_for('leader.ot_approve'))
    for ot in ots:
        ot.status = 'approved'
        ot.reviewer_id = current_user.id
    db.session.commit()
    flash(f'已一键通过 {len(ots)} 条加班申请', 'success')
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
        ot_type = request.form['ot_type']
        shift = request.form['shift']
        qty = float(request.form.get('quantity', 0) or 0)
        manual_amt = float(request.form.get('manual_amount', 0) or 0)
        amount = calculate_overtime_amount(
            ot_type, shift, qty,
            manual_amt if ot_type == '支撑检修' else None
        )
        ot = Overtime(
            user_id=request.form['user_id'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            shift=shift,
            ot_type=ot_type,
            start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
            reason=request.form.get('reason', ''),
            quantity=qty if ot_type == '离线' else None,
            amount=amount,
            status='approved',
            reviewer_id=current_user.id,
            submitter_id=current_user.id
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
        if ot.amount is None and ot.ot_type in ['在线内包', '在线外包', '行车', '离线']:
            amount = calculate_overtime_amount(ot.ot_type, ot.shift, ot.quantity or 0)
        else:
            amount = ot.amount or 0.0
        hours = round(
            (datetime.combine(datetime.today(), ot.end_time) -
             datetime.combine(datetime.today(), ot.start_time)).seconds / 3600,
            1
        )
        data.append([
            user.name, user.department, user.group or '',
            ot.date.strftime('%Y-%m-%d'), ot.shift, ot.ot_type,
            ot.start_time.strftime('%H:%M'), ot.end_time.strftime('%H:%M'), hours,
            ot.quantity or '', round(amount, 2), ot.reason
        ])
    output = export_excel(
        ['姓名', '作业区', '班组', '日期', '班次', '加班类型', '开始', '结束', '时长', '产量(包)', '加班费', '事由'],
        data,
        sheet_name='加班记录',
        col_widths=[10, 12, 8, 15, 8, 12, 10, 10, 8, 10, 10, 30]
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