#!/bin/sh

echo "🚀 Menjalankan PostgreSQL..."
service postgresql start

# Hanya init migration jika folder belum ada
if [ ! -d "migrations" ]; then
    echo "📁 Membuat direktori migrations..."
    flask db init
fi

echo "🔄 Menjalankan migrasi database..."
flask db migrate -m "Init PostgreSQL" || true
flask db upgrade

echo "👤 Menambahkan user admin default..."
python3 seed_admin.py

echo "🧠 Menjalankan aplikasi Flask dengan Gunicorn..."
gunicorn -b 0.0.0.0:5000 app:app
