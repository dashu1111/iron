from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='worker')  # admin, leader, worker
    group = db.Column(db.String(64), nullable=True)  # 班组名称，如 'A班'、'B班'
    department = db.Column(db.String(64), nullable=True)
    enabled = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Overtime(db.Model):
    __tablename__ = 'overtimes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10))
    ot_type = db.Column(db.String(20))  # 在线内包 / 在线外包 / 行车 / 离线 / 支撑检修
    quantity = db.Column(db.Float, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    submit_time = db.Column(db.DateTime, default=datetime.now)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_comment = db.Column(db.String(200))
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='overtimes')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    submitter = db.relationship('User', foreign_keys=[submitter_id], backref='submitted_overtimes')

class Leave(db.Model):
    __tablename__ = 'leaves'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(20))
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    submit_time = db.Column(db.DateTime, default=datetime.now)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_comment = db.Column(db.String(200))

    user = db.relationship('User', foreign_keys=[user_id], backref='leaves')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])

class Bonus(db.Model):
    __tablename__ = 'bonuses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year_month = db.Column(db.String(7), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    reason = db.Column(db.String(200))
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_time = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', foreign_keys=[user_id], backref='bonuses')
    assigner = db.relationship('User', foreign_keys=[assigned_by])