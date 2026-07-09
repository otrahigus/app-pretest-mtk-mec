# Panduan Setup & Deployment — Aplikasi Pretest Matematika

Panduan ini mencakup: menyiapkan Google Sheets API, mengisi `secrets.toml`,
menjalankan aplikasi secara lokal, dan deploy ke Streamlit Community Cloud.

---

## 1. Siapkan Google Sheet Tujuan

1. Buat Google Sheet baru, beri nama misalnya **"Database Pretest Matematika"**.
2. Buat satu sheet/tab dengan nama **`Hasil`** (huruf besar-kecil harus sama
   persis dengan `NAMA_WORKSHEET` di `streamlit_app.py`). Ini opsional —
   kalau tab `Hasil` belum ada, aplikasi akan **membuatnya secara otomatis**
   saat siswa pertama menyelesaikan pretest. Namun tetap disarankan membuat
   tab-nya lebih dulu secara manual agar lebih terkontrol.
3. Baris pertama boleh dikosongkan — aplikasi akan otomatis membuat header
   saat data pertama disimpan. Jika ingin header manual, isi baris 1 dengan:
   `Timestamp, Nama, Kelas, Skor, Level, Soal_1_Jawaban, Soal_1_Benar, ...`
4. Salin **URL lengkap** Google Sheet tersebut (akan dipakai di secrets).

---

## 2. Buat Service Account & Aktifkan API (Google Cloud Console)

1. Buka https://console.cloud.google.com/ dan buat project baru (atau pakai
   project yang sudah ada).
2. Di menu **APIs & Services > Library**, aktifkan dua API berikut:
   - **Google Sheets API**
   - **Google Drive API**
3. Buka **APIs & Services > Credentials** → **Create Credentials** →
   **Service Account**.
   - Beri nama, misalnya `pretest-matematika-sa`.
   - Peran (role) tidak wajib diisi (Skip/Continue) karena akses diatur lewat
     sharing sheet, bukan IAM.
4. Setelah service account terbuat, klik service account tersebut → tab
   **Keys** → **Add Key** → **Create New Key** → pilih **JSON** → Download.
   File JSON ini berisi kredensial rahasia — jangan diunggah ke GitHub.
5. Buka file JSON tersebut, catat nilai `client_email` (contoh:
   `pretest-matematika-sa@nama-project.iam.gserviceaccount.com`).

---

## 3. Bagikan (Share) Google Sheet ke Service Account

1. Buka Google Sheet yang dibuat di langkah 1.
2. Klik **Share/Bagikan**.
3. Tempelkan email service account (`client_email` dari file JSON) sebagai
   **Editor**.
4. Klik **Send/Kirim** (tidak perlu mencentang notifikasi email).

Tanpa langkah ini, aplikasi akan mendapat error `PERMISSION_DENIED` saat
membaca/menulis sheet.

---

## 4. Menyiapkan `secrets.toml` (Lokal)

Buat folder `.streamlit` di root proyek, lalu buat file
`.streamlit/secrets.toml` dengan isi berikut (nilai diambil dari file JSON
service account):

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/ISI_DENGAN_ID_SHEET_ANDA/edit"

type = "service_account"
project_id = "isi-project-id-anda"
private_key_id = "isi-private-key-id-anda"
private_key = "-----BEGIN PRIVATE KEY-----\nISI_PRIVATE_KEY_ANDA\n-----END PRIVATE KEY-----\n"
client_email = "pretest-matematika-sa@nama-project.iam.gserviceaccount.com"
client_id = "isi-client-id-anda"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "isi-client-x509-cert-url-anda"
```

**Catatan penting:**
- Semua nilai (`project_id`, `private_key`, dll.) disalin langsung dari file
  JSON service account yang diunduh di langkah 2.
- Pada `private_key`, pastikan karakter newline tetap berupa `\n` (biasanya
  sudah otomatis benar jika disalin apa adanya dari file JSON ke dalam tanda
  kutip TOML).
- Tambahkan `.streamlit/secrets.toml` ke `.gitignore` agar kredensial tidak
  ikut ter-commit ke repository publik.

---

## 5. Struktur Folder Proyek

```
pretest_app/
├── streamlit_app.py
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml      (jangan di-commit ke GitHub)
```

Contoh isi `.gitignore`:
```
.streamlit/secrets.toml
__pycache__/
*.pyc
```

---

## 6. Menjalankan Aplikasi Secara Lokal

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Aplikasi akan terbuka di browser pada `http://localhost:8501`.

