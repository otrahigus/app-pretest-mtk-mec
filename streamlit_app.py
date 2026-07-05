"""
Aplikasi Pretest Matematika - Operasi Hitung Bilangan Bulat
Level 0 s.d. Level 3 | 24 Soal
Hasil otomatis tersimpan ke Google Sheets, level ditentukan otomatis.
Siswa TIDAK melihat skor/level (hanya untuk guru, tersimpan di Sheets).
"""

import base64
import json
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# =========================================================
# KONFIGURASI HALAMAN
# =========================================================
st.set_page_config(
    page_title="Pretest Matematika",
    page_icon="🧮",
    layout="centered",
)

NAMA_WORKSHEET = "Hasil"  # nama sheet/tab tujuan di Google Sheets

# =========================================================
# BANK SOAL (24 SOAL)
# Setiap soal berupa dict:
#   level  : level materi (0-3)
#   soal   : teks pertanyaan
#   kunci  : kunci jawaban
#   tipe   : "text" (isian) atau "pilihan_ganda"
#   opsi   : daftar pilihan (hanya untuk tipe "pilihan_ganda")
# =========================================================
QUESTIONS = [
    # ---------- LEVEL 0 ----------
    {"level": 0, "soal": "Tuliskan angka yang hilang secara berurutan (pisahkan dengan koma):\n\n5, 6, __, 8, 9, __, 11", "kunci": "7, 10", "tipe": "text"},
    {"level": 0, "soal": "7 + 5 = ...", "kunci": "12", "tipe": "text"},
    {"level": 0, "soal": "15 - 3 = ...", "kunci": "12", "tipe": "text"},
    {"level": 0, "soal": "Tuliskan bilangan setelah 37: ...", "kunci": "38", "tipe": "text"},
    {"level": 0, "soal": "23 + 14 = ...", "kunci": "37", "tipe": "text"},
    {"level": 0, "soal": "46 - 22 = ...", "kunci": "24", "tipe": "text"},
    # ---------- LEVEL 1 ----------
    {"level": 1, "soal": "Tuliskan bilangan sebelum 80: ...", "kunci": "79", "tipe": "text"},
    {"level": 1, "soal": "43 + 26 = ...", "kunci": "69", "tipe": "text"},
    {"level": 1, "soal": "38 + 27 = ...", "kunci": "65", "tipe": "text"},
    {"level": 1, "soal": "75 - 34 = ...", "kunci": "41", "tipe": "text"},
    {"level": 1, "soal": "62 - 48 = ...", "kunci": "14", "tipe": "text"},
    {"level": 1, "soal": "Budi mempunyai 45 kelereng. Ia memberikan 18 kelereng kepada Adi. "
                          "Berapa sisa kelereng Budi?", "kunci": "27", "tipe": "text"},
    # ---------- LEVEL 2 ----------
    {"level": 2, "soal": "4 × 3 = ...", "kunci": "12", "tipe": "text"},
    {"level": 2, "soal": "20 : 5 = ...", "kunci": "4", "tipe": "text"},
    {"level": 2, "soal": "7 × 8 = ...", "kunci": "56", "tipe": "text"},
    {"level": 2, "soal": "54 : 6 = ...", "kunci": "9", "tipe": "text"},
    {"level": 2, "soal": "Ada 6 kantong, masing-masing berisi 5 apel. Berapa total apel seluruhnya?", "kunci": "30", "tipe": "text"},
    {"level": 2, "soal": "15 + 7 - 3 = ...", "kunci": "19", "tipe": "text"},
    # ---------- LEVEL 3 ----------
    {"level": 3, "soal": "276 + 158 = ...", "kunci": "434", "tipe": "text"},
    {"level": 3, "soal": "503 - 287 = ...", "kunci": "216", "tipe": "text"},
    {
        "level": 3,
        "soal": "Pada angka 4.725, angka 7 menempati nilai tempat ....",
        "kunci": "Ratusan",
        "tipe": "pilihan_ganda",
        "opsi": ["Ribuan", "Ratusan", "Puluhan", "Satuan"],
    },
    {"level": 3, "soal": "Urutkan dari yang terkecil (pisahkan dengan koma):\n\n675, 521, 789, 432",
     "kunci": "432, 521, 675, 789", "tipe": "text"},
    {"level": 3, "soal": "34 × 6 = ...", "kunci": "204", "tipe": "text"},
    {"level": 3, "soal": "Ibu membeli 4 kotak pensil. Setiap kotak berisi 12 pensil. "
                          "Ibu membagikan 15 pensil kepada murid-muridnya. "
                          "Berapa sisa pensil Ibu sekarang?", "kunci": "33", "tipe": "text"},
]

