import sqlite3

DB_NAME = 'crm.db'

def get_db_connection():
    """建立資料庫連線"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 讓我們可以用欄位名稱存取資料
    return conn

# ==========================================
# 核心函數 1: 處理學員 (Upsert: Update or Insert)
# ==========================================
def upsert_student(conn, student_data):
    """
    輸入: student_data (字典), 包含 name, phone, company 等
    輸出: student_id (整數)
    邏輯: 用 phone 檢查，有則更新並回傳 ID，無則新增並回傳新 ID
    """
    cursor = conn.cursor()
    
    # 1. 必填檢查 (手機是我們的 Unique Key)
    phone = student_data.get('phone')
    if not phone:
        raise ValueError("學員資料必須包含 'phone' 欄位")

    # 2. 檢查學員是否存在
    cursor.execute("SELECT student_id FROM students WHERE phone = ?", (phone,))
    result = cursor.fetchone()

    if result:
        # --- 情境 A: 老學員 (Found) -> 執行 UPDATE ---
        student_id = result['student_id']
        # 這裡我們更新除了 id 和 phone 以外的欄位，確保資料是最新的
        # (你可以根據需求決定是否要覆蓋舊資料，這裡假設以新上傳的為準)
        sql_update = """
        UPDATE students 
        SET name=?, company=?, department=?, job_title=?, line_id=?, email=?, address=?, tel=?
        WHERE student_id=?
        """
        cursor.execute(sql_update, (
            student_data.get('name'),
            student_data.get('company'),
            student_data.get('department'),
            student_data.get('job_title'),
            student_data.get('line_id'),
            student_data.get('email'),
            student_data.get('address'),
            student_data.get('tel'),
            student_id
        ))
        print(f"學員 {student_data.get('name')} 資料已更新 (ID: {student_id})")
        
    else:
        # --- 情境 B: 新學員 (Not Found) -> 執行 INSERT ---
        sql_insert = """
        INSERT INTO students (name, phone, company, department, job_title, line_id, email, address, tel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_insert, (
            student_data.get('name'),
            phone,
            student_data.get('company'),
            student_data.get('department'),
            student_data.get('job_title'),
            student_data.get('line_id'),
            student_data.get('email'),
            student_data.get('address'),
            student_data.get('tel')
        ))
        student_id = cursor.lastrowid # 取得剛剛新增的那筆資料的 ID
        print(f"新學員 {student_data.get('name')} 已建立 (ID: {student_id})")

    return student_id

# ==========================================
# 核心函數 2: 新增課程紀錄
# ==========================================
def add_course_record(conn, student_id, course_data):
    """
    輸入: student_id, course_data (字典: class_name, type, rfa_info...)
    """
    cursor = conn.cursor()
    
    # 為了避免重複匯入同一堂課 (例如爸爸不小心上傳兩次一樣的 Excel)
    # 我們可以檢查: 同一個人 + 同一個班別 是否已經存在
    check_sql = "SELECT record_id FROM course_records WHERE student_id=? AND class_name=?"
    cursor.execute(check_sql, (student_id, course_data.get('class_name')))
    if cursor.fetchone():
        print(f"  -> 略過：學員 ID {student_id} 已經有 '{course_data.get('class_name')}' 的紀錄了")
        return

    sql = """
    INSERT INTO course_records (student_id, course_type, class_name, rfa_cert_no, rfa_training, rfa_license_no)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (
        student_id,
        course_data.get('course_type', '一般'), # 預設為一般
        course_data.get('class_name'),
        course_data.get('rfa_cert_no'),
        course_data.get('rfa_training'),
        course_data.get('rfa_license_no')
    ))
    print(f"  -> 新增課程紀錄成功：{course_data.get('class_name')}")

# ==========================================
# 核心函數 3: 新增軟體購買紀錄
# ==========================================
def add_software_record(conn, student_id, software_data):
    """
    輸入: student_id, software_data (字典)
    """
    cursor = conn.cursor()
    
    # 同樣檢查是否重複 (同一個人 + 同一個軟體 + 同一個購買日/序號)
    check_sql = "SELECT purchase_id FROM software_purchases WHERE student_id=? AND serial_number=?"
    # 如果沒有序號，可以用軟體名稱+日期來檢查，這邊先示範用序號檢查
    if software_data.get('serial_number') and software_data.get('software_name') == '退休理財顧問系統':
        cursor.execute(check_sql, (student_id, software_data.get('serial_number')))
        if cursor.fetchone():
            print(f"  -> 略過：序號 {software_data.get('serial_number')} 已存在")
            return
    else:
        # 如果不是退休理財顧問系統，或沒有序號，可以用軟體名稱+購買日期來檢查
        check_sql = "SELECT purchase_id FROM software_purchases WHERE student_id=? AND software_name=?"
        cursor.execute(check_sql, (student_id, software_data.get('software_name')))
        if cursor.fetchone():
            print(f"  -> 略過：軟體 {software_data.get('software_name')} 已存在")
            return

    sql = """
    INSERT INTO software_purchases (student_id, software_name, purchase_date, plan_type, serial_number)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (
        student_id,
        software_data.get('software_name'),
        software_data.get('purchase_date'),
        software_data.get('plan_type'),
        software_data.get('serial_number')
    ))
    print(f"  -> 新增軟體紀錄成功：{software_data.get('software_name')}")