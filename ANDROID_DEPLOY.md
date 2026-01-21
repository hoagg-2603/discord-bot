# Hướng dẫn Cài đặt Bot trên Android (Termux)

Bạn đã vào được Ubuntu (`root@localhost`). Bây giờ hãy chạy lần lượt các nhóm lệnh sau:

## 1. Cập nhật và Cài đặt Python + Git
Copy và chạy lệnh này để cài các công cụ cơ bản:
```bash
apt update && apt upgrade -y
apt install python3 python3-pip git nano -y
```

## 2. Kéo Code Bot về máy
Chúng ta sẽ clone code từ máy tính của bạn hoặc tạo mới.
*Cách dễ nhất là tạo thư mục và copy file, nhưng để chuyên nghiệp, ta sẽ giả lập tạo mới.*

```bash
# Tạo thư mục
mkdir discord_bot
cd discord_bot
```

**LƯU Ý**: Vì code đang ở trên PC của bạn, bạn cần **Copy** nội dung file `main.py`, `database/`, `scraper/`, `.env` sang điện thoại.
*   **Cách 1 (Thủ công)**: Dùng lệnh `nano main.py` -> Copy code từ PC -> Paste vào Termux -> Bấm `Ctrl+X` -> `Y` -> `Enter` để lưu.
*   **Cách 2 (Git)**: Nếu bạn đã đẩy code lên GitHub, chỉ cần `git clone <link_repo>`.

*(Giả sử bạn sẽ copy file bằng cách thủ công hoặc dùng Git. Dưới đây là bước cài thư viện)*

## 3. Cài đặt Thư viện cho Bot
```bash
# Tạo môi trường ảo (khuyên dùng để tránh lỗi hệ thống)
python3 -m venv venv
source venv/bin/activate

# Cài các thư viện cần thiết
pip install discord.py python-dotenv apscheduler playwright pydantic python-dateutil
```

## 4. Cài đặt Playwright (Quan trọng)
Playwright cần tải trình duyệt riêng để chạy được trên điện thoại:
```bash
playwright install chromium
playwright install-deps
```
*Lưu ý: Bước này sẽ tốn dung lượng và thời gian khá lâu.*

## 5. Chạy Bot
Trước khi chạy, hãy chắc chắn bạn đã tạo file `.env` chứa Token.
```bash
# Tạo file .env nếu chưa có
nano .env
# (Dán nội dung: DISCORD_TOKEN=... SCHOOL_USERNAME=... SCHOOL_PASSWORD=...)
# Lưu lại: Ctrl+X -> Y -> Enter
```

Chạy bot:
```bash
python3 main.py
```

## Mẹo treo 24/7 trên điện thoại
- Sau khi bot chạy, **đừng tắt ứng dụng Termux**.
- Hãy gạt thanh thông báo xuống, tìm thông báo của Termux và chọn "Acquire wakelock" (Giữ máy thức) để Android không tự động giết ứng dụng khi tắt màn hình.
