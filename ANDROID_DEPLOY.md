# Hướng dẫn Cập nhật Bot trên Android (Termux)

Bạn muốn **loại bỏ bản cũ** và chạy bản mới nhất với cấu trúc "khoa học" vừa làm.

### Bước 1: Dừng Bot cũ
- Mở Termux.
- Nếu bot đang chạy, nhấn `Ctrl + C` để dừng.

### Bước 2: Cập nhật Code (Khuyên dùng Git)
Nếu bạn đã cài qua Git (GitHub), hãy chạy lệnh sau để lấy code mới và xóa sạch file thừa cũ:

```bash
cd ~/discord_bot
git fetch --all
git reset --hard origin/main
```
*Lệnh này sẽ làm cho thư mục trên điện thoại giống hệt trên máy tính của bạn.*

*(Nếu bạn cài thủ công không qua Git: Hãy xóa thư mục cũ `rm -rf ~/discord_bot`, tạo lại và copy file `main.py` cùng các thư mục `bot`, `config`, `database`, `scraper` sang).*

### Bước 3: Khôi phục Dữ liệu (Quan trọng)
Vì lệnh `git reset --hard` có thể không ảnh hưởng file không được track (như `.env` và `schedule.db`), nhưng để chắc chắn:
- Kiểm tra file cấu hình: `cat .env` (Nếu mất thì tạo lại).
- Database `schedule.db` sẽ được giữ nguyên nếu nó nằm trong `.gitignore` (nhưng thường ta track schema, data thì local). Nếu bạn lỡ xóa thì bot sẽ tạo lại DB mới.

### Bước 4: Chạy Bot mới
Cấu trúc mới vẫn chạy từ `main.py` nhưng gọn hơn nhiều.

```bash
# Kích hoạt môi trường ảo (nếu có)
source venv/bin/activate 

# Cài lại thư viện (để đảm bảo không thiếu gì)
pip install -r requirements.txt

# Chạy bot
python main.py
```

### 💡 Lưu ý
- Nếu gặp lỗi `ModuleNotFoundError`, hãy chắc chắn bạn đã chạy `pip install` ở Bước 4.
- Lệnh `!schoolsetup` và `!mailnew` vẫn hoạt động bình thường, dữ liệu cũ trong `schedule.db` vẫn còn (trừ khi bạn xóa file db).

