# Mini OCR Finance

Aplikasi mini untuk mengubah foto struk menjadi data pemasukan dan pengeluaran, lalu otomatis jadi laporan bulanan.

Upload foto struk -> AI OCR baca datanya -> simpan ke database -> tampil di dashboard dan laporan bulanan.

## Fitur Utama

- Auth login dengan JWT, register dan login
- Upload struk pemasukan dan pengeluaran
- AI OCR untuk ekstrak tanggal, merchant, total, item, dan metode bayar
- Edit hasil OCR sebelum disimpan, untuk koreksi kalau AI salah baca
- Dashboard ringkasan harian dan bulanan
- Laporan bulanan per kategori, per merchant, dan per metode bayar
- Filter transaksi berdasarkan tanggal, kategori, dan tipe
- Export laporan ke CSV
- Semua jalan dengan Docker Compose

## Tech Stack

- Frontend: Streamlit
- Backend: FastAPI
- Database: PostgreSQL 16
- ORM: SQLAlchemy
- Auth: JWT + Bcrypt
- OCR: Service terpisah, bisa pakai API Vision atau Tesseract lokal
- Container: Docker dan Docker Compose

## Arsitektur

```
User -> Streamlit (Port 8501)
Streamlit -> FastAPI (Port 8000) via REST API + JWT
FastAPI -> PostgreSQL (Port 5432)
FastAPI -> OCR Service
FastAPI -> Folder uploads/ untuk simpan foto struk
```

Streamlit hanya tampilan. Semua logika hitung, auth, dan OCR ada di FastAPI.

## Prasyarat

- Docker dan Docker Compose sudah terinstall
- Git
- Koneksi internet untuk pull image dan panggil API OCR kalau pakai API

## Cara Install

```bash
git clone https://github.com/anggrdwjy/sample-project-AI-finance.git
cd mini-ocr-finance
cp .env.example .env
```

Edit file `.env` dan isi nilai yang wajib, contoh JWT_SECRET dan API key OCR kalau pakai API.

## Konfigurasi .env

Buat random password dari openssl :

```secure
root@labstack:~# openssl rand -base64 32 (32 karakter random)
Cy0TO8SytowkjmDuSH36pel7kCuqs2F5mGZIiEcUBLw=

root@labstack:~# openssl rand -base64 16 (16 karakter random)
GXQqA56XrqvQwOv99x4HxA==
```

Buat file `.env` dari contoh ini:

```env
DB_USER=ocruser
DB_PASSWORD=ubah_ini
DB_NAME=ocr_finance
JWT_SECRET=secret_acak_panjang_minimal_32_karakter
OCR_PROVIDER=api_vision
OCR_API_KEY=isi_kalau_pakai_api
```

Jangan commit file `.env` ke Git. File ini hanya untuk lokal dan server.

## Cara Menjalankan

```bash
docker compose up --build
```

Tunggu sampai semua service jalan, lalu buka:

- Frontend: http://localhost:8501
- Backend docs: http://localhost:8000/docs
- Database: localhost:5432

Untuk stop:

```bash
docker compose down
```

Untuk reset database dan hapus data:

```bash
docker compose down -v
```

## Cara Pakai

1. Buka frontend di http://localhost:8501
2. Register akun baru di halaman login
3. Login dengan email dan password
4. Buka halaman Upload, upload foto struk
5. Cek hasil OCR, edit tanggal, total, atau kategori kalau ada yang salah
6. Simpan transaksi
7. Buka Dashboard untuk lihat ringkasan
8. Buka Laporan Bulanan, pilih bulan dan tahun, lalu download CSV kalau perlu

## API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | /auth/register | Buat akun baru |
| POST | /auth/login | Login dan dapat JWT token |
| POST | /transactions/upload | Upload struk dan jalankan OCR |
| GET | /transactions | List transaksi dengan filter |
| GET | /transactions/{id} | Detail satu transaksi |
| PUT | /transactions/{id} | Edit transaksi |
| DELETE | /transactions/{id} | Hapus transaksi |
| GET | /reports/monthly?year=2026&month=11 | Rekap bulanan |
| GET | /reports/export?format=csv | Export laporan |

Semua endpoint transaksi dan laporan butuh header:

```
Authorization: Bearer <JWT_TOKEN>
```

## Struktur Folder

```text
mini-ocr-finance/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── auth.py
│       ├── routers/
│       │   ├── auth.py
│       │   ├── transactions.py
│       │   └── reports.py
│       └── services/
│           ├── ocr_service.py
│           ├── categorizer.py
│           └── report_service.py
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── pages/
│       ├── 1_Upload.py
│       ├── 2_Dashboard.py
│       └── 3_Laporan_Bulanan.py
└── uploads/
```

## Database

Tabel inti:

- users: id, email, password_hash, nama, created_at
- categories: id, nama, tipe, warna
- transactions: id, user_id, tanggal, merchant, tipe, total, metode_bayar, kategori_id, receipt_path, confidence, status
- transaction_items: id, transaction_id, nama_item, qty, harga, subtotal

Relasi: satu user punya banyak transaksi, satu transaksi punya banyak item.

## Rekomendasi OS

| OS | Cocok Untuk | Catatan |
|----|-------------|---------|
| Ubuntu 22.04 LTS atau 24.04 LTS | Server VPS dan development utama | Rekomendasi utama, Docker paling stabil |
| Windows 11 + WSL2 Ubuntu | Development di laptop Windows | Jalankan dari dalam WSL2, bukan PowerShell langsung |
| macOS 14 ke atas | Development di Mac | Cocok untuk Apple Silicon |

Hindari Windows Server untuk project ini karena Docker lebih berat dan banyak tutorial FastAPI dan PostgreSQL berasumsi Linux.

## Rekomendasi Spesifikasi

| Kebutuhan | Minimal | Rekomendasi |
|------------|---------|-------------|
| CPU | 2 Core | 4 Core |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB SSD | 50 GB SSD |
| GPU | Tidak perlu | Tidak perlu kalau OCR pakai API |
| Koneksi | Stabil untuk panggil API OCR | Stabil untuk panggil API OCR |

Kalau OCR pakai API Vision, spek minimal sudah cukup. Kalau OCR lokal pakai Tesseract atau EasyOCR, pakai spek rekomendasi dan simpan model di volume Docker supaya tidak download ulang tiap restart.

## Tips Foto Struk

- Foto lurus, tidak miring dan tidak terlipat
- Pastikan total dan tanggal terlihat jelas
- Hindari bayangan dan flash yang menutupi tulisan
- Kalau struk thermal sudah pudar, foto secepatnya sebelum makin hilang

## Troubleshooting

**Frontend tidak bisa connect ke backend**
Cek `API_URL` di docker-compose.yml untuk service frontend. Di dalam Docker harus `http://backend:8000`, bukan `localhost`.

**Database tidak jalan**
Cek port 5432 sudah dipakai aplikasi lain atau belum. Stop dulu PostgreSQL lokal kalau bentrok, atau ganti port di docker-compose.yml.

**Login gagal setelah restart**
Pastikan `JWT_SECRET` di `.env` tidak berubah. Kalau berubah, token lama jadi tidak valid dan harus login ulang.

**OCR salah baca total**
Ini normal untuk struk pudar atau terlipat. Edit manual di halaman Upload sebelum simpan. Hasil koreksi ini yang bikin kategori makin akurat.

## Lisensi

Bebas dipakai untuk belajar dan project pribadi.
