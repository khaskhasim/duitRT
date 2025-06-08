## Versi PostgreSQL dari app.py (Kas RT)

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from sqlalchemy.sql import func, extract, literal_column
from collections import defaultdict
from flask_migrate import Migrate
import calendar
from flask import render_template, request
from io import BytesIO
import pandas as pd
from fpdf import FPDF
import xlsxwriter
import io
import csv
import sqlite3  # optional, bisa dihapus nanti
from flask_bcrypt import Bcrypt
from sqlalchemy import func, extract, desc, literal
from pytz import timezone
import calendar
from dotenv import load_dotenv
import os
##from models import Pengeluaran
##import requests

from pytz import timezone
from datetime import datetime

jakarta = timezone('Asia/Jakarta')
now = datetime.now(jakarta)

load_dotenv()

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
#    'DATABASE_URL',
#    'postgresql://kasrt_user:passwordku@localhost:5432/kasrt'
#)

#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'rahasia-sangat-rahasia')

##import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')



db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# ✅ Tambahkan fungsi global untuk tanggal

def get_filter_dates():
    periode = request.args.get('periode', 'bulan-ini')
    today = date.today()

    if periode == 'hari-ini':
        return today, today
    elif periode == 'minggu-ini':
        awal = today - timedelta(days=today.weekday())
        return awal, awal + timedelta(days=6)
    elif periode == 'tahun-ini':
        return date(today.year, 1, 1), date(today.year, 12, 31)
    elif periode == 'custom':
        try:
            tgl_awal = datetime.strptime(request.args.get('tgl_awal'), '%Y-%m-%d').date()
            tgl_akhir = datetime.strptime(request.args.get('tgl_akhir'), '%Y-%m-%d').date()
            return tgl_awal, tgl_akhir
        except:
            return date(today.year, today.month, 1), today
    else:
        awal = date(today.year, today.month, 1)
        akhir = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        return awal, akhir
    



# =====================
# MODEL DATABASE
# =====================
class Warga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    nik = db.Column(db.String, unique=True, nullable=True)
    alamat = db.Column(db.String(255))
    telepon = db.Column(db.String(30), unique=True, nullable=False)  # login warga
    status = db.Column(db.String(20), default='aktif')
    username = db.Column(db.String(50), unique=True, nullable=True)  # login admin
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'petugas', 'user'



# Model Iuran
class Iuran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    warga_id = db.Column(db.Integer, db.ForeignKey('warga.id'), nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    petugas = db.Column(db.String(100), nullable=True)  

    # Relasi ke model Warga
    warga = db.relationship('Warga', backref=db.backref('iurans', lazy=True))

class IuranEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    warga_id = db.Column(db.Integer, db.ForeignKey('warga.id'), nullable=False)
    nama_event = db.Column(db.String(100), nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    jumlah = db.Column(db.Integer, nullable=False)
    keterangan = db.Column(db.String(255))
    petugas = db.Column(db.String(100))  # bisa diisi 'admin', 'petugas', atau nama warga yang input

    warga = db.relationship('Warga', backref='iuran_event')

class EventNama(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False, unique=True)


# Model Pengeluaran
class Pengeluaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, nullable=False)
    keterangan = db.Column(db.String(255), nullable=False)
    penerima = db.Column(db.String(100), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    petugas = db.Column(db.String(20), nullable=True)  # disimpan nomor telepon



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)  # 👉 ini baris yang kamu maksud
    telepon = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10))  # admin / petugas



class Petugas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    wa_number = db.Column(db.String(20), unique=True, nullable=False)


    
# =====================
# ROUTES
# =====================

app.secret_key = 'rahasia'  # Ganti dengan secret key aman


def insert_default_users():
    # Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        db.session.add(admin)

    # Petugas
    if not User.query.filter_by(username='petugas1').first():
        petugas = User(
            username='petugas1',
            password=bcrypt.generate_password_hash('petugas123').decode('utf-8'),
            role='petugas'
        )
        db.session.add(petugas)

    # Warga (user biasa)
    if not User.query.filter_by(username='warga1').first():
        warga = User(
            username='warga1',
            password=bcrypt.generate_password_hash('warga123').decode('utf-8'),
            role='user'
        )
        db.session.add(warga)

    db.session.commit()

def get_aktivitas_terkini(limit=10):
    zona_wib = timezone('Asia/Jakarta')

    # Siapkan mapping telepon → nama
    petugas_dict = {w.telepon: w.nama for w in Warga.query.with_entities(Warga.telepon, Warga.nama).all()}

    iuran_data = (
        db.session.query(
            Iuran.tanggal,
            Iuran.jumlah,
            Warga.nama.label('nama'),
            Iuran.petugas,
            literal_column("'Iuran'").label('jenis')
        )
        .join(Warga)
        .all()
    )

    pengeluaran_data = (
        db.session.query(
            Pengeluaran.tanggal,
            Pengeluaran.jumlah,
            Pengeluaran.keterangan.label('nama'),
            Pengeluaran.petugas,
            literal_column("'Pengeluaran'").label('jenis')
        )
        .all()
    )

    semua = iuran_data + pengeluaran_data
    semua.sort(key=lambda x: x.tanggal.astimezone(zona_wib), reverse=True)

    aktivitas = []
    for item in semua[:limit]:
        waktu = item.tanggal.astimezone(zona_wib).strftime('%d/%m/%Y %H:%M')
        nama_petugas = petugas_dict.get(item.petugas, item.petugas or "-")

        if item.jenis == 'Iuran':
            keterangan = f"💰 {item.nama} membayar iuran sebesar Rp {item.jumlah:,} oleh {nama_petugas}"
            warna = "success"
            ikon = "bi-cash-coin"
        else:
            keterangan = f"🧾 Pengeluaran: {item.nama} sebesar Rp {item.jumlah:,} oleh {nama_petugas}"
            warna = "danger"
            ikon = "bi-credit-card-2-front"

        aktivitas.append({
            "keterangan": keterangan,
            "waktu": waktu,
            "icon": ikon,
            "color": warna
        })

    return aktivitas


@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identitas = request.form['username'].strip()
        pw = request.form['password']

        # 1️⃣ ADMIN pakai username (contoh: 'admin')
        if identitas == 'admin':
            user = User.query.filter_by(username='admin').first()
            if user and bcrypt.check_password_hash(user.password, pw):
                session['username'] = user.username
                session['role'] = 'admin'
                return redirect(url_for('dashboard'))
            flash('Password salah untuk admin', 'danger')
            return render_template('login.html')

        # 2️⃣ PETUGAS dan WARGA pakai nomor telepon dari tabel Warga
        warga = Warga.query.filter_by(telepon=identitas).first()
        if warga and bcrypt.check_password_hash(warga.password, pw):
            session['telepon'] = warga.telepon
            session['role'] = warga.role  # 'user' atau 'petugas'
            return redirect(url_for('dashboard'))

        flash('Login gagal. Nomor telepon atau password salah.', 'danger')

    return render_template('login.html')





@app.route('/logout')
def logout():
    session.pop('username', None)  # Hapus session
    flash('Anda telah logout', 'success')  # Opsional: tampilkan pesan
    return redirect(url_for('login'))


@app.context_processor
def inject_datetime():
    return dict(datetime=datetime, date=date)


