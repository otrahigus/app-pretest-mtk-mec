"""
Aplikasi Pretest Matematika ADAPTIF - Level 0 s.d. Level 30 (SD-SMP)
Menggunakan metode binary search: anak diuji di level tebakan, naik/turun
berdasarkan benar/salah, sampai ditemukan level penempatan yang pas.
Hasil otomatis tersimpan ke Google Sheets. Siswa TIDAK melihat skor/level.
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

NAMA_WORKSHEET = "Hasil"   # nama sheet/tab tujuan di Google Sheets
LEVEL_MIN = 0
LEVEL_MAX = 30
MAKS_RONDE = 6              # pengaman agar tidak berputar tanpa henti (log2(31) ~ 5)

# =========================================================
# NAMA LEVEL (untuk ditampilkan ke guru di sidebar & Google Sheets)
# =========================================================
NAMA_LEVEL = {
    0: "Berhitung 1-50, +/- Dasar",
    1: "Berhitung 1-100, +/- Menyimpan/Meminjam",
    2: "Perkalian & Pembagian 1-10",
    3: "Bersusun Ratusan, Nilai Tempat",
    4: "Pecahan Dasar, +/- Penyebut Sama",
    5: "Persiapan Kelas Lanjut",
    6: "Menyederhanakan Pecahan, +/- Penyebut Beda",
    7: "Bilangan Bulat Positif/Negatif",
    8: "Satuan & Pengukuran",
    9: "Pola Bilangan, Variabel, Persamaan",
    10: "Nilai Tempat sampai 10.000",
    11: "+/- Pecahan Penyebut Beda",
    12: "Perbandingan, Skala, Untung/Rugi",
    13: "Bangun Datar & Volume",
    14: "Jaring-jaring, Luas Permukaan & Tabung",
    15: "Statistika, Mean/Median/Modus, Peluang",
    16: "Bentuk Aljabar, PLSV",
    17: "Perbandingan & Trigonometri Dasar",
    18: "Himpunan & Diagram Venn",
    19: "Bilangan Berpangkat & Bentuk Akar",
    20: "PLSV, PtLSV, PLDV",
    21: "SPLDV",
    22: "Relasi & Fungsi",
    23: "Garis & Sudut",
    24: "Segitiga & Teorema Pythagoras",
    25: "Segiempat & Segi-n",
    26: "Bangun Ruang Sisi Datar & Luas Permukaan",
    27: "Volume Bangun Ruang",
    28: "Lingkaran",
    29: "Statistika & Peluang",
    30: "Trigonometri & Transformasi",
}

# =========================================================
# BANK SOAL — 2 soal representatif per level (0-30)
# Setiap soal: {"soal":..., "kunci":..., "tipe":"text"/"pilihan_ganda", "opsi": [...]}
# =========================================================
ITEM_BANK = {
    0: [
        {"soal": "23 + 14 = ...", "kunci": "37", "tipe": "text"},
        {"soal": "46 - 22 = ...", "kunci": "24", "tipe": "text"},
    ],
    1: [
        {"soal": "38 + 27 = ...", "kunci": "65", "tipe": "text"},
        {"soal": "62 - 48 = ...", "kunci": "14", "tipe": "text"},
    ],
    2: [
        {"soal": "7 × 8 = ...", "kunci": "56", "tipe": "text"},
        {"soal": "54 : 6 = ...", "kunci": "9", "tipe": "text"},
    ],
    3: [
        {
            "soal": "Pada angka 4.725, angka 7 menempati nilai tempat ....",
            "kunci": "Ratusan",
            "tipe": "pilihan_ganda",
            "opsi": ["Ribuan", "Ratusan", "Puluhan", "Satuan"],
        },
        {"soal": "34 × 6 = ...", "kunci": "204", "tipe": "text"},
    ],
    4: [
        {"soal": "1/4 + 2/4 = ... (tulis sebagai pecahan, contoh: 3/4)", "kunci": "3/4", "tipe": "text"},
        {"soal": "Ubah pecahan 1/2 menjadi desimal: ...", "kunci": "0,5", "tipe": "text"},
    ],
    5: [
        {"soal": "23 × 14 = ...", "kunci": "322", "tipe": "text"},
        {"soal": "(8 + 4) × 2 = ...", "kunci": "24", "tipe": "text"},
    ],
    6: [
        {"soal": "Sederhanakan pecahan 8/12 menjadi bentuk paling sederhana: ...", "kunci": "2/3", "tipe": "text"},
        {"soal": "1/2 + 1/4 = ... (tulis sebagai pecahan)", "kunci": "3/4", "tipe": "text"},
    ],
    7: [
        {"soal": "(-5) + 8 = ...", "kunci": "3", "tipe": "text"},
        {"soal": "-3 + 5 × 2 = ...", "kunci": "7", "tipe": "text"},
    ],
    8: [
        {"soal": "5 km = ... m", "kunci": "5000", "tipe": "text"},
        {"soal": "Keliling persegi panjang dengan panjang 8 cm dan lebar 5 cm = ... cm", "kunci": "26", "tipe": "text"},
    ],
    9: [
        {"soal": "Lengkapi pola berikut: 2, 4, 6, 8, ...", "kunci": "10", "tipe": "text"},
        {"soal": "Jika x + 5 = 12, maka x = ...", "kunci": "7", "tipe": "text"},
    ],
    10: [
        {"soal": "3245 + 4518 = ...", "kunci": "7763", "tipe": "text"},
        {"soal": "215 × 4 = ...", "kunci": "860", "tipe": "text"},
    ],
    11: [
        {"soal": "1/3 + 1/4 = ... (tulis sebagai pecahan, contoh: 7/12)", "kunci": "7/12", "tipe": "text"},
        {"soal": "2/3 × 3/4 = ... (tulis sebagai pecahan paling sederhana)", "kunci": "1/2", "tipe": "text"},
    ],
    12: [
        {"soal": "Jika harga 4 kg apel adalah Rp60.000, berapa harga 6 kg apel? (tulis angka saja, tanpa titik)", "kunci": "90000", "tipe": "text"},
        {"soal": "Sebuah sepatu dibeli Rp150.000 dan dijual Rp180.000. Berapa untungnya? (angka saja)", "kunci": "30000", "tipe": "text"},
    ],
    13: [
        {"soal": "Luas segitiga dengan alas 10 cm dan tinggi 8 cm = ... cm²", "kunci": "40", "tipe": "text"},
        {"soal": "Volume balok dengan panjang 5 cm, lebar 4 cm, tinggi 3 cm = ... cm³", "kunci": "60", "tipe": "text"},
    ],
    14: [
        {"soal": "Luas permukaan balok dengan p=4 cm, l=3 cm, t=2 cm = ... cm²", "kunci": "52", "tipe": "text"},
        {"soal": "Volume tabung dengan jari-jari 7 cm dan tinggi 10 cm (π = 22/7) = ... cm³", "kunci": "1540", "tipe": "text"},
    ],
    15: [
        {"soal": "Mean (rata-rata) dari data 4, 6, 8, 10, 12 adalah ...", "kunci": "8", "tipe": "text"},
        {"soal": "Median dari data 3, 7, 9, 10, 15 adalah ...", "kunci": "9", "tipe": "text"},
    ],
    16: [
        {"soal": "3x + 5x = ...", "kunci": "8x", "tipe": "text"},
        {"soal": "Jika 2x + 3 = 11, maka x = ...", "kunci": "4", "tipe": "text"},
    ],
    17: [
        {"soal": "Jika a : b = 2 : 3 dan a = 8, maka b = ...", "kunci": "12", "tipe": "text"},
        {"soal": "sin 30° = ... (tulis sebagai pecahan, contoh: 1/2)", "kunci": "1/2", "tipe": "text"},
    ],
    18: [
        {"soal": "Diketahui A = {1,2,3,4} dan B = {3,4,5,6}. Tuliskan anggota A ∩ B (pisahkan dengan koma):", "kunci": "3, 4", "tipe": "text"},
        {"soal": "Diketahui A = {1,2,3,4} dan B = {3,4,5,6}. Tuliskan anggota A ∪ B (pisahkan dengan koma):", "kunci": "1, 2, 3, 4, 5, 6", "tipe": "text"},
    ],
    19: [
        {"soal": "2³ = ...", "kunci": "8", "tipe": "text"},
        {"soal": "√64 = ...", "kunci": "8", "tipe": "text"},
    ],
    20: [
        {"soal": "Selesaikan pertidaksamaan 2x + 3 > 7. Nilai batas x adalah ...", "kunci": "2", "tipe": "text"},
        {"soal": "Diketahui 2x + y = 10. Jika x = 3, maka y = ...", "kunci": "4", "tipe": "text"},
    ],
    21: [
        {"soal": "Diketahui x + y = 7 dan x - y = 1. Nilai x = ...", "kunci": "4", "tipe": "text"},
        {"soal": "Diketahui x + y = 7 dan x - y = 1. Nilai y = ...", "kunci": "3", "tipe": "text"},
    ],
    22: [
        {"soal": "Jika f(x) = 2x + 3, maka f(4) = ...", "kunci": "11", "tipe": "text"},
        {"soal": "Jika f(x) = 3x - 2 dan f(x) = 13, maka x = ...", "kunci": "5", "tipe": "text"},
    ],
    23: [
        {"soal": "Dua sudut saling berpelurus. Salah satu sudutnya 65°. Sudut lainnya = ... derajat", "kunci": "115", "tipe": "text"},
        {"soal": "Sebuah sudut siku-siku dibagi menjadi dua sudut sama besar. Besar masing-masing sudut = ... derajat", "kunci": "45", "tipe": "text"},
    ],
    24: [
        {"soal": "Segitiga siku-siku memiliki sisi siku-siku 3 cm dan 4 cm. Panjang sisi miring = ... cm", "kunci": "5", "tipe": "text"},
        {"soal": "Luas segitiga siku-siku dengan sisi siku-siku 6 cm dan 8 cm = ... cm²", "kunci": "24", "tipe": "text"},
    ],
    25: [
        {"soal": "Keliling persegi dengan panjang sisi 9 cm = ... cm", "kunci": "36", "tipe": "text"},
        {"soal": "Jumlah besar sudut dalam segi-8 (oktagon) = ... derajat", "kunci": "1080", "tipe": "text"},
    ],
    26: [
        {"soal": "Luas permukaan kubus dengan panjang sisi 5 cm = ... cm²", "kunci": "150", "tipe": "text"},
        {"soal": "Sebuah limas memiliki luas alas 16 cm² dan jumlah luas sisi tegak 48 cm². Luas permukaannya = ... cm²", "kunci": "64", "tipe": "text"},
    ],
    27: [
        {"soal": "Volume kubus dengan panjang sisi 6 cm = ... cm³", "kunci": "216", "tipe": "text"},
        {"soal": "Volume tabung dengan jari-jari 7 cm dan tinggi 10 cm (π = 22/7) = ... cm³", "kunci": "1540", "tipe": "text"},
    ],
    28: [
        {"soal": "Keliling lingkaran dengan jari-jari 14 cm (π = 22/7) = ... cm", "kunci": "88", "tipe": "text"},
        {"soal": "Luas lingkaran dengan jari-jari 7 cm (π = 22/7) = ... cm²", "kunci": "154", "tipe": "text"},
    ],
    29: [
        {"soal": "Mean dari data 5, 7, 9, 11, 13 adalah ...", "kunci": "9", "tipe": "text"},
        {"soal": "Sebuah dadu dilempar sekali. Peluang muncul angka genap = ... (tulis sebagai pecahan, contoh: 1/2)", "kunci": "1/2", "tipe": "text"},
    ],
    30: [
        {"soal": "cos 60° = ... (tulis sebagai pecahan, contoh: 1/2)", "kunci": "1/2", "tipe": "text"},
        {"soal": "Titik A(2,3) ditranslasikan oleh (3,-1). Koordinat bayangannya = ... (format: x,y)", "kunci": "5, 2", "tipe": "text"},
    ],
}

# Tebakan level awal berdasarkan kelas siswa (dipetakan kasar ke kurikulum di atas)
KELAS_KE_LEVEL_AWAL = {1: 1, 2: 3, 3: 5, 4: 8, 5: 11, 6: 13, 7: 17, 8: 21, 9: 25}
LEVEL_AWAL_DEFAULT = 15  # jika kelas tidak diketahui/tidak bisa dibaca -> mulai di tengah


# =========================================================
# FUNGSI BANTU
# =========================================================
def normalisasi(teks: str) -> str:
    """Menormalkan teks jawaban agar perbandingan lebih toleran
    terhadap spasi, huruf besar/kecil, dan format koma/titik ribuan."""
    teks = str(teks).strip().lower()
    teks = re.sub(r"\s*,\s*", ",", teks)
    teks = re.sub(r"\s+", "", teks)
    return teks


def cek_jawaban(jawaban_siswa: str, kunci: str) -> bool:
    if jawaban_siswa is None or str(jawaban_siswa).strip() == "":
        return False
    return normalisasi(jawaban_siswa) == normalisasi(kunci)


def tebak_level_awal(kelas_input: str) -> int:
    """Menebak level awal yang masuk akal berdasarkan angka kelas yang
    dituliskan siswa (mis. '5', '5A', 'VII', dll). Jika tidak terbaca,
    pakai level tengah sebagai default."""
    m = re.search(r"\d+", str(kelas_input))
    if m:
        angka_kelas = int(m.group())
        if angka_kelas in KELAS_KE_LEVEL_AWAL:
            return KELAS_KE_LEVEL_AWAL[angka_kelas]
    return LEVEL_AWAL_DEFAULT


def tentukan_label_level(level_tertinggi_lulus):
    """Menentukan label level penempatan akhir berdasarkan level
    tertinggi yang berhasil dilewati (lulus kedua soalnya)."""
    if level_tertinggi_lulus is None:
        return "Level 0.1", 0
    penempatan = level_tertinggi_lulus + 1
    if penempatan > LEVEL_MAX:
        return "Lulus semua level (tuntas s.d. Level 30)", LEVEL_MAX
    return f"Level {penempatan}.1", penempatan


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
    data = {
        "tahap": st.session_state.tahap,
        "nama": st.session_state.nama,
        "kelas": st.session_state.kelas,
        "rendah": st.session_state.rendah,
        "tinggi": st.session_state.tinggi,
        "level_uji": st.session_state.level_uji,
        "soal_idx": st.session_state.soal_idx,
        "jawaban_level_ini": st.session_state.jawaban_level_ini,
        "level_tertinggi_lulus": st.session_state.level_tertinggi_lulus,
        "ronde": st.session_state.ronde,
        "riwayat_ronde": st.session_state.riwayat_ronde,
        "riwayat_semua": st.session_state.riwayat_semua,
        "tersimpan": st.session_state.tersimpan,
    }
    try:
        st.query_params["p"] = _encode_progress(data)
    except Exception:
        pass


def hapus_progres_url():
    try:
        if "p" in st.query_params:
            del st.query_params["p"]
    except Exception:
        pass


# =========================================================
# GOOGLE SHEETS
# =========================================================
def sudah_pernah_pretest(nama: str, kelas: str) -> bool:
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        data = conn.read(worksheet=NAMA_WORKSHEET, ttl=0)
        data = data.dropna(how="all")
    except Exception:
        return False

    if data.empty or "Nama" not in data.columns or "Kelas" not in data.columns:
        return False

    nama_target = normalisasi(nama)
    kelas_target = normalisasi(kelas)
    nama_cocok = data["Nama"].astype(str).apply(normalisasi) == nama_target
    kelas_cocok = data["Kelas"].astype(str).apply(normalisasi) == kelas_target
    return bool((nama_cocok & kelas_cocok).any())


def simpan_ke_gsheets(nama, kelas, level_label, level_penempatan, level_tertinggi_lulus,
                      riwayat_ronde, riwayat_semua):
    conn = st.connection("gsheets", type=GSheetsConnection)

    worksheet_sudah_ada = True
    try:
        data_lama = conn.read(worksheet=NAMA_WORKSHEET, ttl=0)
        data_lama = data_lama.dropna(how="all")
    except Exception:
        data_lama = pd.DataFrame()
        worksheet_sudah_ada = False

    total_soal = len(riwayat_semua)
    total_benar = sum(1 for it in riwayat_semua if it["benar"])
    ringkasan_ronde = " | ".join(
        f"Level {r['level']} ({NAMA_LEVEL.get(r['level'], '')}): {r['skor']}/2 "
        f"{'LULUS' if r['lulus'] else 'gagal'}"
        for r in riwayat_ronde
    )

    baris_baru = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Nama": nama,
        "Kelas": kelas,
        "Level_Penempatan": level_label,
        "Level_Penempatan_Angka": level_penempatan,
        "Level_Tertinggi_Lulus": level_tertinggi_lulus if level_tertinggi_lulus is not None else "-",
        "Total_Soal_Dikerjakan": total_soal,
        "Total_Benar": total_benar,
        "Ringkasan_Per_Ronde": ringkasan_ronde,
        "Detail_Jawaban_JSON": json.dumps(riwayat_semua, ensure_ascii=False),
    }

    df_baru = pd.DataFrame([baris_baru])
    data_gabungan = pd.concat([data_lama, df_baru], ignore_index=True)

    if worksheet_sudah_ada:
        conn.update(worksheet=NAMA_WORKSHEET, data=data_gabungan)
    else:
        conn.create(worksheet=NAMA_WORKSHEET, data=data_gabungan)


# =========================================================
# STATE AWAL (dipulihkan dari URL jika sesi sempat terputus)
# =========================================================
if "tahap" not in st.session_state:
    progres_url = None
    try:
        if "p" in st.query_params:
            progres_url = _decode_progress(st.query_params["p"])
    except Exception:
        progres_url = None

    default_state = {
        "tahap": "identitas",
        "nama": "",
        "kelas": "",
        "rendah": LEVEL_MIN,
        "tinggi": LEVEL_MAX,
        "level_uji": LEVEL_AWAL_DEFAULT,
        "soal_idx": 0,
        "jawaban_level_ini": [],
        "level_tertinggi_lulus": None,
        "ronde": 0,
        "riwayat_ronde": [],
        "riwayat_semua": [],
        "tersimpan": False,
    }
    sumber = progres_url if progres_url else default_state
    for k, v in default_state.items():
        st.session_state[k] = sumber.get(k, v)


# =========================================================
# TAHAP 1: FORM IDENTITAS
# =========================================================
if st.session_state.tahap == "identitas":
    st.title("🧮 Pretest Matematika Adaptif")
    st.subheader("Menentukan Level Awal Kemampuan Matematika")
    st.write(
        "Sebelum memulai, silakan isi data diri terlebih dahulu. "
        "Soal akan menyesuaikan otomatis dengan kemampuanmu — jumlah soal "
        "tidak tetap, tergantung seberapa cepat sistem menemukan level yang pas."
    )

    with st.form("form_identitas"):
        nama_input = st.text_input("Nama Lengkap")
        kelas_input = st.text_input("Kelas (contoh: 5, 5A, 7B)")
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
                    st.session_state.level_uji = tebak_level_awal(kelas_input.strip())
                    st.session_state.tahap = "soal"
                    simpan_progres_ke_url()
                    st.rerun()

# =========================================================
# TAHAP 2: SOAL ADAPTIF
# =========================================================
elif st.session_state.tahap == "soal":
    level_uji = st.session_state.level_uji
    soal_idx = st.session_state.soal_idx
    item_aktif = ITEM_BANK[level_uji][soal_idx]

    st.title("🧮 Pretest Matematika Adaptif")
    estimasi_progres = min(st.session_state.ronde / MAKS_RONDE, 0.95)
    st.progress(estimasi_progres)
    st.caption(f"Tahap {st.session_state.ronde + 1} (perkiraan maksimal {MAKS_RONDE} tahap)")

    st.markdown(f"### Soal {soal_idx + 1} dari 2 (tahap ini)")
    st.write(item_aktif["soal"])
    st.caption("💡 Jika halaman error atau blank, refresh saja — progresmu tidak akan hilang.")

    with st.form(key=f"form_soal_{level_uji}_{soal_idx}"):
        if item_aktif["tipe"] == "pilihan_ganda":
            jawaban = st.radio(
                "Pilih jawaban:",
                options=item_aktif["opsi"],
                index=None,
                key=f"input_{level_uji}_{soal_idx}",
            )
        else:
            jawaban = st.text_input("Jawaban Anda:", key=f"input_{level_uji}_{soal_idx}")

        lanjut = st.form_submit_button("Jawab & Lanjut ➜")

        if lanjut:
            benar = cek_jawaban(jawaban, item_aktif["kunci"])
            st.session_state.jawaban_level_ini.append(benar)
            st.session_state.riwayat_semua.append(
                {
                    "level": level_uji,
                    "soal": item_aktif["soal"],
                    "jawaban": jawaban,
                    "benar": benar,
                }
            )

            if soal_idx + 1 < len(ITEM_BANK[level_uji]):
                # masih ada soal berikutnya di level yang sama
                st.session_state.soal_idx += 1
            else:
                # level ini selesai diuji -> evaluasi lulus/tidak
                skor_level = sum(st.session_state.jawaban_level_ini)
                lulus_level = skor_level == len(st.session_state.jawaban_level_ini)

                st.session_state.riwayat_ronde.append(
                    {"level": level_uji, "skor": skor_level, "lulus": lulus_level}
                )
                st.session_state.ronde += 1

                if lulus_level:
                    st.session_state.level_tertinggi_lulus = level_uji
                    st.session_state.rendah = level_uji + 1
                else:
                    st.session_state.tinggi = level_uji - 1

                if (
                    st.session_state.rendah > st.session_state.tinggi
                    or st.session_state.ronde >= MAKS_RONDE
                ):
                    st.session_state.tahap = "selesai"
                else:
                    st.session_state.level_uji = (
                        st.session_state.rendah + st.session_state.tinggi
                    ) // 2
                    st.session_state.soal_idx = 0
                    st.session_state.jawaban_level_ini = []

            simpan_progres_ke_url()
            st.rerun()

# =========================================================
# TAHAP 3: SELESAI -> HITUNG LEVEL, SIMPAN, TAMPILKAN UCAPAN
#           (LEVEL TIDAK DITAMPILKAN KE SISWA)
# =========================================================
elif st.session_state.tahap == "selesai":
    st.title("🧮 Pretest Matematika Adaptif")
    st.progress(1.0)

    level_label, level_penempatan = tentukan_label_level(st.session_state.level_tertinggi_lulus)

    if not st.session_state.tersimpan:
        try:
            simpan_ke_gsheets(
                st.session_state.nama,
                st.session_state.kelas,
                level_label,
                level_penempatan,
                st.session_state.level_tertinggi_lulus,
                st.session_state.riwayat_ronde,
                st.session_state.riwayat_semua,
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
        "Level penempatan tidak ditampilkan di halaman ini."
    )

    if st.button("Isi Ulang / Selesai"):
        for key in [
            "tahap", "nama", "kelas", "rendah", "tinggi", "level_uji", "soal_idx",
            "jawaban_level_ini", "level_tertinggi_lulus", "ronde", "riwayat_ronde",
            "riwayat_semua", "tersimpan",
        ]:
            del st.session_state[key]
        hapus_progres_url()
        st.rerun()

# =========================================================
# CATATAN UNTUK GURU (sidebar)
# =========================================================
with st.sidebar:
    st.markdown("#### Panduan Sistem Adaptif (untuk Guru)")
    st.caption(
        "Pretest ini bersifat **adaptif** menggunakan metode binary search "
        "di antara Level 0 sampai Level 30 (mengikuti kurikulum SD-SMP).\n\n"
        "**Cara penilaian:**\n"
        "- Setiap level diuji dengan 2 soal representatif.\n"
        "- Kedua soal benar → dianggap **lulus** level tsb, sistem naik ke "
        "level lebih tinggi.\n"
        "- Ada yang salah → dianggap **belum lulus**, sistem turun ke level "
        "lebih rendah.\n"
        "- Level penempatan akhir = satu level di atas level tertinggi yang "
        "lulus (mis. lulus s.d. Level 9 → penempatan Level 10.1).\n\n"
        "Hasil lengkap (level penempatan, ringkasan per tahap, dan detail "
        "tiap jawaban dalam format JSON) tersimpan otomatis di Google Sheets "
        f"pada worksheet **'{NAMA_WORKSHEET}'**."
    )
    with st.expander("Lihat daftar nama Level 0-30"):
        for lvl, nm in NAMA_LEVEL.items():
            st.caption(f"**Level {lvl}** — {nm}")