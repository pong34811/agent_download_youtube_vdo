import os
import subprocess
import sys
from datetime import datetime
import yt_dlp


def auto_update_ytdlp() -> None:
    """อัปเดต yt-dlp อัตโนมัติถ้ามีเวอร์ชันใหม่"""
    try:
        print("🔍 กำลังตรวจสอบเวอร์ชัน yt-dlp...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if "Successfully installed" in result.stdout:
            import importlib
            importlib.reload(yt_dlp)
            print(f"⬆️  อัปเดต yt-dlp เป็นเวอร์ชัน {yt_dlp.version.__version__}")
        else:
            print(f"✅ yt-dlp เวอร์ชัน {yt_dlp.version.__version__} ล่าสุดแล้ว")
    except Exception as e:
        print(f"⚠️  ไม่สามารถอัปเดต yt-dlp ได้: {e}")


def download_video(url: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "merge_output_format": "mp4",
        "outtmpl": f"{today}/%(title)s.%(ext)s",
        # ลด concurrent เพื่อไม่ให้ YouTube detect และ throttle
        "concurrent_fragment_downloads": 1,
        # retry ไม่จำกัดจำนวน (float('inf'))
        "retries": float("inf"),
        "fragment_retries": float("inf"),
        "file_access_retries": float("inf"),
        # ต่อดาวน์โหลดต่อจากจุดที่ค้างได้
        "continuedl": True,
        # หยุดพักระหว่าง retry เพื่อลด rate-limit
        "sleep_interval_requests": 1,
        "sleep_interval": 2,
        "max_sleep_interval": 10,
        # timeout สำหรับ socket
        "socket_timeout": 60,
        # ดาวน์โหลดเป็น chunk เล็กๆ 10MB เพื่อให้ resume ได้ง่าย
        "http_chunk_size": 10 * 1024 * 1024,
    }
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
    else:
        ydl_opts["cookiesfrombrowser"] = ("edge",)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main() -> None:
    auto_update_ytdlp()

    # โหมด CLI: รับ URL จาก argument แล้วจบ
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
        if not url:
            print("URL ว่างเปล่า")
            return
        print("กำลังดาวน์โหลด...")
        try:
            download_video(url)
            print("✅ ดาวน์โหลดเสร็จแล้ว!")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
        return

    # โหมด Interactive (run.bat): วนลูปต่อเนื่องจนกว่าจะกด Ctrl+C
    print("📥 โหมดดาวน์โหลดต่อเนื่อง — กด Ctrl+C เพื่อออก")
    print("-" * 50)
    while True:
        try:
            url = input("\nกรุณาวาง URL: ").strip().removeprefix("\ufeff")
        except KeyboardInterrupt:
            print("\n\n👋 ออกจากโปรแกรมแล้ว")
            break

        if not url:
            print("⚠️  URL ว่างเปล่า กรุณาวาง URL อีกครั้ง")
            continue

        print("กำลังดาวน์โหลด...")
        try:
            download_video(url)
            print("✅ ดาวน์โหลดเสร็จแล้ว! พร้อมสำหรับ URL ถัดไป")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")


if __name__ == "__main__":
    main()

