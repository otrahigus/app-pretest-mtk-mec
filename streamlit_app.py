"""
Aplikasi Pretest Matematika - Operasi Hitung Bilangan Bulat
Level 0 s.d. Level 3 | 24 Soal
Hasil otomatis tersimpan ke Google Sheets, level ditentukan otomatis.
Siswa TIDAK melihat skor/level (hanya untuk guru, tersimpan di Sheets).
"""

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
# Format: (level, teks_soal, kunci_jawaban)
# =========================================================
QUESTIONS = [
    # ---------- LEVEL 0 ----------
    (0, "Tuliskan angka yang hilang secara berurutan (pisahkan dengan koma):\n\n5, 6, __, 8, 9, __, 11", "7, 10"),
    (0, "7 + 5 = ...", "12"),
    (0, "15 - 3 = ...", "12"),
    (0, "Tuliskan bilangan setelah 37: ...", "38"),
    (0, "23 + 14 = ...", "37"),
    (0, "46 - 22 = ...", "24"),
    # ---------- LEVEL 1 ----------
    (1, "Tuliskan bilangan sebelum 80: ...", "79"),
    (1, "43 + 26 = ...", "69"),
    (1, "38 + 27 = ...", "65"),
    (1, "75 - 34 = ...", "41"),
    (1, "62 - 48 = ...", "14"),
    (1, "Budi mempunyai 45 kelereng. Ia memberikan 18 kelereng kepada Adi. "
        "Berapa sisa kelereng Budi?", "27"),
    # ---------- LEVEL 2 ----------
    (2, "4 × 3 = ...", "12"),
    (2, "20 : 5 = ...", "4"),
    (2, "7 × 8 = ...", "56"),
    (2, "54 : 6 = ...", "9"),
    (2, "Ada 6 kantong, masing-masing berisi 5 apel. Berapa total apel seluruhnya?", "30"),
    (2, "15 + 7 - 3 = ...", "19"),
    # ---------- LEVEL 3 ----------
    (3, "276 + 158 = ...", "434"),
    (3, "503 - 287 = ...", "216"),
    (3, "Pada angka 4.725, angka 7 menempati nilai tempat ....", "ratusan"),
    (3, "Urutkan dari yang terkecil (pisahkan dengan koma):\n\n675, 521, 789, 432",
        "432, 521, 675, 789"),
    (3, "34 × 6 = ...", "204"),
    (3, "Ibu membeli 4 kotak pensil. Setiap kotak berisi 12 pensil. "
        "Ibu membagikan 15 pensil kepada murid-muridnya. "
        "Berapa sisa pensil Ibu sekarang?", "33"),
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


def simpan_ke_gsheets(nama: str, kelas: str, daftar_jawaban: list, skor: int, level: str):
    """Menyimpan satu baris hasil pretest ke Google Sheets."""
    conn = st.connection("gsheets", type=GSheetsConnection)

    try:
        data_lama = conn.read(worksheet=NAMA_WORKSHEET, ttl=0)
        data_lama = data_lama.dropna(how="all")
    except Exception:
        data_lama = pd.DataFrame()

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
    conn.update(worksheet=NAMA_WORKSHEET, data=data_gabungan)


# =========================================================
# STATE AWAL
# =========================================================
if "tahap" not in st.session_state:
    st.session_state.tahap = "identitas"   # identitas -> soal -> selesai
if "index_soal" not in st.session_state:
    st.session_state.index_soal = 0
if "daftar_jawaban" not in st.session_state:
    st.session_state.daftar_jawaban = []
if "nama" not in st.session_state:
    st.session_state.nama = ""
if "kelas" not in st.session_state:
    st.session_state.kelas = ""
if "tersimpan" not in st.session_state:
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
                st.session_state.nama = nama_input.strip()
                st.session_state.kelas = kelas_input.strip()
                st.session_state.tahap = "soal"
                st.rerun()

# =========================================================
# TAHAP 2: MENAMPILKAN SOAL SATU PER SATU
# =========================================================
elif st.session_state.tahap == "soal":
    idx = st.session_state.index_soal
    level_soal, teks_soal, kunci_jawaban = QUESTIONS[idx]

    st.title("🧮 Pretest Matematika")
    st.progress((idx) / TOTAL_SOAL)
    st.caption(f"Soal {idx + 1} dari {TOTAL_SOAL}")

    st.markdown(f"### Soal {idx + 1}")
    st.write(teks_soal)

    with st.form(key=f"form_soal_{idx}"):
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