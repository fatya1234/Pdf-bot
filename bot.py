import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram import F

# ضعي توكن البوت بتاعك هنا (من @BotFather)
BOT_TOKEN = "8861251861:AAHPaufto74DP9e-Z63E-m4IpYsaHFs4P4M"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

TELEGRAM_LIMIT_MB = 50  # حد إرسال الملفات في تليجرام العادي


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "اهلاً! ابعتي رابط ملف PDF مباشر وأنا هضغطه وأرجعه لك."
    )


@dp.message(F.text.startswith("http"))
async def handle_link(message: types.Message):
    url = message.text.strip()
    await message.answer("⏳ بنزّل الملف...")

    original_path = os.path.join(DOWNLOAD_DIR, "original.pdf")
    compressed_path = os.path.join(DOWNLOAD_DIR, "compressed.pdf")

    try:
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(original_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        await message.answer(f"❌ حصل خطأ في تحميل الملف: {e}")
        return

    size_mb = os.path.getsize(original_path) / (1024 * 1024)
    await message.answer(f"📄 حجم الملف الأصلي: {size_mb:.2f} MB\n⏳ بنضغطه دلوقتي...")

    success = compress_pdf(original_path, compressed_path)

    if not success or not os.path.exists(compressed_path):
        await message.answer("❌ فشل ضغط الملف.")
        return

    new_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
    await message.answer(
        f"✅ تم الضغط!\nالحجم الجديد: {new_size_mb:.2f} MB"
    )

    if new_size_mb <= TELEGRAM_LIMIT_MB:
        doc = types.FSInputFile(compressed_path, filename="compressed.pdf")
        await message.answer_document(doc)
    else:
        await message.answer(
            "⚠️ الملف بعد الضغط لسه أكبر من 50 ميجا، فمش هينفع يُرسل عبر تليجرام مباشرة.\n"
            "محتاجين سيرفر/local Bot API server للملفات الأكبر."
        )

    os.remove(original_path)
    os.remove(compressed_path)


def compress_pdf(input_path: str, output_path: str) -> bool:
    """ضغط PDF باستخدام Ghostscript - يقلل جودة الصور لتقليل الحجم"""
    import subprocess
    try:
        subprocess.run(
            [
                "gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/screen",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={output_path}",
                input_path,
            ],
            check=True,
        )
        return True
    except Exception as e:
        logging.error(f"Ghostscript error: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