@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    bulan_ini = datetime.now(timezone('Asia/Jakarta')).month
    tahun_ini = datetime.now(timezone('Asia/Jakarta')).year

    if role == 'admin':
        total_warga = db.session.query(func.count(Warga.id)).scalar() or 0
        warga_aktif = db.session.query(func.count(Warga.id)).filter(Warga.status == 'aktif').scalar() or 0

        total_iuran_reguler = db.session.query(func.sum(Iuran.jumlah)).scalar() or 0
        total_iuran_event = db.session.query(func.sum(IuranEvent.jumlah)).scalar() or 0
        total_iuran = total_iuran_reguler + total_iuran_event

        total_pengeluaran = db.session.query(func.sum(Pengeluaran.jumlah)).scalar() or 0
        sisa_kas = total_iuran - total_pengeluaran

        iuran_bulan_ini = db.session.query(func.sum(Iuran.jumlah)).filter(
            extract('month', Iuran.tanggal) == bulan_ini,
            extract('year', Iuran.tanggal) == tahun_ini
        ).scalar() or 0

        iuran_event_bulan_ini = db.session.query(func.sum(IuranEvent.jumlah)).filter(
            extract('month', IuranEvent.tanggal) == bulan_ini,
            extract('year', IuranEvent.tanggal) == tahun_ini
        ).scalar() or 0

        total_iuran_bulan_ini = (iuran_bulan_ini or 0) + (iuran_event_bulan_ini or 0)

        target_iuran = total_warga * 600000
        persentase_iuran_bulan_ini = round((total_iuran_bulan_ini / target_iuran) * 100) if target_iuran > 0 else 0

        pengeluaran_bulan_ini = db.session.query(func.sum(Pengeluaran.jumlah)).filter(
            extract('month', Pengeluaran.tanggal) == bulan_ini,
            extract('year', Pengeluaran.tanggal) == tahun_ini
        ).scalar() or 0

        anggaran_bulanan = 200000
        persentase_pengeluaran_bulan_ini = round((pengeluaran_bulan_ini / anggaran_bulanan) * 100) if anggaran_bulanan > 0 else 0

        warga_bayar_bulan_ini = db.session.query(Iuran.warga_id).filter(
            extract('month', Iuran.tanggal) == bulan_ini,
            extract('year', Iuran.tanggal) == tahun_ini
        ).distinct().count()

        persentase_warga_aktif = round((warga_bayar_bulan_ini / warga_aktif) * 100) if warga_aktif > 0 else 0

        aktivitas_terkini = get_aktivitas_terkini()

        return render_template("dashboard.html",
            jumlah_warga=total_warga,
            total_iuran=total_iuran,
            total_pengeluaran=total_pengeluaran,
            sisa_kas=sisa_kas,
            persentase_warga_aktif=persentase_warga_aktif,
            persentase_iuran_bulan_ini=persentase_iuran_bulan_ini,
            persentase_pengeluaran_bulan_ini=persentase_pengeluaran_bulan_ini,
            aktivitas_terkini=aktivitas_terkini
        )

    elif role == 'petugas':
        total_iuran_reguler = db.session.query(func.sum(Iuran.jumlah)).scalar() or 0
        total_iuran_event = db.session.query(func.sum(IuranEvent.jumlah)).scalar() or 0
        total_iuran = total_iuran_reguler + total_iuran_event
        total_pengeluaran = db.session.query(func.sum(Pengeluaran.jumlah)).scalar() or 0
        sisa_kas = total_iuran - total_pengeluaran
        warga = Warga.query.filter_by(telepon=session['telepon']).first()
        aktivitas_terkini = get_aktivitas_terkini()

        from collections import defaultdict
        mingguan_iuran = defaultdict(int)
        mingguan_pengeluaran = defaultdict(int)

        iurans = Iuran.query.filter(
            extract('month', Iuran.tanggal) == bulan_ini,
            extract('year', Iuran.tanggal) == tahun_ini
        ).all()

        pengeluarans = Pengeluaran.query.filter(
            extract('month', Pengeluaran.tanggal) == bulan_ini,
            extract('year', Pengeluaran.tanggal) == tahun_ini
        ).all()

        for i in iurans:
            minggu = ((i.tanggal.day - 1) // 7) + 1
            mingguan_iuran[minggu] += i.jumlah

        for p in pengeluarans:
            minggu = ((p.tanggal.day - 1) // 7) + 1
            mingguan_pengeluaran[minggu] += p.jumlah

        labels = [f"Minggu {i}" for i in range(1, 6)]
        data_iuran = [mingguan_iuran[i] for i in range(1, 6)]
        data_pengeluaran = [mingguan_pengeluaran[i] for i in range(1, 6)]

        return render_template('dashboard_petugas.html',
            nama=warga.nama,
            total_iuran=total_iuran,
            total_pengeluaran=total_pengeluaran,
            sisa_kas=sisa_kas,
            aktivitas_terkini=aktivitas_terkini,
            labels=labels,
            data_iuran=data_iuran,
            data_pengeluaran=data_pengeluaran
        )

    elif role == 'user':
        if 'telepon' not in session:
            flash("Sesi login tidak ditemukan", "danger")
            return redirect(url_for('logout'))

        warga = Warga.query.filter_by(telepon=session['telepon']).first()
        if not warga:
            flash("Data warga tidak ditemukan", "danger")
            return redirect(url_for('logout'))

        iuran_user = db.session.query(func.sum(Iuran.jumlah)).filter_by(warga_id=warga.id).scalar() or 0
        iuran_event_user = db.session.query(func.sum(IuranEvent.jumlah)).filter_by(warga_id=warga.id).scalar() or 0
        total_iuran_user = iuran_user + iuran_event_user

        total_iuran_reguler = db.session.query(func.sum(Iuran.jumlah)).scalar() or 0
        total_iuran_event = db.session.query(func.sum(IuranEvent.jumlah)).scalar() or 0
        total_iuran = total_iuran_reguler + total_iuran_event
        total_pengeluaran = db.session.query(func.sum(Pengeluaran.jumlah)).scalar() or 0
        sisa_kas = total_iuran - total_pengeluaran

        aktivitas_terkini = get_aktivitas_terkini()

        from collections import defaultdict
        mingguan_iuran = defaultdict(int)
        mingguan_pengeluaran = defaultdict(int)

        iurans = Iuran.query.filter(
            extract('month', Iuran.tanggal) == bulan_ini,
            extract('year', Iuran.tanggal) == tahun_ini
        ).all()

        pengeluarans = Pengeluaran.query.filter(
            extract('month', Pengeluaran.tanggal) == bulan_ini,
            extract('year', Pengeluaran.tanggal) == tahun_ini
        ).all()

        for i in iurans:
            minggu = ((i.tanggal.day - 1) // 7) + 1
            mingguan_iuran[minggu] += i.jumlah

        for p in pengeluarans:
            minggu = ((p.tanggal.day - 1) // 7) + 1
            mingguan_pengeluaran[minggu] += p.jumlah

        labels = [f"Minggu {i}" for i in range(1, 6)]
        data_iuran = [mingguan_iuran[i] for i in range(1, 6)]
        data_pengeluaran = [mingguan_pengeluaran[i] for i in range(1, 6)]

        return render_template('dashboard_user.html',
            nama=warga.nama,
            total_iuran=total_iuran,
            total_pengeluaran=total_pengeluaran,
            sisa_kas=sisa_kas,
            aktivitas_terkini=aktivitas_terkini,
            labels=labels,
            data_iuran=data_iuran,
            data_pengeluaran=data_pengeluaran
        )

    else:
        flash("Peran tidak dikenali", "danger")
        return redirect(url_for('logout'))


@app.route('/input_iuran_petugas', methods=['GET', 'POST'])
def input_iuran_petugas():
    if 'telepon' not in session or session.get('role') not in ['petugas', 'admin']:
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form['nama'].strip()
        try:
            total_bayar = int(request.form['total_bayar'])
            jumlah_minggu = int(request.form['jumlah_minggu'])
        except ValueError:
            flash("Input tidak valid", "danger")
            return redirect(url_for('input_iuran_petugas'))

        if total_bayar < 2000 or jumlah_minggu < 1:
            flash("Minimal iuran total Rp 2.000 dan jumlah minggu minimal 1", "danger")
            return redirect(url_for('input_iuran_petugas'))

        per_minggu = total_bayar // jumlah_minggu

        if per_minggu < 2000:
            flash(f"Iuran per minggu Rp {per_minggu:,} terlalu kecil. Minimal Rp 2.000", "danger")
            return redirect(url_for('input_iuran_petugas'))

        if per_minggu > 5000:
            min_minggu = (total_bayar + 4999) // 5000
            flash(f"Iuran per minggu Rp {per_minggu:,} melebihi Rp 5.000. Gunakan minimal {min_minggu} minggu", "danger")
            return redirect(url_for('input_iuran_petugas'))

        warga = Warga.query.filter_by(nama=nama).first()
        if not warga:
            flash(f"Warga dengan nama '{nama}' tidak ditemukan", 'danger')
            return redirect(url_for('input_iuran_petugas'))

        zona_wib = timezone('Asia/Jakarta')
        minggu_bentrok = []

        for i in range(jumlah_minggu):
            tanggal = datetime.now(zona_wib) + timedelta(weeks=i)
            tahun = tanggal.year
            bulan = tanggal.month
            minggu_ke = ((tanggal.day - 1) // 7) + 1

            # Ambil semua iuran bulan itu
            iurans_bulan = Iuran.query.filter(
                Iuran.warga_id == warga.id,
                extract('year', Iuran.tanggal) == tahun,
                extract('month', Iuran.tanggal) == bulan
            ).all()

            # Cek bentrok
            sudah_bayar = any(
                ((i.tanggal.day - 1) // 7 + 1) == minggu_ke for i in iurans_bulan
            )

            if sudah_bayar:
                minggu_bentrok.append(f"Minggu ke-{minggu_ke} ({tanggal.strftime('%d/%m')})")

        if minggu_bentrok:
            flash(f"❌ Pembayaran ditolak! Warga sudah bayar di: {', '.join(minggu_bentrok)}", "danger")
            return redirect(url_for('input_iuran_petugas'))

        # ✅ Simpan iuran untuk minggu-minggu valid
        for i in range(jumlah_minggu):
            tanggal = datetime.now(zona_wib) + timedelta(weeks=i)
            iuran = Iuran(
                warga_id=warga.id,
                jumlah=per_minggu,
                tanggal=tanggal,
                petugas=session['telepon']
            )
            db.session.add(iuran)

        db.session.commit()
        flash("✅ Iuran berhasil dicatat", "success")
        return redirect(url_for('input_iuran_petugas'))

    return render_template('input_iuran_petugas.html')


@app.route('/daftar_iuran')
def daftar_iuran():
    iurans = Iuran.query.order_by(Iuran.tanggal.desc()).all()

    # Buat mapping nomor telepon => nama
    telepon_to_nama = {w.telepon: w.nama for w in Warga.query.all()}

    return render_template('daftar_iuran.html', iurans=iurans, telepon_to_nama=telepon_to_nama)


@app.route('/iuran/edit/<int:id>', methods=['GET', 'POST'])
def edit_iuran(id):
    if 'telepon' not in session or session.get('role') not in ['admin', 'petugas']:
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    iuran = Iuran.query.get_or_404(id)

    if request.method == 'POST':
        try:
            iuran.jumlah = int(request.form['jumlah'])
            tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d')
            iuran.tanggal = timezone('Asia/Jakarta').localize(datetime.combine(tanggal, datetime.now().time()))
            db.session.commit()
            flash("Data iuran berhasil diperbarui", "success")
            return redirect(url_for('daftar_iuran'))
        except Exception as e:
            flash(f"Gagal mengupdate: {str(e)}", "danger")

    return render_template('edit_iuran.html', iuran=iuran)

@app.route('/iuran/hapus/<int:id>', methods=['POST'])
def hapus_iuran(id):


    iuran = Iuran.query.get_or_404(id)
    try:
        db.session.delete(iuran)
        db.session.commit()
        flash("Data iuran berhasil dihapus", "success")
    except Exception as e:
        flash(f"Gagal menghapus: {str(e)}", "danger")
    return redirect(url_for('daftar_iuran'))



@app.route('/autocomplete-nama')
def autocomplete_nama():
    query = request.args.get('q', '')
    if query:
        hasil = Warga.query.filter(Warga.nama.ilike(f'%{query}%')).all()
        nama_list = [warga.nama for warga in hasil]
    else:
        nama_list = []
    return jsonify(nama_list)


@app.route('/laporan')
def laporan():
    bulan = request.args.get('bulan', type=int, default=datetime.now().month)
    tahun = request.args.get('tahun', type=int, default=datetime.now().year)

    zona_wib = timezone('Asia/Jakarta')

    tgl_awal = datetime(tahun, bulan, 1, tzinfo=zona_wib)
    if bulan == 12:
        tgl_akhir = datetime(tahun + 1, 1, 1, tzinfo=zona_wib) - timedelta(seconds=1)
    else:
        tgl_akhir = datetime(tahun, bulan + 1, 1, tzinfo=zona_wib) - timedelta(seconds=1)

    # Ambil data pemasukan
    pemasukan_iuran = (
        db.session.query(Iuran)
        .join(Warga)
        .filter(Iuran.tanggal >= tgl_awal, Iuran.tanggal <= tgl_akhir)
        .all()
    )
    pemasukan_event = (
        db.session.query(IuranEvent)
        .join(Warga)
        .filter(IuranEvent.tanggal >= tgl_awal, IuranEvent.tanggal <= tgl_akhir)
        .all()
    )
    pemasukan = pemasukan_iuran + pemasukan_event
    pemasukan.sort(key=lambda x: x.tanggal)

    # Tambahkan nama petugas (jika ada) sebagai properti dinamis
    def get_nama_petugas(nomor_wa):
        if not nomor_wa:
            return '-'
        petugas = Warga.query.filter_by(telepon=nomor_wa).first()
        return petugas.nama if petugas else nomor_wa

    for item in pemasukan:
        item.petugas_nama = get_nama_petugas(item.petugas)

    # Ambil data pengeluaran
    pengeluaran = (
        db.session.query(Pengeluaran)
        .filter(Pengeluaran.tanggal >= tgl_awal, Pengeluaran.tanggal <= tgl_akhir)
        .all()
    )

    # Tambahkan field penerima
    for item in pengeluaran:
        item.penerima = get_nama_petugas(item.petugas)

    # Total
    total_pemasukan = sum(i.jumlah for i in pemasukan)
    total_pengeluaran = sum(p.jumlah for p in pengeluaran)
    saldo_kas = total_pemasukan - total_pengeluaran

    # Total iuran tahun ini
    awal_tahun = datetime(tahun, 1, 1, tzinfo=zona_wib)
    akhir_tahun = datetime(tahun + 1, 1, 1, tzinfo=zona_wib) - timedelta(seconds=1)

    total_iuran_tahun_ini = (
        db.session.query(func.sum(Iuran.jumlah))
        .filter(Iuran.tanggal >= awal_tahun, Iuran.tanggal <= akhir_tahun)
        .scalar()
    ) or 0

    # Grafik data mingguan
    from collections import defaultdict
    pemasukan_data = defaultdict(int)
    pengeluaran_data = defaultdict(int)

    for i in pemasukan:
        minggu = ((i.tanggal.day - 1) // 7) + 1
        pemasukan_data[minggu] += i.jumlah

    for p in pengeluaran:
        minggu = ((p.tanggal.day - 1) // 7) + 1
        pengeluaran_data[minggu] += p.jumlah

    labels = [f"Minggu {i}" for i in range(1, 6)]
    data_pemasukan = [pemasukan_data[i] for i in range(1, 6)]
    data_pengeluaran = [pengeluaran_data[i] for i in range(1, 6)]

    return render_template('laporan.html',
        pemasukan=pemasukan,
        pengeluaran=pengeluaran,
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        saldo_kas=saldo_kas,
        total_iuran_tahun_ini=total_iuran_tahun_ini,
        bulan=bulan,
        tahun=tahun,
        labels=labels,
        pemasukan_data=data_pemasukan,
        pengeluaran_data=data_pengeluaran
    )






@app.route('/laporan_iuran_perminggu')
def laporan_iuran_perminggu():
    bulan = request.args.get('bulan', type=int, default=datetime.now().month)
    tahun = request.args.get('tahun', type=int, default=datetime.now().year)

    iurans = Iuran.query.join(Warga).filter(
        extract('month', Iuran.tanggal) == bulan,
        extract('year', Iuran.tanggal) == tahun
    ).order_by(Iuran.tanggal).all()

    from collections import defaultdict
    data = defaultdict(lambda: defaultdict(int))

    for iuran in iurans:
        if iuran.warga:  # Hindari error jika relasi kosong
            minggu_ke = ((iuran.tanggal.day - 1) // 7) + 1
            data[iuran.warga.nama][minggu_ke] += iuran.jumlah

    minggu_labels = ['Minggu 1', 'Minggu 2', 'Minggu 3', 'Minggu 4', 'Minggu 5']

    return render_template("laporan_iuran_perminggu.html",  # pastikan ini sesuai nama file HTML
        data=data,
        bulan=bulan,
        tahun=tahun,
        minggu_labels=minggu_labels,
        datetime=datetime
    )


@app.route('/laporan_input_petugas')
def laporan_input_petugas():
    bulan = request.args.get('bulan', default=date.today().month, type=int)
    tahun = request.args.get('tahun', default=date.today().year, type=int)

    # Awal dan akhir bulan
    awal_bulan = date(tahun, bulan, 1)
    akhir_bulan = date(tahun, bulan, calendar.monthrange(tahun, bulan)[1])

    # Ambil iuran dalam rentang waktu tersebut
    iurans = Iuran.query.filter(Iuran.tanggal.between(awal_bulan, akhir_bulan)).all()

    # Ambil semua warga sebagai referensi nomor → nama
    warga_map = {w.telepon: w.nama for w in Warga.query.all()}

    from collections import defaultdict
    data = defaultdict(lambda: defaultdict(int))  # {petugas_nama: {minggu_ke: total}}

    for iuran in iurans:
        telepon_petugas = iuran.petugas or 'Tidak Diketahui'
        nama_petugas = warga_map.get(telepon_petugas, telepon_petugas)

        minggu_ke = ((iuran.tanggal.day - 1) // 7) + 1
        data[nama_petugas][minggu_ke] += iuran.jumlah

    minggu_labels = [f"Minggu {i}" for i in range(1, 6)]

    return render_template("laporan_input_petugas.html",
        data=data,
        minggu_labels=minggu_labels,
        bulan=bulan,
        tahun=tahun,
        datetime=datetime
    )






@app.route('/data_warga', methods=['GET', 'POST'])
def data_warga():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form['nama'].strip()
        nik = request.form['nik'].strip()
        alamat = request.form['alamat'].strip()
        telepon = request.form['telepon'].strip()
        password = request.form['password']
        role = request.form['role']
        status = request.form.get('status', 'aktif')

        if not nama or not telepon or not password:
            flash("Nama, Telepon, dan Password wajib diisi", "danger")
            return redirect(url_for('data_warga'))

        if Warga.query.filter_by(telepon=telepon).first():
            flash("Nomor telepon sudah digunakan", "danger")
            return redirect(url_for('data_warga'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        warga_baru = Warga(
            nama=nama,
            nik=nik if nik else None,
            alamat=alamat,
            telepon=telepon,
            password=hashed_pw,
            role=role,
            status=status
        )
        db.session.add(warga_baru)
        db.session.commit()

        flash("✅ Warga berhasil ditambahkan", "success")
        return redirect(url_for('data_warga'))

    # === Bagian GET: tampilkan warga dengan pagination dan search ===
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)

    query = Warga.query
    if search:
        query = query.filter(
            Warga.nama.ilike(f'%{search}%') |
            Warga.telepon.ilike(f'%{search}%')
        )

    wargas = query.order_by(Warga.nama.asc()).paginate(page=page, per_page=10)

    return render_template("warga.html", wargas=wargas, search=search)



@app.route('/tambah_warga', methods=['POST'])
def tambah_warga():
    nama = request.form['nama']
    nik = request.form['nik']
    alamat = request.form['alamat']
    telepon = request.form['telepon']
    status = request.form['status']
    username = request.form['username']
    raw_password = request.form['password']

    # Hash password sebelum disimpan
    hashed_pw = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    # Cek jika username sudah digunakan
    existing = Warga.query.filter_by(username=username).first()
    if existing:
        flash('Username sudah digunakan, silakan pilih yang lain', 'danger')
        return redirect(url_for('data_warga'))

    warga = Warga(
        nama=nama,
        nik=nik,
        alamat=alamat,
        telepon=telepon,
        status=status,
        username=username,
        password=hashed_pw,
        role='user'
    )
    db.session.add(warga)
    db.session.commit()

    flash("Warga berhasil ditambahkan", "success")
    return redirect(url_for('data_warga'))



@app.route('/warga/edit/<int:id>', methods=['GET', 'POST'])
def edit_warga(id):
    warga = Warga.query.get_or_404(id)

    if request.method == 'POST':
        warga.nama = request.form['nama']
        nik = request.form.get('nik', '').strip()
        nik = nik if nik else None

        if nik and nik != warga.nik and Warga.query.filter_by(nik=nik).first():
            flash('NIK sudah terdaftar', 'danger')
            return redirect(url_for('edit_warga', id=id))

        warga.nik = nik
        warga.alamat = request.form['alamat']
        warga.telepon = request.form.get('telepon', '').strip()
       ## warga.username = request.form['username']
        warga.role = request.form['role']  # hanya role, status dihapus

        if request.form['password']:
            warga.password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        db.session.commit()
        flash('Data warga berhasil diperbarui', 'success')
        return redirect(url_for('data_warga'))

    return render_template('edit_warga.html', warga=warga)


@app.route('/warga/hapus/<int:id>', methods=['POST'])
def hapus_warga(id):
    warga = Warga.query.get_or_404(id)

    # Hapus semua iuran yang terkait terlebih dahulu
    Iuran.query.filter_by(warga_id=warga.id).delete()
    IuranEvent.query.filter_by(warga_id=warga.id).delete()  # jika kamu juga pakai IuranEvent

    db.session.delete(warga)
    db.session.commit()

    flash('Data warga berhasil dihapus.', 'success')
    return redirect(url_for('data_warga'))

@app.route('/search_warga')
def search_warga():
    q = request.args.get('q', '').strip().lower()
    results = []

    if q:
        wargas = Warga.query.filter(Warga.nama.ilike(f'%{q}%')).limit(10).all()
        results = [{'id': w.id, 'nama': w.nama, 'telepon': w.telepon} for w in wargas]

    return jsonify(results)



@app.route('/export_warga')
def export_warga():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    warga_data = Warga.query.order_by(Warga.nama).all()

    data = [{
        'Nama': w.nama,
        'NIK': w.nik or '',
        'Alamat': w.alamat or '',
        'Telepon': w.telepon or '',
        'Status': w.status or '',
        'Peran': w.role or ''
    } for w in warga_data]

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Warga')

    output.seek(0)
    return send_file(
        output,
        download_name="data_warga.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




# TAMBAH PENGELUARAN
@app.route('/pengeluaran/tambah', methods=['GET', 'POST'])
def tambah_pengeluaran():
    if 'telepon' not in session:
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            zona_wib = timezone('Asia/Jakarta')
            tanggal_str = request.form['tanggal']
            jam_sekarang = datetime.now(zona_wib).time()
            tanggal_obj = datetime.strptime(tanggal_str, '%Y-%m-%d')
            tanggal_full = datetime.combine(tanggal_obj, jam_sekarang)
            tanggal_full = zona_wib.localize(tanggal_full)

            keterangan = request.form['keterangan'].strip()
            penerima = request.form['penerima'].strip()
            jumlah = int(request.form['jumlah'])
            petugas = session.get('telepon')  # no telepon

            if not keterangan or not penerima:
                flash('Semua field wajib diisi.', 'danger')
                return redirect(url_for('tambah_pengeluaran'))

            if jumlah < 1000:
                flash('Jumlah minimal Rp 1.000', 'danger')
                return redirect(url_for('tambah_pengeluaran'))

            baru = Pengeluaran(
                tanggal=tanggal_full,
                keterangan=keterangan,
                penerima=penerima,
                jumlah=jumlah,
                petugas=petugas
            )
            db.session.add(baru)
            db.session.commit()

            flash('✅ Pengeluaran berhasil dicatat', 'success')
            return redirect(url_for('daftar_pengeluaran'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('tambah_pengeluaran.html', date=datetime.now(timezone('Asia/Jakarta')))


@app.route('/pengeluaran')
def daftar_pengeluaran():
    bulan = request.args.get('bulan', type=int)
    tahun = request.args.get('tahun', type=int)

    query = Pengeluaran.query

    if bulan:
        query = query.filter(db.extract('month', Pengeluaran.tanggal) == bulan)
    if tahun:
        query = query.filter(db.extract('year', Pengeluaran.tanggal) == tahun)

    pengeluaran_list = query.order_by(Pengeluaran.tanggal.desc()).all()

    # Buat mapping nomor telepon ke nama petugas dari tabel Warga
    petugas_dict = {w.telepon: w.nama for w in Warga.query.all()}

    # Sisipkan nama petugas ke setiap item pengeluaran
    for p in pengeluaran_list:
        p.nama_petugas = petugas_dict.get(p.petugas, "-")

    total = sum(p.jumlah for p in pengeluaran_list)

    return render_template(
        'daftar_pengeluaran.html',
        pengeluaran=pengeluaran_list,
        total=total,
        bulan=bulan,
        tahun=tahun
    )



@app.route('/pengeluaran/edit/<int:id>', methods=['GET', 'POST'])
def edit_pengeluaran(id):
    pengeluaran = Pengeluaran.query.get_or_404(id)

    if request.method == 'POST':
        try:
            zona_wib = timezone('Asia/Jakarta')
            tanggal_str = request.form['tanggal']
            tanggal_obj = datetime.strptime(tanggal_str, '%Y-%m-%d')
            jam_sekarang = datetime.now(zona_wib).time()
            tanggal_full = zona_wib.localize(datetime.combine(tanggal_obj, jam_sekarang))

            keterangan = request.form['keterangan'].strip()
            penerima = request.form['penerima'].strip()
            jumlah = int(request.form['jumlah'])

            if not keterangan or not penerima:
                flash('Keterangan dan Penerima tidak boleh kosong', 'danger')
                return redirect(url_for('edit_pengeluaran', id=id))

            if jumlah < 1000:
                flash('Jumlah pengeluaran minimal Rp 1.000', 'danger')
                return redirect(url_for('edit_pengeluaran', id=id))

            pengeluaran.tanggal = tanggal_full
            pengeluaran.keterangan = keterangan
            pengeluaran.penerima = penerima
            pengeluaran.jumlah = jumlah

            db.session.commit()
            flash('✅ Data pengeluaran berhasil diperbarui.', 'success')
            return redirect(url_for('daftar_pengeluaran'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Terjadi kesalahan: {str(e)}', 'danger')

    return render_template('edit_pengeluaran.html', pengeluaran=pengeluaran)



@app.route('/pengeluaran/hapus/<int:id>', methods=['POST'])
def hapus_pengeluaran(id):
    try:
        pengeluaran = Pengeluaran.query.get_or_404(id)
        db.session.delete(pengeluaran)
        db.session.commit()
        flash('Data pengeluaran berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus pengeluaran: {str(e)}', 'danger')
    return redirect(url_for('daftar_pengeluaran'))



@app.route('/pengeluaran/export')
def export_pengeluaran():
    bulan = request.args.get('bulan', type=int)
    tahun = request.args.get('tahun', type=int)

    query = Pengeluaran.query

    if bulan:
        query = query.filter(db.extract('month', Pengeluaran.tanggal) == bulan)
    if tahun:
        query = query.filter(db.extract('year', Pengeluaran.tanggal) == tahun)

    pengeluaran = query.order_by(Pengeluaran.tanggal).all()

    # Ambil semua telepon petugas yang muncul
    nomor_petugas = [p.petugas for p in pengeluaran if p.petugas]
    petugas_dict = {w.telepon: w.nama for w in Warga.query.filter(Warga.telepon.in_(nomor_petugas)).all()}

    data = [{
        'Tanggal': p.tanggal.strftime('%d/%m/%Y'),
        'Keterangan': p.keterangan,
        'Penerima': p.penerima,
        'Petugas': petugas_dict.get(p.petugas, '') if p.petugas else '',
        'Jumlah': p.jumlah
    } for p in pengeluaran]

    df = pd.DataFrame(data)
    total_pengeluaran = sum(p.jumlah for p in pengeluaran)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pengeluaran', startrow=0)

        # Tambahkan total
        workbook = writer.book
        worksheet = writer.sheets['Pengeluaran']
        row_count = len(df) + 2
        worksheet.write(row_count, 3, 'Total', workbook.add_format({'bold': True}))
        worksheet.write(row_count, 4, total_pengeluaran, workbook.add_format({'bold': True, 'num_format': '#,##0'}))

    output.seek(0)
    return send_file(
        output,
        download_name='pengeluaran.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




@app.route('/import_warga', methods=['POST'])
def import_warga():
    file = request.files.get('file')
    if not file:
        flash('File tidak ditemukan.', 'danger')
        return redirect(url_for('data_warga'))

    if not file.filename.endswith('.csv'):
        flash('Format file harus .csv', 'danger')
        return redirect(url_for('data_warga'))

    file_data = file.read().decode('utf-8')
    csv_reader = csv.reader(file_data.splitlines())

    baris_sukses = 0
    baris_duplikat = 0
    baris_skip = 0

    for idx, row in enumerate(csv_reader):
        if idx == 0:
            continue  # Lewati header

        if len(row) != 7:
            baris_skip += 1
            continue

        nama, nik, alamat, telepon, status, role, plain_pw = [x.strip() for x in row]

        if not nama or not telepon or not plain_pw:
            baris_skip += 1
            continue

        # Cek duplikat nomor telepon
        if Warga.query.filter_by(telepon=telepon).first():
            baris_duplikat += 1
            continue

        hashed_pw = bcrypt.generate_password_hash(plain_pw).decode('utf-8')

        warga_baru = Warga(
            nama=nama,
            nik=nik or None,
            alamat=alamat,
            telepon=telepon,
            status=status.lower() if status.lower() in ['aktif', 'nonaktif'] else 'aktif',
            username=telepon,
            password=hashed_pw,
            role=role.lower() if role.lower() in ['user', 'petugas'] else 'user'
        )
        db.session.add(warga_baru)
        baris_sukses += 1

    db.session.commit()
    flash(f'{baris_sukses} warga berhasil diimpor. {baris_duplikat} nomor telepon sudah digunakan. {baris_skip} baris dilewati.', 'success')
    return redirect(url_for('data_warga'))



class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Laporan duitRT", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Halaman {self.page_no()}", align="C")

    def table_section(self, title, headers, rows):
        self.set_font("Arial", "B", 11)
        self.cell(0, 8, title, ln=True)
        self.set_font("Arial", "B", 10)
        for h in headers:
            self.cell(40, 8, h, border=1)
        self.ln()
        self.set_font("Arial", "", 10)
        for row in rows:
            for item in row:
                self.cell(40, 8, str(item), border=1)
            self.ln()
        self.ln(5)

def get_filter_dates():
    # Ganti dengan cara ambil tgl_awal dan tgl_akhir dari parameter / session sesuai kebutuhan
    today = datetime.now(timezone('Asia/Jakarta'))
    tgl_awal = today.replace(day=1)
    tgl_akhir = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    return tgl_awal, tgl_akhir

@app.route('/export_laporan/<format>')
def export_laporan(format):
    tgl_awal, tgl_akhir = get_filter_dates()
    zona_wib = timezone('Asia/Jakarta')

    # Ambil mapping nomor telepon ke nama petugas
    warga_map = {
        w.telepon: w.nama
        for w in Warga.query.with_entities(Warga.telepon, Warga.nama).all()
    }

    pemasukan_iuran = (
        db.session.query(Iuran)
        .join(Warga)
        .filter(Iuran.tanggal.between(tgl_awal, tgl_akhir))
        .all()
    )

    pemasukan_event = (
        db.session.query(IuranEvent)
        .join(Warga)
        .filter(IuranEvent.tanggal.between(tgl_awal, tgl_akhir))
        .all()
    )

    pemasukan = pemasukan_iuran + pemasukan_event
    pemasukan.sort(key=lambda x: x.tanggal)

    pengeluaran = (
        db.session.query(Pengeluaran)
        .filter(Pengeluaran.tanggal.between(tgl_awal, tgl_akhir))
        .order_by(Pengeluaran.tanggal.asc())
        .all()
    )

    headers1 = ['No', 'Tanggal', 'Nama Warga', 'Jumlah', 'Keterangan', 'Petugas']
    headers2 = ['No', 'Tanggal', 'Keterangan', 'Jumlah', 'Petugas']

    if format == 'excel':
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        ws1 = workbook.add_worksheet('Pemasukan')
        for col, h in enumerate(headers1):
            ws1.write(0, col, h)

        for idx, item in enumerate(pemasukan, 1):
            tanggal = item.tanggal.astimezone(zona_wib).strftime('%d/%m/%Y %H:%M')
            nama_petugas = warga_map.get(item.petugas, item.petugas or "-")
            sumber = f"Event: {item.nama_event}" if item.__class__.__name__ == "IuranEvent" else "Iuran Bulanan"

            ws1.write(idx, 0, idx)
            ws1.write(idx, 1, tanggal)
            ws1.write(idx, 2, item.warga.nama)
            ws1.write(idx, 3, item.jumlah)
            ws1.write(idx, 4, sumber)
            ws1.write(idx, 5, nama_petugas)

        ws2 = workbook.add_worksheet('Pengeluaran')
        for col, h in enumerate(headers2):
            ws2.write(0, col, h)

        for idx, item in enumerate(pengeluaran, 1):
            tanggal = item.tanggal.astimezone(zona_wib).strftime('%d/%m/%Y %H:%M')
            nama_petugas = warga_map.get(item.petugas, item.petugas or "-")

            ws2.write(idx, 0, idx)
            ws2.write(idx, 1, tanggal)
            ws2.write(idx, 2, item.keterangan)
            ws2.write(idx, 3, item.jumlah)
            ws2.write(idx, 4, nama_petugas)

        workbook.close()
        output.seek(0)
        filename = f"laporan_kas_{tgl_awal.strftime('%Y%m%d')}_{tgl_akhir.strftime('%Y%m%d')}.xlsx"
        return send_file(output, download_name=filename, as_attachment=True)

    elif format == 'pdf':
        pdf = PDF()
        pdf.add_page()

        pemasukan_rows = []
        for idx, i in enumerate(pemasukan, 1):
            tanggal = i.tanggal.astimezone(zona_wib).strftime('%d/%m/%Y %H:%M')
            nama_petugas = warga_map.get(i.petugas, i.petugas or "-")
            pemasukan_rows.append([
                idx,
                tanggal,
                i.warga.nama,
                f"Rp {i.jumlah:,}",
                f"Event: {i.nama_event}" if i.__class__.__name__ == "IuranEvent" else "Iuran Bulanan",
                nama_petugas
            ])

        pengeluaran_rows = []
        for idx, p in enumerate(pengeluaran, 1):
            tanggal = p.tanggal.astimezone(zona_wib).strftime('%d/%m/%Y %H:%M')
            nama_petugas = warga_map.get(p.petugas, p.petugas or "-")
            pengeluaran_rows.append([
                idx,
                tanggal,
                p.keterangan,
                f"Rp {p.jumlah:,}",
                nama_petugas
            ])

        pdf.table_section("Pemasukan", headers1, pemasukan_rows)
        pdf.table_section("Pengeluaran", headers2, pengeluaran_rows)

        pdf_bytes = BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin1')
        pdf_bytes.write(pdf_output)
        pdf_bytes.seek(0)

        filename = f"laporan_kas_{tgl_awal.strftime('%Y%m%d')}_{tgl_akhir.strftime('%Y%m%d')}.pdf"
        return send_file(pdf_bytes, download_name=filename, as_attachment=True)

    return "Format tidak didukung", 400



@app.route('/download_template')
def download_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['nama', 'nik', 'alamat', 'telepon', 'status', 'role', 'password'])
    writer.writerow(['Contoh Nama', '1234567890123456', 'Jl. Contoh Alamat', '08123456789', 'aktif', 'user', '123456'])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='template_warga.csv'
    )


@app.route('/manajemen_user')
def manajemen_user():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('manajemen_user.html', users=users)

@app.route('/user/tambah', methods=['GET', 'POST'])
def tambah_user():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role']

        # ✅ Hash password!
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan', 'danger')
            return redirect(url_for('tambah_user'))

        user = User(username=username, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()
        flash('User berhasil ditambahkan', 'success')
        return redirect(url_for('manajemen_user'))

    return render_template('form_user.html')


@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.username = request.form['username'].strip()
        user.role = request.form['role']

        new_password = request.form['password'].strip()
        if new_password:
            # ✅ Hash password baru
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        db.session.commit()
        flash('User berhasil diperbarui', 'success')
        return redirect(url_for('manajemen_user'))

    return render_template('form_user.html', user=user)


@app.route('/user/hapus/<int:id>', methods=['POST'])
def hapus_user(id):
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User berhasil dihapus', 'success')
    return redirect(url_for('manajemen_user'))





@app.route('/iuran_saya')
def iuran_saya():
    if 'telepon' not in session or session.get('role') != 'user':
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    warga = Warga.query.filter_by(telepon=session['telepon']).first()
    if not warga:
        flash("Data warga tidak ditemukan", "danger")
        return redirect(url_for('logout'))

    # Ambil filter bulan dan tahun
    bulan = request.args.get('bulan', default=datetime.now().month, type=int)
    tahun = request.args.get('tahun', default=datetime.now().year, type=int)

    # Ambil iuran berdasarkan filter
    iurans = Iuran.query.filter(
        Iuran.warga_id == warga.id,
        extract('month', Iuran.tanggal) == bulan,
        extract('year', Iuran.tanggal) == tahun
    ).order_by(Iuran.tanggal.desc()).all()

    total = sum(i.jumlah for i in iurans)

    # Mapping petugas (telepon) ke nama
    warga_list = Warga.query.all()
    wargas_dict = {w.telepon: w.nama for w in warga_list}

    return render_template("iuran_saya.html",
        iurans=iurans,
        total=total,
        bulan=bulan,
        tahun=tahun,
        datetime=datetime,
        wargas_dict=wargas_dict
    )


@app.route('/input_iuran_event_petugas', methods=['GET', 'POST'])
def input_iuran_event_petugas():
    if 'telepon' not in session or session['role'] not in ['admin', 'petugas']:
        flash("Akses ditolak", "danger")
        return redirect(url_for('login'))

    from pytz import timezone
    zona_wib = timezone('Asia/Jakarta')

    if request.method == 'POST':
        nama = request.form['nama'].strip()
        nama_event = request.form['nama_event'].strip()
        jumlah = request.form['jumlah']

        warga = Warga.query.filter_by(nama=nama).first()
        if not warga:
            flash("❌ Warga tidak ditemukan", "danger")
            return redirect(url_for('input_iuran_event_petugas'))

        # Simpan ke database
        iuran = IuranEvent(
            warga_id=warga.id,
            nama_event=nama_event,
            jumlah=int(jumlah),
            petugas=session['telepon'],
            tanggal=datetime.now(zona_wib)
        )
        db.session.add(iuran)
        db.session.commit()
        flash("✅ Iuran Event berhasil dicatat", "success")
        return redirect(url_for('input_iuran_event_petugas'))

    # Data event dan riwayat untuk form dan tabel
    daftar_event = EventNama.query.order_by(EventNama.nama).all()
    data = IuranEvent.query.order_by(IuranEvent.tanggal.desc()).limit(20).all()
    return render_template('input_iuran_event_petugas.html', daftar_event=daftar_event, data=data)



@app.route('/manajemen_event', methods=['GET', 'POST'])
def manajemen_event():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nama_event = request.form['nama'].strip()
        if EventNama.query.filter_by(nama=nama_event).first():
            flash("Nama event sudah ada", "warning")
        else:
            db.session.add(EventNama(nama=nama_event))
            db.session.commit()
            flash("Event berhasil ditambahkan", "success")
        return redirect(url_for('manajemen_event'))

    events = EventNama.query.order_by(EventNama.nama).all()
    return render_template('manajemen_event.html', events=events)


@app.route('/event/hapus/<int:id>', methods=['POST'])
def hapus_event(id):
    if 'username' not in session or session.get('role') != 'admin':
        flash("Akses ditolak", "danger")
        return redirect(url_for('dashboard'))

    event = EventNama.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash("Event berhasil dihapus", "success")
    return redirect(url_for('manajemen_event'))


@app.route('/laporan_iuran_event')
def laporan_iuran_event():
    bulan = request.args.get('bulan', default=date.today().month, type=int)
    tahun = request.args.get('tahun', default=date.today().year, type=int)

    start_date = date(tahun, bulan, 1)
    end_date = date(tahun, bulan, calendar.monthrange(tahun, bulan)[1])

    # Ambil data iuran event bulan ini
    iuran_event = IuranEvent.query.filter(
        IuranEvent.tanggal.between(start_date, end_date)
    ).order_by(IuranEvent.tanggal.asc()).all()

    total = sum(i.jumlah for i in iuran_event)

    # Ambil mapping telepon → nama
    warga_map = {w.telepon: w.nama for w in Warga.query.all()}

    # Ubah field petugas menjadi nama (jika cocok)
    for i in iuran_event:
        if i.petugas in warga_map:
            i.petugas = warga_map[i.petugas]

    daftar_event = db.session.query(IuranEvent.nama_event)\
        .distinct().order_by(IuranEvent.nama_event).all()
    
    return render_template('laporan_iuran_event.html',
        iuran_event=iuran_event,
        total=total,
        bulan=bulan,
        tahun=tahun,
        daftar_event=daftar_event,
        datetime=datetime
    )

@app.route('/iuran_event/edit/<int:id>', methods=['GET', 'POST'])
def edit_iuran_event(id):
    iuran = IuranEvent.query.get_or_404(id)

    daftar_event = db.session.query(IuranEvent.nama_event).distinct().order_by(IuranEvent.nama_event).all()
    event_list = [e.nama_event for e in daftar_event]

    if request.method == 'POST':
        iuran.jumlah = int(request.form['jumlah'])
        iuran.nama_event = request.form['nama_event']
        iuran.tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d')
        db.session.commit()
        flash('Iuran Event berhasil diperbarui', 'success')
        return redirect(url_for('laporan_iuran_event'))

    return render_template('edit_iuran_event.html', iuran=iuran, daftar_event=event_list)


@app.route('/iuran_event/hapus/<int:id>', methods=['POST'])
def hapus_iuran_event(id):
    iuran = IuranEvent.query.get_or_404(id)
    db.session.delete(iuran)
    db.session.commit()
    flash('Iuran Event berhasil dihapus', 'success')
    return redirect(url_for('laporan_iuran_event'))


@app.route('/laporan_iuran_event_per_warga')
def laporan_iuran_event_per_warga():
    bulan = request.args.get('bulan', default=date.today().month, type=int)
    tahun = request.args.get('tahun', default=date.today().year, type=int)

    awal_bulan = date(tahun, bulan, 1)
    akhir_bulan = date(tahun, bulan, calendar.monthrange(tahun, bulan)[1])

    iuran_event = IuranEvent.query.filter(
        IuranEvent.tanggal.between(awal_bulan, akhir_bulan)
    ).order_by(IuranEvent.tanggal.asc()).all()

    # Ambil daftar semua nomor telepon → nama petugas
    warga_dict = {w.telepon: w.nama for w in Warga.query.all()}

    return render_template('laporan_iuran_event_per_warga.html',
        iuran_event=iuran_event,
        bulan=bulan,
        tahun=tahun,
        warga_dict=warga_dict,
        datetime=datetime
    )


@app.route('/ubah_password_petugas', methods=['GET', 'POST'])
def ubah_password_petugas():
    if 'telepon' not in session or session.get('role') != 'petugas':
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('login'))

    petugas = Warga.query.filter_by(telepon=session['telepon'], role='petugas').first()
    if not petugas:
        flash('Petugas tidak ditemukan.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        password_lama = request.form.get('password_lama')
        password_baru = request.form.get('password_baru')
        konfirmasi = request.form.get('konfirmasi')

        if not bcrypt.check_password_hash(petugas.password, password_lama):
            flash('Password lama salah.', 'danger')
        elif password_baru != konfirmasi:
            flash('Konfirmasi password tidak cocok.', 'danger')
        else:
            petugas.password = bcrypt.generate_password_hash(password_baru).decode('utf-8')
            db.session.commit()
            flash('Password berhasil diubah.', 'success')
            return redirect(url_for('dashboard'))

    return render_template('ubah_password_petugas.html', nama=petugas.nama)



########################   API    ============

@app.route('/api/iuran', methods=['POST'])
def api_iuran():
    data = request.get_json()
    nama_input = data.get('nama', '').lower()
    jumlah_total = data.get('jumlah', 0)
    jumlah_minggu = data.get('minggu', 1)
    sender = data.get('petugas')

    if not sender or not nama_input or not jumlah_total or not jumlah_minggu:
        return jsonify({'message': 'Data tidak lengkap.'}), 400

    try:
        jumlah_per_minggu = jumlah_total / jumlah_minggu
    except:
        return jsonify({'message': 'Format jumlah atau minggu tidak valid.'}), 400

    # Validasi batas iuran per minggu
    if jumlah_per_minggu < 2000 or jumlah_per_minggu > 5000:
        return jsonify({
            'message': f'Iuran per minggu harus antara Rp 2000 - Rp 5000. Saat ini: Rp {jumlah_per_minggu:,.0f}'.replace(',', '.')
        }), 400

    # Validasi petugas dari data warga
    sender_normalized = sender[-10:]
    petugas = Warga.query.filter(
        Warga.role == 'petugas',
        func.replace(Warga.telepon, '-', '').endswith(sender_normalized)
    ).first()

    if not petugas:
        return jsonify({'message': 'Hanya petugas yang bisa mencatat iuran.'}), 403

    # Cari warga berdasarkan nama (case-insensitive)
    warga = Warga.query.filter(func.lower(Warga.nama).like(f"%{nama_input}%")).first()
    if not warga:
        return jsonify({'message': f'Warga dengan nama mengandung "{nama_input}" tidak ditemukan.'}), 404

    # Waktu dan tanggal target minggu ke depan
    zona_wib = timezone('Asia/Jakarta')
    today = datetime.now(zona_wib).date()
    tanggal_target = [today + timedelta(weeks=i) for i in range(jumlah_minggu)]

    # Cek apakah warga sudah membayar di minggu-minggu tersebut
    existing_iuran = Iuran.query.filter(
        Iuran.warga_id == warga.id,
        func.date(Iuran.tanggal).in_(tanggal_target)
    ).all()

    if existing_iuran:
        daftar_tanggal = [i.tanggal.strftime('%d/%m') for i in existing_iuran]
        return jsonify({
            'message': f'❌ Warga ini sudah membayar untuk tanggal: {", ".join(daftar_tanggal)}'
        }), 409

    # Simpan iuran untuk minggu ke depan
    for i in range(jumlah_minggu):
        tanggal_iuran = today + timedelta(weeks=i)
        iuran = Iuran(
            warga_id=warga.id,
            tanggal=tanggal_iuran,
            jumlah=jumlah_per_minggu,
            petugas=sender
        )
        db.session.add(iuran)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'nama_lengkap': warga.nama,
        'petugas_nama': petugas.nama
    })




@app.route('/api/hapus_iuran', methods=['POST'])
def hapus_iuran_api():
    data = request.get_json()
    nama = data.get('nama', '').strip().lower()
    minggu = int(data.get('jumlah', 1))
    sender = data.get('petugas', '').strip()

    # Validasi petugas
    petugas = Warga.query.filter(
        Warga.role == 'petugas',
        func.replace(Warga.telepon, '-', '').endswith(sender[-10:])
    ).first()

    if not petugas:
        return jsonify({'message': 'Hanya petugas yang dapat menghapus iuran.'}), 403

    # Ambil warga sesuai nama
    warga = Warga.query.filter(func.lower(Warga.nama).like(f'%{nama}%')).first()
    if not warga:
        return jsonify({'message': 'Warga tidak ditemukan'}), 404

    # Ambil iuran terakhir berdasarkan tanggal
    iuran_terakhir = Iuran.query.filter_by(warga_id=warga.id)\
        .order_by(Iuran.tanggal.desc()).limit(minggu).all()

    if not iuran_terakhir:
        return jsonify({'message': 'Tidak ada data iuran untuk dihapus'}), 404

    total_dihapus = sum(i.jumlah for i in iuran_terakhir)

    for iuran in iuran_terakhir:
        db.session.delete(iuran)
    db.session.commit()

    return jsonify({
        'message': f'Iuran sebanyak {minggu} minggu (Rp {total_dihapus}) berhasil dihapus untuk {warga.nama}',
        'nama_lengkap': warga.nama,
        'petugas_nama': petugas.nama
    }), 200


@app.route('/api/laporan_petugas_minggu_ini')
def laporan_petugas_minggu_ini():
    zona = timezone('Asia/Jakarta')
    today = datetime.now(zona).date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    # Ambil semua data iuran minggu ini
    iuran_minggu_ini = db.session.query(
        Iuran.petugas,
        Iuran.jumlah,
        Iuran.tanggal,
        Warga.nama.label('nama_warga')
    ).join(Warga, Warga.id == Iuran.warga_id).filter(
        Iuran.tanggal.between(start, end)
    ).all()

    # Petakan WA dan username berdasarkan data warga
    petugas_list = Warga.query.filter(Warga.role == 'petugas').all()
    map_wa_to_user = {}
    user_to_nama = {}

    for p in petugas_list:
        if p.telepon:
            akhir_10 = p.telepon[-10:]
            map_wa_to_user[akhir_10] = p.username
        user_to_nama[p.username] = p.nama

    hasil = {}
    for item in iuran_minggu_ini:
        petugas = item.petugas or "?"
        petugas_id = map_wa_to_user.get(petugas[-10:], petugas)  # Normalisasi

        if petugas_id not in hasil:
            hasil[petugas_id] = {
                'nama_petugas': user_to_nama.get(petugas_id, petugas_id),
                'total': 0,
                'detail': []
            }

        asal = '(via WA)' if petugas.isdigit() else '(via Web)'
        hasil[petugas_id]['total'] += item.jumlah
        hasil[petugas_id]['detail'].append({
            'nama_warga': item.nama_warga,
            'jumlah': item.jumlah,
            'tanggal': item.tanggal.strftime('%d-%m-%Y'),
            'asal': asal
        })

    return jsonify(hasil)






def get_nama_petugas_by_nomor(nomor):
    if not nomor:
        return 'Tidak diketahui'
    nomor_bersih = nomor[-10:]
    petugas = Warga.query.filter(func.replace(Warga.telepon, '-', '').endswith(nomor_bersih)).first()
    return petugas.nama if petugas else nomor




# =====================
# INISIALISASI DB
# =====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        #insert_default_users()
    app.run(host='0.0.0.0', port=8001, debug=True)