---

## 7. Deploy ke Streamlit Community Cloud

1. Unggah folder proyek (tanpa `secrets.toml`) ke repository GitHub, misalnya
   `pretest-matematika`.
2. Buka https://share.streamlit.io/ dan login dengan akun GitHub.
3. Klik **New app**, pilih repository dan branch, lalu tentukan file utama:
   `streamlit_app.py`.
4. Sebelum/atau setelah deploy, buka **App settings > Secrets**, lalu
   tempelkan seluruh isi `secrets.toml` (persis seperti pada langkah 4) ke
   kolom Secrets tersebut, kemudian **Save**.
5. Klik **Deploy**. Streamlit akan menginstal dependensi dari
   `requirements.txt` dan menjalankan aplikasi.
6. Setelah aktif, bagikan URL aplikasi (`https://nama-app.streamlit.app`)
   kepada siswa untuk mengerjakan pretest.

---

## 8. Cara Guru Melihat Hasil

- Buka Google Sheet yang sudah dihubungkan, lalu buka tab **Hasil**.
- Setiap kali siswa menyelesaikan pretest, satu baris baru otomatis
  ditambahkan berisi:
  - `Timestamp`, `Nama`, `Kelas`
  - `Level_Penempatan` (contoh: "Level 10.1") dan `Level_Penempatan_Angka`
  - `Level_Tertinggi_Lulus` — level tertinggi yang berhasil dilewati siswa
  - `Total_Soal_Dikerjakan` dan `Total_Benar` — jumlah soal yang dijalani
    (bervariasi antar siswa karena sistem adaptif, biasanya sekitar 10-12 soal)
  - `Ringkasan_Per_Ronde` — ringkasan tiap tahap pengujian, contoh:
    `Level 15 (Statistika...): 2/2 LULUS | Level 23 (...): 1/2 gagal`
  - `Detail_Jawaban_JSON` — rincian lengkap tiap soal & jawaban dalam format
    JSON, bisa dibuka/diformat ulang jika perlu audit mendalam.
- Level penempatan siswa dapat langsung dilihat pada kolom
  **`Level_Penempatan`**.

### Catatan tentang sistem adaptif
Pretest ini menggunakan metode **binary search** di antara Level 0–30
(mengikuti kurikulum SD-SMP). Setiap level diuji dengan 2 soal representatif:
- Kedua soal benar → level dianggap **lulus**, sistem naik menguji level
  lebih tinggi.
- Ada yang salah → level dianggap **belum lulus**, sistem turun menguji
  level lebih rendah.
- Proses berhenti ketika rentang pencarian habis (maksimal ~6 tahap
  pengujian), dan level penempatan akhir = satu level di atas level
  tertinggi yang berhasil dilewati.

Karena sifatnya adaptif, jumlah soal yang dikerjakan setiap siswa bisa
berbeda-beda — ini normal dan merupakan bagian dari desain agar pretest
lebih efisien dan tetap akurat menemukan level yang pas untuk tiap anak.

---

## 9. Troubleshooting Umum

| Masalah | Kemungkinan Penyebab | Solusi |
|---|---|---|
| `PERMISSION_DENIED` | Sheet belum di-share ke service account | Ulangi langkah 3 |
| `SpreadsheetNotFound` | URL di secrets salah/typo | Cek ulang `spreadsheet` di secrets.toml |
| `WorksheetNotFound` | Tab `Hasil` belum ada di spreadsheet | Sudah ditangani otomatis oleh kode (akan dibuat sendiri saat data pertama disimpan). Jika masih error, pastikan service account punya akses **Editor**, karena membuat tab baru butuh izin tulis |
| Data tidak muncul di Sheets | Nama worksheet tidak sama (`Hasil`) | Samakan nama tab dengan `NAMA_WORKSHEET` |
| Error saat deploy karena `secrets.toml` tidak ada | Secrets belum diisi di dashboard Streamlit Cloud | Isi via App settings > Secrets |