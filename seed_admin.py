from app import db
from app.models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

if not User.query.filter_by(telepon='08123456789').first():
    hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
    admin = User(
        telepon='08123456789',
        password=hashed_pw,
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin default berhasil ditambahkan.")
else:
    print("✅ Admin sudah ada.")
