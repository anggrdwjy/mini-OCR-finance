# Deploy Mini OCR Finance ke VPS Ubuntu

Panduan singkat untuk menjalankan project ini online, bisa diakses lewat domain.

## 1. Siapkan VPS

Rekomendasi minimal untuk 10-20 user:
- OS: Ubuntu 22.04 LTS atau 24.04 LTS
- CPU: 2 Core, rekomendasi 4 Core
- RAM: 4 GB, rekomendasi 8 GB
- Storage: 50 GB SSD
- Buka port: 22 (SSH), 80 (HTTP), 443 (HTTPS)

Arahkan domain kamu ke IP VPS:
- `app.kamu.com` -> IP VPS untuk frontend Streamlit
- `api.kamu.com` -> IP VPS untuk backend FastAPI

## 2. Install Docker di VPS

Login lewat SSH, lalu jalankan:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl unzip

# Install Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Cek
docker --version
docker compose version
```

Tambahkan user ke grup docker biar tidak perlu sudo terus:

```bash
sudo usermod -aG docker $USER
# Logout lalu login lagi
```

## 3. Upload Project ke VPS

Dari laptop kamu, upload ZIP nya:

```bash
scp mini-ocr-finance.zip root@IP_VPS:/root/
```

Di VPS, extract:

```bash
cd /root
unzip -o mini-ocr-finance.zip
cd mini-ocr-finance
ls -la
```

## 4. Setting .env untuk Production

```bash
cp .env.example .env
nano .env
```

Isi dengan nilai production, jangan pakai default:

```env
DB_USER=ocruser
DB_PASSWORD=password_kuat_acak_minimal_16_karakter
DB_NAME=ocr_finance
JWT_SECRET=secret_acak_panjang_minimal_32_karakter_beda_dari_lokal
JWT_EXPIRE_HOURS=24
OCR_PROVIDER=tesseract
OCR_API_KEY=
```

Buat password acak cepat:

```bash
openssl rand -base64 32
```

## 5. Setting Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Jangan buka port 5432, 8000, 8501 ke publik. Nanti diakses lewat Nginx saja.

## 6. Install Nginx dan Buat Reverse Proxy

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Buat file config:

```bash
sudo nano /etc/nginx/sites-available/ocr-finance
```

Isi:

```nginx
server {
    listen 80;
    server_name app.kamu.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}

server {
    listen 80;
    server_name api.kamu.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 20M;
    }
}
```

Aktifkan:

```bash
sudo ln -s /etc/nginx/sites-available/ocr-finance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Sesuaikan API_URL di Frontend

Secara default frontend di Docker pakai `http://backend:8000` untuk komunikasi internal.
Tapi browser user butuh akses API lewat domain.

Cara paling gampang untuk mini project:
Di file `frontend/app.py` dan `frontend/pages/*.py`, `API_URL` diambil dari env.
Di VPS, kita set `API_URL` di `docker-compose.yml` untuk service frontend jadi domain API publik.

Edit `docker-compose.yml` bagian frontend:

```yaml
  frontend:
    environment:
      API_URL: https://api.kamu.com
```

Atau kalau mau tetap internal dan tidak expose API ke publik, biarkan `http://backend:8000` dan hanya expose frontend.

Untuk versi ini, pakai `https://api.kamu.com` supaya Streamlit di browser bisa panggil API.

## 8. Jalankan dengan Docker Compose

```bash
cd /root/mini-ocr-finance
docker compose up -d --build
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

Cek:
- Backend: `curl http://localhost:8000/` harus balas JSON
- Frontend: `curl http://localhost:8501` harus balas HTML Streamlit

## 9. Pasang SSL Gratis

```bash
sudo certbot --nginx -d app.kamu.com -d api.kamu.com
```

Ikuti prompt, pilih redirect ke HTTPS. Certbot akan auto update config Nginx.
Cek auto renew:

```bash
sudo certbot renew --dry-run
```

## 10. Cek Online

Buka:
- `https://app.kamu.com` -> harus muncul halaman login Streamlit
- `https://api.kamu.com/docs` -> harus muncul Swagger FastAPI

Register akun baru, upload 1 struk, cek Dashboard dan Laporan Bulanan.

## 11. Perawatan

Lihat log:
```bash
docker compose logs -f --tail=100
```

Restart:
```bash
docker compose restart
```

Update kode baru:
```bash
# Upload zip baru, extract timpa, lalu:
docker compose up -d --build
```

Backup database:
```bash
docker compose exec db pg_dump -U ocruser ocr_finance > backup_$(date +%Y%m%d).sql
```

Restore:
```bash
cat backup_20261108.sql | docker compose exec -T db psql -U ocruser -d ocr_finance
```

Backup folder uploads:
```bash
tar -czf uploads_backup.tar.gz uploads/
```

## Troubleshooting

**Domain tidak bisa dibuka**
Cek DNS sudah mengarah ke IP VPS, cek `sudo nginx -t` dan `sudo systemctl status nginx`.

**Frontend 502 Bad Gateway**
Backend atau frontend belum jalan. Cek `docker compose ps` dan `docker compose logs -f frontend`.

**Login gagal di production**
Pastikan `JWT_SECRET` di `.env` tidak berubah setelah user register. Kalau berubah, semua token lama hangus, user harus login ulang.

**Upload gagal, file besar**
Naikkan `client_max_body_size 20M` di Nginx dan restart Nginx.

**Port bentrok**
Jangan jalankan PostgreSQL lokal di VPS bersamaan dengan Docker. Matikan service lokal atau ganti port di `docker-compose.yml`.

## Checklist Sebelum Go Live

- [ ] `.env` sudah diganti, tidak pakai password default
- [ ] Port 5432, 8000, 8501 tidak dibuka ke publik
- [ ] SSL sudah aktif, `https://` jalan
- [ ] Backup database sudah dites restore
- [ ] `docker compose up -d` jalan otomatis setelah reboot VPS
