from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Overtime, Leave, Bonus
from datetime import datetime
from utils import role_required, calculate_overtime_amount

worker_bp = Blueprint('worker', __name__)

@worker_bp.route('/dashboard')
@login_required
@role_required('worker')
def dashboard():
    now = datetime.now()
    ym = f"{now.year}-{now.month:02d}"
    bonuses = Bonus.query.filter_by(user_id=current_user.id, year_month=ym).all()
    total_bonus = sum(b.amount for b in bonuses)
    ot_pending = Overtime.query.filter_by(user_id=current_user.id, status='pending').count()
    ot_approved = Overtime.query.filter_by(user_id=current_user.id, status='approved').count()
    lv_pending = Leave.query.filter_by(user_id=current_user.id, status='pending').count()
    lv_approved = Leave.query.filter_by(user_id=current_user.id, status='approved').count()
    return render_template('worker/dashboard.html',
                           total_bonus=total_bonus,
                           ot_pending=ot_pending, ot_approved=ot_approved,
                           lv_pending=lv_pending, lv_approved=lv_approved)

@worker_bp.route('/overtime/add', methods=['GET', 'POST'])
@login_required
@role_required('worker')
def overtime_add():
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
            user_id=current_user.id,
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            shift=shift,
            ot_type=ot_type,
            start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
            reason=request.form.get('reason', ''),
            quantity=qty if ot_type == '离线' else None,
            amount=amount,
            submitter_id=current_user.id
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
    bonuses = Bonus.query.filter_by(user_id=current_user.id).order_by(Bonus.year_month.desc()).all()
    return render_template('worker/my_records.html', ots=ots, leaves=leaves, bonuses=bonuses)
