# 🤖 Bot Pengingat & Generator Logbook Harian Monev MagangHub

Bot Telegram pintar berbasis AI (Google Gemini 2.5 Flash) yang otomatis:
1. **Mengingatkan pengisian logbook / absen harian Monev MagangHub** setiap jam 16:00 - 21:00 WITA (Senin - Jumat).
2. **Membuatkan teks isian logbook harian otomatis yang rapi dan profesional** hanya dengan mengirimkan poin-poin kegiatan singkat Anda hari ini.
3. **Format hasil copy-paste friendly**:
   - 🎯 **Rencana Capaian**: Output dalam codeblock (tinggal klik untuk copy).
   - 📝 **Deskripsi Realisasi**: Output dalam codeblock (tinggal klik untuk copy).
   - 🌟 **Hasil & Refleksi**: Rangkuman pencapaian dan pembelajaran hari ini.
   - Tombol langsung ke website Monev MagangHub dan tombol "✅ Sudah Isi" untuk mematikan pengingat hari tersebut.

---

## 🚀 Panduan Setup Cepat

### 1. Salin File Konfigurasi `.env`
Salin file `.env.example` menjadi `.env`:
```bash
copy .env.example .env
```

### 2. Isi Konfigurasi `.env`
Buka file `.env` dan masukkan:
- `TELEGRAM_BOT_TOKEN`: Token bot dari [@BotFather](https://t.me/BotFather).
- `USER_CHAT_ID`: ID akun Telegram Anda (jika belum tahu, jalankan bot lalu ketik `/myid`).
- `GEMINI_API_KEY`: API Key Google Gemini (gratis didapatkan dari [Google AI Studio](https://aistudio.google.com/)).
- `TIMEZONE`: Default `Asia/Makassar` (WITA). Sesuaikan jika di zona lain (misal: `Asia/Jakarta`).

### 3. Install Dependensi (jika belum)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Jalankan Bot
Cukup klik ganda (double-click) file **`run_bot.bat`** atau jalankan lewat terminal:
```bash
run_bot.bat
```

---

## 💡 Cara Penggunaan

1. **Cek Koneksi & ID Anda**:
   Kirim perintah `/start` atau `/myid` ke bot di Telegram.
2. **Test Simulasi Notifikasi Pengingat**:
   Kirim perintah `/test` ke bot untuk mencoba tampilan pengingat logbook.
3. **Generate Isian Logbook**:
   Kirim pesan biasa berisi kegiatan harian Anda (bisa santai / bullet points). Contoh:
   > *"hari ini menyelesaikan bug verifikasi katim di percepat, bikin fitur filter expired barang reagen, sama ikut rapat evaluasi mingguan"*
   
   AI akan langsung membalas dengan draf **Rencana Capaian**, **Deskripsi Realisasi**, dan **Hasil & Refleksi** dalam format siap copy!
4. **Matikan Pengingat**:
   Setelah selesai mengisi Monev MagangHub, klik tombol **"✅ Sudah Isi"** pada pesan pengingat agar bot tidak mengingatkan lagi untuk hari tersebut.
