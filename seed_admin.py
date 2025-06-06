from flask_bcrypt import Bcrypt
from app import app, db, User  # ambil langsung dari app.py

bcrypt = Bcrypt(app)

default_telepon = '08123456789'
default_password = 'admin123'
default_role = 'admin'

with app.app_context():
    existing_admin = User.query.filter_by(telepon=default_telepon).first()

    if not existing_admin:
        hashed_password = bcrypt.generate_password_hash(default_password).decode('utf-8')
        admin = User(
            telepon=default_telepon,
            password=hashed_password,
            role=default_role,
            username='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin default berhasil ditambahkan. Nomor: {default_telepon}")
    else:
        print("✅ Admin sudah ada.")
