"""Initialize database and create default admin user if missing."""
from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            name='管理员',
            role='admin',
            enabled=True,
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Created admin user: admin / admin123')
    else:
        print('Admin user already exists')
