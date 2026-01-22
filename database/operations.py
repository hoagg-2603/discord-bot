import sqlite3
from database.db import get_connection
from datetime import datetime


def save_user(discord_id, student_code, password=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if updating or inserting
        if password:
            cursor.execute("""
                INSERT INTO users (discord_id, student_code, password_encrypted, last_sync)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET
                student_code=excluded.student_code,
                password_encrypted=excluded.password_encrypted,
                last_sync=excluded.last_sync
            """, (str(discord_id), student_code, password, datetime.now()))
        else:
            # If password not provided, don't overwrite it (preserve existing)
             cursor.execute("""
                INSERT INTO users (discord_id, student_code, last_sync)
                VALUES (?, ?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET
                student_code=excluded.student_code,
                last_sync=excluded.last_sync
            """, (str(discord_id), student_code, datetime.now()))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False
    finally:
        conn.close()

def get_users():
    """
    Returns list of users with their credentials.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT discord_id, student_code, password_encrypted FROM users")
        rows = cursor.fetchall()
        users = []
        for r in rows:
            users.append({
                "discord_id": r[0],
                "student_code": r[1],
                "password": r[2]
            })
        return users
    finally:
        conn.close()


def save_schedule(discord_id, schedule_data):
    """
    Parses the JSON data from scraper and saves to DB.
    schedule_data: The list of weeks or the root object containing 'ds_tuan_tkb'
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Handle structure variations
    weeks = []
    if isinstance(schedule_data, dict):
        weeks = schedule_data.get('ds_tuan_tkb', [])
    elif isinstance(schedule_data, list):
         # It might be the list of weeks directly
         weeks = schedule_data
         
    print(f"Saving schedule for {discord_id}. Found {len(weeks)} weeks.")
    
    try:
        # We might want to clear old future schedules or just upsert based on unique_id
        # For now, let's upsert.
        
        count = 0
        for week in weeks:
            for class_session in week.get('ds_thoi_khoa_bieu', []):
                # Extract fields
                subject_code = class_session.get('ma_mon')
                subject_name = class_session.get('ten_mon')
                class_code = class_session.get('ma_lop')
                teacher = class_session.get('ten_giang_vien')
                room = class_session.get('ma_phong')
                period_start = class_session.get('tiet_bat_dau')
                period_count = class_session.get('so_tiet')
                
                # Date parsing: "2026-01-12T00:00:00" -> "2026-01-12"
                raw_date = class_session.get('ngay_hoc', '')
                date_str = raw_date.split('T')[0] if raw_date else ''
                
                # Unique ID for deduplication
                # discord_id + subject_code + date + period_start
                unique_id = f"{discord_id}_{subject_code}_{date_str}_{period_start}"
                
                cursor.execute("""
                    INSERT INTO schedules (
                        user_id, subject_name, subject_code, class_code, 
                        teacher, room, date, period_start, period_count, unique_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET -- Wait, we need a unique constraint on unique_id or just insert?
                    -- SQLite doesn't strictly enforce unique unless defined.
                    -- Let's check existence first or use unique index.
                    subject_name=excluded.subject_name,
                    teacher=excluded.teacher,
                    room=excluded.room
                """, (
                    discord_id, subject_name, subject_code, class_code,
                    teacher, room, date_str, period_start, period_count, unique_id
                ))
                
                # Actually, standard INSERT OR REPLACE or upsert requires a unique index.
                # Let's add logic: check if exists by unique criteria (user + date + period)
                
                # Better approach: Delete existing for this User + Date + Period? 
                # Or just rely on the fact that we can clean up old data?
                
                # Let's fix the INSERT above. It's standard insert. 
                # If we want to avoid duplicates, we should check.
                
                # Check for duplicate
                cursor.execute("""
                    SELECT id FROM schedules 
                    WHERE user_id = ? AND date = ? AND period_start = ? AND subject_code = ?
                """, (discord_id, date_str, period_start, subject_code))
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    cursor.execute("""
                        UPDATE schedules SET
                        subject_name=?, teacher=?, room=?, period_count=?, unique_id=?
                        WHERE id = ?
                    """, (subject_name, teacher, room, period_count, unique_id, existing[0]))
                else:
                    # Insert
                    cursor.execute("""
                        INSERT INTO schedules (
                            user_id, subject_name, subject_code, class_code, 
                            teacher, room, date, period_start, period_count, unique_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        discord_id, subject_name, subject_code, class_code,
                        teacher, room, date_str, period_start, period_count, unique_id
                    ))
                count += 1
                
        conn.commit()
        print(f"Saved/Updated {count} class sessions.")
    except Exception as e:
        print(f"Error saving schedule: {e}")
        # conn.rollback() # optional handling
    finally:
        conn.close()

def get_schedule_by_date(discord_id, target_date):
    """
    Get schedule for a specific date (YYYY-MM-DD)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # We query by date. Note: user_id logic needs refinement if multiple users.
        # For now, we query ALL schedules for that date (assuming single user bot)
        # OR query by specific user if we had the mapping. 
        # Since we saved with "global_bot_user", let's just query by date for now.
        
        cursor.execute("""
            SELECT subject_name, room, period_start, period_count, teacher
            FROM schedules 
            WHERE date = ? 
            ORDER BY period_start ASC
        """, (target_date,))
        
        rows = cursor.fetchall()
        return [
            {
                "subject": r[0],
                "room": r[1],
                "start": r[2],
                "count": r[3],
                "teacher": r[4]
            }
            for r in rows
        ]
    # ... (existing get_schedule_by_date code) ...
    finally:
        conn.close()

def get_upcoming_classes(minutes_window=60):
    """
    Find classes starting within the next `minutes_window` minutes.
    Returns list of dicts.
    """
    from datetime import datetime, timedelta
    from utils.time_utils import PERIOD_START_TIME
    
    # Current time in System Local Time (Assuming Server/Phone is correct or we adjusting)
    # User said "sync with Vietnam clock".
    # Termux/Android usually follows system time. 
    # If VPS, ensure TZ=Asia/Ho_Chi_Minh or handle offset.
    # Safe way: datetime.now() if system is correct.
    
    now = datetime.now()
    
    # We look for classes TODAY
    today_str = now.strftime("%Y-%m-%d")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    upcoming = []
    
    try:
        # Get all classes for today
        cursor.execute("""
            SELECT user_id, subject_name, room, period_start, teacher
            FROM schedules
            WHERE date = ?
        """, (today_str,))
        
        rows = cursor.fetchall()
        
        for row in rows:
            user_id, subject, room, p_start, teacher = row
            
            # Get start time string "HH:MM"
            start_time_str = PERIOD_START_TIME.get(p_start)
            if not start_time_str:
                continue
                
            # Create datetime for this class start
            # Format: YYYY-MM-DD HH:MM
            class_dt_str = f"{today_str} {start_time_str}:00"
            class_dt = datetime.strptime(class_dt_str, "%Y-%m-%d %H:%M:%S")
            
            # Calculate difference
            # upcoming means: now < class_dt <= now + window
            # But user wants "remind 1 hour before".
            # Means if class is at 8:00, remind at 7:00.
            # So if (class_dt - now) is between 55 and 65 minutes (approx 1 hour).
            # Or just "Is class starting in [0, 60] minutes?"
            
            delta = class_dt - now
            minutes_diff = delta.total_seconds() / 60
            
            # Condition: Class is in the future AND within window
            # Let's say we check every 5 mins.
            # We want to catch it when minutes_diff is around 60.
            # Range: 50 < minutes_diff <= 65 ?
            
            if 45 <= minutes_diff <= 75: # Broad window to catch "1 hour before", run job every 15-30m
                upcoming.append({
                    "user_id": user_id,
                    "subject": subject,
                    "room": room,
                    "time": start_time_str,
                    "minutes_left": int(minutes_diff),
                    "start_period": p_start
                })
                
    finally:
        conn.close()
        
    return upcoming


def add_gmail_account(user_id, email, app_password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO gmail_accounts (user_id, email, app_password, last_checked)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, email) DO UPDATE SET
            app_password=excluded.app_password
        """, (str(user_id), email, app_password, datetime.now()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding gmail account: {e}")
        return False
    finally:
        conn.close()

def get_gmail_accounts(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if user_id:
            cursor.execute("""
                SELECT email, app_password, last_checked FROM gmail_accounts WHERE user_id = ?
            """, (str(user_id),))
        else:
            cursor.execute("""
                SELECT email, app_password, last_checked, user_id FROM gmail_accounts
            """)
        
        rows = cursor.fetchall()
        accounts = []
        for r in rows:
            acc = {
                "email": r[0],
                "app_password": r[1],
                "last_checked": r[2]
            }
            if len(r) > 3:
                acc["user_id"] = r[3]
            accounts.append(acc)
        return accounts
    finally:
        conn.close()

def delete_gmail_account(user_id, email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM gmail_accounts WHERE user_id = ? AND email = ?
        """, (str(user_id), email))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
