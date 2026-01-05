import sqlite3
import os

# 設定資料庫檔案名稱
DB_NAME = 'crm.db'

def create_database():
    # 1. 建立連線 (如果檔案不存在，它會自動建立一個新的)
    conn = sqlite3.connect(DB_NAME)
    
    # 2. 建立游標 (Cursor)，這是用來執行 SQL 指令的工具
    cursor = conn.cursor()

    # 3. 啟用外鍵約束 (SQLite 預設有時會關閉，開啟比較安全)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- 定義 SQL 語法 ---

    # 表 1: 學員主表 (Students)
    # phone 我們設為 TEXT，方便存 09 開頭的號碼
    sql_create_students = """
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT, 
        company TEXT,
        department TEXT,
        job_title TEXT,
        line_id TEXT,
        email TEXT,
        address TEXT,
        tel TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 表 2: 上課紀錄表 (Course Records)
    # FOREIGN KEY (student_id) REFERENCES students (student_id) -> 綁定關係
    sql_create_courses = """
    CREATE TABLE IF NOT EXISTS course_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_type TEXT, 
        class_name TEXT,
        rfa_cert_no TEXT,
        rfa_training TEXT,
        rfa_license_no TEXT,
        FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
    );
    """

    # 表 3: 軟體購買紀錄 (Software Purchases)
    sql_create_software = """
    CREATE TABLE IF NOT EXISTS software_purchases (
        purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        software_name TEXT,
        purchase_date TEXT,
        plan_type TEXT,
        serial_number TEXT,
        FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE
    );
    """

    # 4. 執行 SQL 指令
    try:
        print("正在建立 'students' 表...")
        cursor.execute(sql_create_students)
        
        print("正在建立 'course_records' 表...")
        cursor.execute(sql_create_courses)
        
        print("正在建立 'software_purchases' 表...")
        cursor.execute(sql_create_software)
        
        # 5. 提交變更 (Commit) - 這步沒做，資料庫不會真的存檔
        conn.commit()
        print(f"成功！資料庫 {DB_NAME} 已建立完成。")
        
    except Exception as e:
        print(f"發生錯誤：{e}")
        conn.rollback() # 如果出錯，回復到原本狀態
        
    finally:
        # 6. 關閉連線 (好習慣)
        conn.close()

if __name__ == '__main__':
    # 如果資料庫已存在，這行可以先刪除舊的重新來過 (測試階段可以用，正式上線要小心)
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("已刪除舊資料庫")

    create_database()