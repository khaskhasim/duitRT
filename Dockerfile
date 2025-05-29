# Gunakan image Python dengan Debian
FROM python:3.11

# Install PostgreSQL
RUN apt-get update && apt-get install -y postgresql postgresql-contrib

# Buat direktori kerja
WORKDIR /app

# Salin semua file ke container
COPY . /app

# Install dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Buat user PostgreSQL dan database
USER postgres
RUN service postgresql start && \
    psql --command "CREATE USER kasrt_user WITH PASSWORD 'passwordku';" && \
    createdb -O kasrt_user kasrt

# Kembali ke user root
USER root

# Salin dan beri izin eksekusi untuk entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port untuk Flask dan PostgreSQL
EXPOSE 5000
EXPOSE 5432

# Jalankan skrip startup
CMD ["/entrypoint.sh"]
