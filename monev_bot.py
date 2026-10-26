import os
import sys
import asyncio
from datetime import datetime
import pytz

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot Monev is running and healthy!")

    def log_message(self, format, *args):
        # Mute log akses web request agar terminal tetap bersih
        pass

def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Health check web server aktif di port {port} (siap untuk Render)")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Gagal menjalankan health check web server di port {port}: {e}")


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from google import genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from dotenv import load_dotenv

# Muat file .env dari folder yang sama
load_dotenv()

# ================= KONFIGURASI DARI .ENV =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_CHAT_ID = int(os.getenv("USER_CHAT_ID", "0"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TIMEZONE = pytz.timezone("Asia/Makassar")  # WITA (BPOM Mataram)
URL_MONEV = os.getenv("URL_MONEV", "https://monev.maganghub.kemnaker.go.id")
# =========================================================

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY or not USER_CHAT_ID:
    print("⚠️ PERINGATAN: Pastikan TELEGRAM_BOT_TOKEN, USER_CHAT_ID, dan GEMINI_API_KEY sudah diisi di file .env!")

# Inisialisasi Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Status apakah hari ini sudah diisi
sudah_diisi_hari_ini = False
last_date_recorded = None


def generate_monev_content(user_notes: str) -> dict:
    """Menggunakan Gemini untuk merangkum isian pas minimal 100 karakter, padat, dan tidak bertele-tele."""
    prompt = f"""
Anda adalah asisten cerdas pengisi laporan harian MagangHub Kemnaker (Monev) untuk posisi IT / Pengembang Sistem di instansi BBPOM.
Pengguna memberikan catatan singkat kegiatan hari ini:
"{user_notes}"

Tugas Anda adalah menghasilkan 3 bagian isian:
1. Uraian Aktivitas
2. Pembelajaran yang Diperoleh
3. Kendala yang Dialami

ATURAN KETAT:
- Masing-masing bagian HARUS MINIMAL 100 KARAKTER (sistem menolak jika di bawah 100 karakter).
- JANGAN TERLALU PANJANG! Buat ringkas, lugas, padat, dan profesional (sekitar 110 - 140 karakter per bagian).
- Gaya bahasa formal dan realistis untuk pekerjaan teknis IT/Software.
- Jika pada catatan pengguna tidak ada kendala, tuliskan bahwa kendala teknis dapat diatasi dengan baik (tetap minimal 100 karakter).

Format keluaran WAJIB persis seperti ini (pisahkan dengan pemisah ###):
URAIAN:
[isi uraian minimal 100 karakter]
###
PEMBELAJARAN:
[isi pembelajaran minimal 100 karakter]
###
KENDALA:
[isi kendala minimal 100 karakter]
"""
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text

    # Parsing output
    parts = text.split("###")
    uraian = (
        parts[0].replace("URAIAN:", "").strip()
        if len(parts) > 0
        else "Melakukan pengembangan sistem..."
    )
    pembelajaran = (
        parts[1].replace("PEMBELAJARAN:", "").strip()
        if len(parts) > 1
        else "Mempelajari alur kerja..."
    )
    kendala = (
        parts[2].replace("KENDALA:", "").strip()
        if len(parts) > 2
        else "Tidak ada kendala yang signifikan..."
    )

    return {
        "uraian": uraian,
        "pembelajaran": pembelajaran,
        "kendala": kendala,
    }


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    welcome_text = (
        "👋 Halo! Saya adalah **Bot Asisten Monev MagangHub**.\n\n"
        f"🆔 **Chat ID Anda:** `{chat_id}`\n"
        "*(Salin ID di atas dan masukkan ke file `.env` pada variabel `USER_CHAT_ID`)*\n\n"
        "🔔 Saya akan mengingatkan Anda setiap 1 jam mulai jam 16:00 WITA (Senin-Jumat) jika belum mengisi Monev.\n\n"
        "💡 **Cara pakai:** Cukup ketik kegiatan singkat Anda hari ini di sini, contoh:\n"
        "`- benerin verifikasi katim dan tu`\n"
        "`- buat filter reagen exp`\n\n"
        "AI akan langsung membuatkan 3 isian formal (min. 100 karakter) yang siap Anda salin ke website Monev!\n\n"
        "🛠 Perintah lain:\n"
        "/myid - Lihat Chat ID Anda\n"
        "/test - Tes langsung notifikasi pengingat jam 16:00"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan Chat ID pengguna."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🆔 Chat ID Anda adalah: `{chat_id}`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menguji tampilan notifikasi pengingat secara langsung."""
    now = datetime.now(TIMEZONE)
    reminder_text = (
        f"🔔 **[TES] PENGINGAT ABSEN MONEV ({now.strftime('%H:%M')} WITA)**\n\n"
        "Anda belum mengisi laporan harian MagangHub hari ini!\n"
        "Silakan **balas chat ini dengan poin kegiatan singkat** Anda hari ini agar AI buatkan isiannya."
    )
    keyboard = [
        [
            InlineKeyboardButton("🌐 Buka Website Monev", url=URL_MONEV),
            InlineKeyboardButton("✅ Sudah Isi", callback_data="mark_done"),
        ]
    ]
    await update.message.reply_text(
        reminder_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menerima pesan kegiatan dari user dan mengoptimalkannya dengan AI."""
    global sudah_diisi_hari_ini
    user_input = update.message.text

    wait_msg = await update.message.reply_text("⏳ Sedang menyusun isian Monev dengan AI...")

    try:
        data = generate_monev_content(user_input)

        # Di Telegram mobile, teks di dalam tag `code block` (```) bisa disalin HANYA DENGAN 1 KALI TAP!
        response_text = (
            f"✨ **Isian Monev Siap Digunakan!**\n"
            f"*(Tap pada masing-masing kotak abu-abu di bawah untuk langsung menyalin teks)*\n\n"
            f"📌 **1. Uraian Aktivitas** ({len(data['uraian'])} karakter):\n"
            f"```{data['uraian']}```\n\n"
            f"💡 **2. Pembelajaran yang Diperoleh** ({len(data['pembelajaran'])} karakter):\n"
            f"```{data['pembelajaran']}```\n\n"
            f"⚠️ **3. Kendala yang Dialami** ({len(data['kendala'])} karakter):\n"
            f"```{data['kendala']}```"
        )

        keyboard = [
            [
                InlineKeyboardButton("🌐 Buka Website Monev", url=URL_MONEV),
                InlineKeyboardButton("✅ Sudah Saya Isi!", callback_data="mark_done"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await wait_msg.delete()
        await update.message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
    except Exception as e:
        await wait_msg.edit_text(f"❌ Gagal memproses AI: {str(e)}")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler tombol 'Sudah Saya Isi'"""
    global sudah_diisi_hari_ini
    query = update.callback_query
    await query.answer()

    if query.data == "mark_done":
        sudah_diisi_hari_ini = True
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "🎉 **Bagus sekali!** Pengingat untuk hari ini dihentikan. Sampai jumpa besok sore!"
        )


async def check_and_send_reminder(app):
    """Fungsi pengingat berkala setiap 1 jam mulai jam 16:00 sampai 21:00 WITA."""
    global sudah_diisi_hari_ini, last_date_recorded

    now = datetime.now(TIMEZONE)
    today_str = now.strftime("%Y-%m-%d")

    # Reset status saat berganti hari baru
    if last_date_recorded != today_str:
        sudah_diisi_hari_ini = False
        last_date_recorded = today_str

    # Hanya jalankan di hari kerja (Senin=0 s/d Jumat=4)
    if now.weekday() >= 5:
        return

    # Hanya ingatkan di jam 16:00 sampai 21:00 WITA jika belum isi
    if 16 <= now.hour <= 23 and not sudah_diisi_hari_ini:
        reminder_text = (
            f"🔔 **PENGINGAT ABSEN MONEV ({now.strftime('%H:%M')} WITA)**\n\n"
            "Anda belum mengisi laporan harian MagangHub hari ini!\n"
            "Silakan **balas chat ini dengan poin kegiatan singkat** Anda hari ini agar AI buatkan isiannya."
        )
        keyboard = [
            [
                InlineKeyboardButton("🌐 Buka Monev", url=URL_MONEV),
                InlineKeyboardButton("✅ Sudah Isi", callback_data="mark_done"),
            ]
        ]
        await app.bot.send_message(
            chat_id=USER_CHAT_ID,
            text=reminder_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


scheduler = AsyncIOScheduler(timezone=TIMEZONE)


async def post_init(application):
    """Memulai scheduler setelah event loop asyncio aktif."""
    scheduler.add_job(
        check_and_send_reminder,
        "cron",
        minute="0",
        hour="16-21",
        day_of_week="mon-fri",
        args=[application],
    )
    scheduler.start()
    print("⏰ Scheduler pengingat logbook aktif (Setiap jam 16:00 - 21:00 WITA, Senin - Jumat)")


async def post_shutdown(application):
    """Mematikan scheduler secara aman saat bot berhenti."""
    if scheduler.running:
        scheduler.shutdown(wait=False)


def main():
    # Jalankan health check web server di background thread (diperlukan untuk Render Web Service)
    threading.Thread(target=start_health_server, daemon=True).start()

    request_config = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request_config)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot Monev MagangHub aktif dan siap menerima pesan...")
    app.run_polling(bootstrap_retries=5)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Bot dimatikan.")