TOTAL_SOAL = len(QUESTIONS)


# =========================================================
# FUNGSI BANTU
# =========================================================
def normalisasi(teks: str) -> str:
    """Menormalkan teks jawaban agar perbandingan lebih toleran
    terhadap spasi, huruf besar/kecil, dan format koma."""
    teks = str(teks).strip().lower()
    teks = re.sub(r"\s*,\s*", ",", teks)   # rapikan spasi di sekitar koma
    teks = re.sub(r"\s+", "", teks)        # hapus semua spasi tersisa
    teks = teks.replace(".", "")           # abaikan titik ribuan, jika ada
    return teks


def cek_jawaban(jawaban_siswa: str, kunci: str) -> bool:
    if jawaban_siswa is None or jawaban_siswa.strip() == "":
        return False
    return normalisasi(jawaban_siswa) == normalisasi(kunci)


def tentukan_level(skor: int) -> str:
    if skor == 24:
        return "Lulus semua level"
    elif 19 <= skor <= 23:
        return "Level 3.1"
    elif 13 <= skor <= 18:
        return "Level 2.1"
    elif 7 <= skor <= 12:
        return "Level 1.1"
    else:
        return "Level 0.1"


def sudah_pernah_pretest(nama: str, kelas: str) -> bool:
    """Mengecek ke Google Sheets apakah kombinasi Nama+Kelas ini
    sudah pernah mengerjakan pretest sebelumnya."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        data = conn.read(worksheet=NAMA_WORKSHEET, ttl=0)
        data = data.dropna(how="all")
    except Exception:
        # Worksheet belum ada -> belum pernah ada yang mengerjakan pretest
        return False

    if data.empty or "Nama" not in data.columns or "Kelas" not in data.columns:
        return False

    nama_target = normalisasi(nama)
    kelas_target = normalisasi(kelas)

    nama_cocok = data["Nama"].astype(str).apply(normalisasi) == nama_target
    kelas_cocok = data["Kelas"].astype(str).apply(normalisasi) == kelas_target
    return bool((nama_cocok & kelas_cocok).any())


# =========================================================
# PENYIMPANAN PROGRES KE URL (agar tahan terhadap refresh /
# koneksi terputus saat siswa lama menjawab)
# =========================================================
def _encode_progress(data: dict) -> str:
    mentah = json.dumps(data, ensure_ascii=False)
    return base64.urlsafe_b64encode(mentah.encode("utf-8")).decode("utf-8")


def _decode_progress(token: str) -> dict:
    mentah = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
    return json.loads(mentah)


def simpan_progres_ke_url():
    """Menyalin progres pengerjaan saat ini ke query parameter URL,
    sehingga jika halaman ter-refresh (mis. koneksi sempat terputus),
    progres dapat dipulihkan tanpa mengulang dari soal nomor 1."""
    data = {
        "tahap": st.session_state.tahap,
        "index_soal": st.session_state.index_soal,
        "daftar_jawaban": st.session_state.daftar_jawaban,
        "nama": st.session_state.nama,
        "kelas": st.session_state.kelas,
        "tersimpan": st.session_state.tersimpan,
    }
    try:
        st.query_params["p"] = _encode_progress(data)
    except Exception:
        pass  # jika gagal, biarkan saja -> paling buruk progres tidak tersimpan di URL


def hapus_progres_url():
    try:
        if "p" in st.query_params:
            del st.query_params["p"]
    except Exception:
        pass


def simpan_ke_gsheets(nama: str, kelas: str, daftar_jawaban: list, skor: int, level: str):
    """Menyimpan satu baris hasil pretest ke Google Sheets."""
    conn = st.connection("gsheets", type=GSheetsConnection)

    worksheet_sudah_ada = True
    try:
        data_lama = conn.read(worksheet=NAMA_WORKSHEET, ttl=0)
        data_lama = data_lama.dropna(how="all")
    except Exception:
        # Worksheet dengan nama NAMA_WORKSHEET belum ada di spreadsheet
        data_lama = pd.DataFrame()
        worksheet_sudah_ada = False

    baris_baru = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Nama": nama,
        "Kelas": kelas,
        "Skor": skor,
        "Level": level,
    }
    for i, item in enumerate(daftar_jawaban, start=1):
        baris_baru[f"Soal_{i}_Jawaban"] = item["jawaban"]
        baris_baru[f"Soal_{i}_Benar"] = "Ya" if item["benar"] else "Tidak"

    df_baru = pd.DataFrame([baris_baru])
    data_gabungan = pd.concat([data_lama, df_baru], ignore_index=True)

    if worksheet_sudah_ada:
        conn.update(worksheet=NAMA_WORKSHEET, data=data_gabungan)
    else:
        # Worksheet belum tersedia di spreadsheet -> buat baru sekaligus isi datanya
        conn.create(worksheet=NAMA_WORKSHEET, data=data_gabungan)


# =========================================================
# STATE AWAL (dipulihkan dari URL jika sesi sebelumnya sempat
# terputus, misalnya karena siswa lama menjawab)
# =========================================================
if "tahap" not in st.session_state:
    progres_url = None
    try:
        if "p" in st.query_params:
            progres_url = _decode_progress(st.query_params["p"])
    except Exception:
        progres_url = None

    if progres_url:
        st.session_state.tahap = progres_url.get("tahap", "identitas")
        st.session_state.index_soal = progres_url.get("index_soal", 0)
        st.session_state.daftar_jawaban = progres_url.get("daftar_jawaban", [])
        st.session_state.nama = progres_url.get("nama", "")
        st.session_state.kelas = progres_url.get("kelas", "")
        st.session_state.tersimpan = progres_url.get("tersimpan", False)
    else:
        st.session_state.tahap = "identitas"   # identitas -> soal -> selesai
        st.session_state.index_soal = 0
        st.session_state.daftar_jawaban = []
        st.session_state.nama = ""
        st.session_state.kelas = ""
        st.session_state.tersimpan = False


# =========================================================
# TAHAP 1: FORM IDENTITAS
# =========================================================
if st.session_state.tahap == "identitas":
    st.title("🧮 Pretest Matematika")
    st.subheader("Operasi Hitung Bilangan Bulat")
    st.write(
        "Sebelum memulai, silakan isi data diri terlebih dahulu. "
        "Terdapat **24 soal** yang harus dikerjakan satu per satu."
    )

    with st.form("form_identitas"):
        nama_input = st.text_input("Nama Lengkap")
        kelas_input = st.text_input("Kelas")
        mulai = st.form_submit_button("Mulai Pretest")

        if mulai:
            if nama_input.strip() == "" or kelas_input.strip() == "":
                st.warning("Mohon isi Nama dan Kelas terlebih dahulu.")
            else:
                with st.spinner("Memeriksa data..."):
                    sudah_pernah = sudah_pernah_pretest(nama_input.strip(), kelas_input.strip())

                if sudah_pernah:
                    st.error(
                        "❌ Data dengan Nama dan Kelas ini sudah pernah mengerjakan "
                        "pretest sebelumnya. Setiap siswa hanya dapat mengerjakan "
                        "pretest satu kali. Jika kamu merasa ini keliru, silakan "
                        "hubungi gurumu."
                    )
                else:
                    st.session_state.nama = nama_input.strip()
                    st.session_state.kelas = kelas_input.strip()
                    st.session_state.tahap = "soal"
                    simpan_progres_ke_url()
                    st.rerun()

# =========================================================
# TAHAP 2: MENAMPILKAN SOAL SATU PER SATU
# =========================================================
elif st.session_state.tahap == "soal":
    idx = st.session_state.index_soal
    soal_aktif = QUESTIONS[idx]
    level_soal = soal_aktif["level"]
    teks_soal = soal_aktif["soal"]
    kunci_jawaban = soal_aktif["kunci"]
    tipe_soal = soal_aktif["tipe"]

    st.title("🧮 Pretest Matematika")
    st.progress((idx) / TOTAL_SOAL)
    st.caption(f"Soal {idx + 1} dari {TOTAL_SOAL}")

    st.markdown(f"### Soal {idx + 1}")
    st.write(teks_soal)
    st.caption("💡 Jika halaman error atau blank, refresh saja — progresmu tidak akan hilang.")

    with st.form(key=f"form_soal_{idx}"):
        if tipe_soal == "pilihan_ganda":
            jawaban = st.radio(
                "Pilih jawaban:",
                options=soal_aktif["opsi"],
                index=None,
                key=f"input_{idx}",
            )
        else:
            jawaban = st.text_input("Jawaban Anda:", key=f"input_{idx}")

        lanjut = st.form_submit_button("Jawab & Lanjut ➜")

        if lanjut:
            benar = cek_jawaban(jawaban, kunci_jawaban)
            st.session_state.daftar_jawaban.append(
                {"soal": teks_soal, "jawaban": jawaban, "benar": benar, "level": level_soal}
            )
            if idx + 1 < TOTAL_SOAL:
                st.session_state.index_soal += 1
            else:
                st.session_state.tahap = "selesai"
            simpan_progres_ke_url()
            st.rerun()

# =========================================================
# TAHAP 3: SELESAI -> HITUNG SKOR, SIMPAN, TAMPILKAN UCAPAN
#           (SKOR & LEVEL TIDAK DITAMPILKAN KE SISWA)
# =========================================================
elif st.session_state.tahap == "selesai":
    st.title("🧮 Pretest Matematika")
    st.progress(1.0)

    skor = sum(1 for item in st.session_state.daftar_jawaban if item["benar"])
    level = tentukan_level(skor)

    if not st.session_state.tersimpan:
        try:
            simpan_ke_gsheets(
                st.session_state.nama,
                st.session_state.kelas,
                st.session_state.daftar_jawaban,
                skor,
                level,
            )
            st.session_state.tersimpan = True
            simpan_progres_ke_url()
        except Exception as e:
            st.error(
                "Terjadi kendala saat menyimpan hasil. "
                "Silakan hubungi guru/admin untuk memastikan koneksi Google Sheets."
            )
            st.exception(e)

    st.success("✅ Pretest telah selesai dikerjakan. Terima kasih!")
    st.write(
        f"**Nama:** {st.session_state.nama}  \n"
        f"**Kelas:** {st.session_state.kelas}"
    )
    st.info(
        "Hasil pretest kamu sudah tersimpan dan akan diinformasikan oleh gurumu. "
        "Skor dan level tidak ditampilkan di halaman ini."
    )

    if st.button("Isi Ulang / Selesai"):
        for key in ["tahap", "index_soal", "daftar_jawaban", "nama", "kelas", "tersimpan"]:
            del st.session_state[key]
        hapus_progres_url()
        st.rerun()

# =========================================================
# CATATAN UNTUK GURU (disembunyikan dari alur utama, opsional)
# =========================================================
with st.sidebar:
    st.markdown("#### Panduan Level (untuk Guru)")
    st.caption(
        "- Skor 24 → Lulus semua level\n"
        "- Skor 19–23 → Level 3.1\n"
        "- Skor 13–18 → Level 2.1\n"
        "- Skor 7–12 → Level 1.1\n"
        "- Skor 0–6 → Level 0.1\n\n"
        "Hasil lengkap tiap siswa dapat dilihat pada Google Sheets "
        f"di worksheet **'{NAMA_WORKSHEET}'**."
    )