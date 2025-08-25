import threading
import time
import subprocess
import sys
import os


def run_main_app():
    """Chạy ứng dụng chính (port 5000)"""
    print("🚀 Đang khởi động ứng dụng chính trên port 5000...")
    subprocess.run([sys.executable, "app.py"])


def run_admin_app():
    """Chạy ứng dụng admin (port 443)"""
    time.sleep(2)  # Đợi 2 giây để main app khởi động trước
    print("🛡️  Đang khởi động admin panel trên port 443...")
    subprocess.run([sys.executable, "admin_app.py"])


if __name__ == "__main__":
    print("=" * 60)
    print("🐾 PET SHOP - MULTI-SERVER LAUNCHER")
    print("=" * 60)
    print("📋 Cấu hình:")
    print("   • Ứng dụng chính (khách hàng): http://localhost:5000")
    print("   • Admin panel: http://localhost:443")
    print("=" * 60)
    print()

    try:
        # Tạo thread cho từng ứng dụng
        main_thread = threading.Thread(target=run_main_app, daemon=True)
        admin_thread = threading.Thread(target=run_admin_app, daemon=True)

        # Khởi động các thread
        main_thread.start()
        admin_thread.start()

        print("✅ Cả hai server đã được khởi động!")
        print("🔄 Nhấn Ctrl+C để dừng tất cả server...")

        # Giữ main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Đang dừng tất cả server...")
        print("👋 Cảm ơn bạn đã sử dụng Pet Shop!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Lỗi khi khởi động: {e}")
        sys.exit(1)