from datetime import datetime, timedelta

# Mapping Period -> Start Hour (Int)
# Tiết 1 bắt đầu lúc 7:00
# Mỗi tiết 50p + 10p nghỉ?
# User request: "tiết 1-2 là từ 7 đến 8 giờ" -> Tiết 1 bắt đầu 7h, Tiết 2 bắt đầu 8h?
# Hay Tiết 1-2 (cặp tiết) là 7h-9h?
# Theo quy chuẩn phổ biến ĐH ở VN:
# Sáng:
# Tiết 1: 7:00
# Tiết 2: 8:00 (hoặc 7:50)
# Tiết 3: 9:00
# ...
# Chiều:
# Tiết 7: 13:00 (hoặc 12:30)
# ...

# User nói: "tiết 1-2 là từ 7 đến 8 giờ" -> Có vẻ tiết 1 bắt đầu 7:00, tiết 2 bắt đầu 8:00 (nếu "đến 8 giờ" nghĩa là xong lúc 8h thì tiết 1 chỉ 1 tiếng?).
# Giả sử tiết bắt đầu vào các khung giờ chẵn cho đơn giản theo ý user, hoặc chuẩn PTIT.
# PTIT: 
# Kíp 1 (Tiết 1-2): 7h00 - 8h50 (Nghỉ giải lao giữa giờ)
# Kíp 2 (Tiết 3-4): 9h00 - 10h50
# Kíp 3 (Tiết 5-6): 12h00 - 13h50 (ít học) hoặc 13h00?
# Chuẩn PTIT (Thường):
# Tiết 1: 07:00
# Tiết 2: 08:00
# Tiết 3: 09:00
# Tiết 4: 10:00
# ...
# Tiết 7: 13:00
# Tiết 8: 14:00
# ...

PERIOD_START_TIME = {
    1: "07:00",
    2: "08:00",
    3: "09:00",
    4: "10:00",
    5: "11:00", # Ít học
    6: "12:00", # Ít học
    7: "13:00",
    8: "14:00",
    9: "15:00",
    10: "16:00",
    11: "17:00",
    12: "18:00", 
    13: "19:00" # Tối
}

def get_period_time(period_start):
    """Returns datetime object for start of the period today or specified string"""
    # Trả về chuỗi HH:MM
    return PERIOD_START_TIME.get(period_start, "00:00")

def is_upcoming(class_date, period_start, minutes_alert=60):
    """
    Check if a class is happening in ~minutes_alert.
    class_date: "YYYY-MM-DD"
    period_start: int
    """
    # Logic will be handled in ops
    pass
