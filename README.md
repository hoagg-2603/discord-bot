# Hướng dẫn Sử dụng Bot Lịch Học

Bot đã được hoàn thiện với các tính năng:
1.  **Tự động lấy lịch**: Quét lịch từ `qldt.ptit.edu.vn` lúc 00:00 và 12:00 hàng ngày.
2.  **Lưu trữ**: Dữ liệu được lưu trong SQLite (`schedule.db`).
3.  **Lệnh Discord**:
    - `!ping`: Kiểm tra bot còn sống không.
    - `!ping`: Kiểm tra bot còn sống không.
    - `!ping`: Kiểm tra bot còn sống không.
    - `!force_sync`: Bắt buộc bot quét dữ liệu ngay lập tức.
    - `!tkb [homnay|mai|ngày]`: Xem thời khóa biểu. 
      - Ví dụ: `!tkb` (hôm nay), `!tkb mai`, `!tkb 22012026`, `!tkb 2026-01-22`.

## Mời Bot vào Server (Discord Invite)
Để thêm bot vào server của bạn, bạn cần lấy link mời từ Developer Portal:
1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications).
2. Chọn App của bạn -> Menu trái chọn **OAuth2** -> **URL Generator**.
3. Phần **SCOPES**: Tích chọn `bot`.
4. Phần **BOT PERMISSIONS**: Tích chọn:
   - `Read Messages/View Channels`
   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
   - `Read Message History`
5. Copy đường dẫn ở cuối trang (Generated URL) và dán vào trình duyệt để mời bot.

## Cách chạy Bot

1.  **Kích hoạt môi trường ảo** (nếu chưa):
    ```bash
    .\venv\Scripts\activate
    ```

2.  **Chạy Bot**:
    ```bash
    python main.py
    ```

## Kiểm tra hoạt động
- Khi chạy thành công, cửa sổ console sẽ hiện:
  ```
  Logged in as [Tên Bot] (ID: ...)
  Scheduler started (00:00 and 12:00 scan configured).
  ```
- Vào Discord gõ `!ping` để thử.

## Cấu trúc dữ liệu
- File Database: `schedule.db` (được tạo tự động tại thư mục gốc).
- File Log mạng (debug): `scraper/*.log` (nếu có).

## Lưu ý
- Bot chạy trình duyệt ẩn (headless) để lấy dữ liệu. Đừng tắt cửa sổ console khi bot đang chạy.
- Nếu đổi mật khẩu trường, hãy cập nhật lại file `.env`.
