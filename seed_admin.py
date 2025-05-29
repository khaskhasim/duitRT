from app import db, bcrypt, User

with db.app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        db.session.add(admin)
        print("✔ Admin 'admin' ditambahkan")

    if not User.query.filter_by(username='petugas1').first():
        petugas = User(
            username='petugas1',
            password=bcrypt.generate_password_hash('petugas123').decode('utf-8'),
            role='petugas'
        )
        db.session.add(petugas)
        print("✔ Petugas 'petugas1' ditambahkan")

    db.session.commit()
