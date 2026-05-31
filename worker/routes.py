from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Overtime, Leave, Bonus
from datetime import datetime, date
from utils import role_required

worker_bp = Blueprint('worker', __name__)

@worker_bp.route('/dashboard')
@login_required
@role_required('worker')
def dashboard():
    # 本月奖金总计
    now = datetime.now()
    ym = f"{now.year}-{now.month:02d}"
    bonuses = Bonus.query.filter_by(user_id=current_user.id, year_month=ym).all()
    total_bonus = sum(b.amount for b in bonuses)
    # 待审加班/请假条数
    ot_pending = Overtime.query.filter_by(user_id=current_user.id, status='pending').count()
    lv_pending = Leave.query.filter_by(user_id=current_user.id, status='pending').count()
    return render_template('worker/dashboard.html', total_bonus=total_bonus,
                           ot_pending=ot_pending, lv_pending=lv_pending)

@worker_bp.route('/overtime/add', methods=['GET', 'POST'])
@login_required
@role_required('worker')
def overtime_add():
    if request.method == 'POST':
        ot = Overtime(
            user_id=current_user.id,
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            shift=request.form['shift'],
            ot_type=request.form['ot_type'],
            start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
            reason=request.form['reason']
        )
        db.session.add(ot)
        db.session.commit()
        flash('加班申请已提交', 'success')
        return redirect(url_for('worker.my_records'))
    return render_template('worker/overtime_submit.html')

@worker_bp.route('/leave/add', methods=['GET', 'POST'])
@login_required
@role_required('worker')
def leave_add():
    if request.method == 'POST':
        lv = Leave(
            user_id=current_user.id,
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            leave_type=request.form['leave_type'],
            reason=request.form['reason']
        )
        db.session.add(lv)
        db.session.commit()
        flash('请假申请已提交', 'success')
        return redirect(url_for('worker.my_records'))
    return render_template('worker/leave_submit.html')

@worker_bp.route('/records')
@login_required
@role_required('worker')
def my_records():
    ots = Overtime.query.filter_by(user_id=current_user.id).order_by(Overtime.date.desc()).all()
    leaves = Leave.query.filter_by(user_id=current_user.id).order_by(Leave.start_date.desc()).all()
    return render_template('worker/my_records.html', ots=ots, leaves=leaves)