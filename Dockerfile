FROM python:3.11

# Install PostgreSQL Server
RUN apt-get update && apt-get install -y postgresql postgresql-contrib

# Create working directory
WORKDIR /app

# Copy app files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Setup PostgreSQL DB and user
USER postgres
RUN service postgresql start && \
    psql --command "CREATE USER kasrt_user WITH PASSWORD 'passwordku';" && \
    createdb -O kasrt_user kasrt

USER root

# Expose ports (Flask and Postgres)
EXPOSE 5000
EXPOSE 5432

# Jalankan PostgreSQL dan Flask app (pakai supervisord atau script bash)
CMD service postgresql start && \
    flask db init && \
    flask db migrate -m "Init PostgreSQL" && \
    flask db upgrade && \
    gunicorn -b 0.0.0.0:5000 app:app

