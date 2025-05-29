from app import app, db, bcrypt, User

with app.app_context():
    # Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        db.session.add(admin)

    db.session.commit()
    print("✅ User default berhasil ditambahkan.")
