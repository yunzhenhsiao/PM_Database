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
    cursor = conn.cursor()
    
    # 取得並清理基本資訊
    phone = student_data.get('phone')
    name = student_data.get('name')
    company = student_data.get('company')
    email = student_data.get('email')
    address = student_data.get('address')

    result = None
    match_method = "" # 用來追蹤是怎麼找到人的

    # --- 步驟 1: 優先用手機找 ---
    if phone and phone not in ['None', 'nan', '']:
        cursor.execute("SELECT student_id FROM students WHERE phone = ?", (phone,))
        result = cursor.fetchone()
        if result: match_method = "手機配對"

    # --- 步驟 2: 如果沒手機或沒對到，開始多層次配對 ---
    if not result and name:
        # 2-1. 姓名 + EMAIL
        if email and email not in ['None', 'nan', '']:
            cursor.execute("SELECT student_id FROM students WHERE name = ? AND email = ?", (name, email))
            result = cursor.fetchone()
            if result: match_method = "姓名+EMAIL配對"
        
        # 2-2. 如果還沒對到，嘗試 姓名 + 住址
        if not result and address and address not in ['None', 'nan', '']:
            cursor.execute("SELECT student_id FROM students WHERE name = ? AND address = ?", (name, address))
            result = cursor.fetchone()
            if result: match_method = "姓名+住址配對"
            
        # 2-3. 如果還沒對到，嘗試 姓名 + 公司
        if not result and company and company not in ['None', 'nan', '']:
            cursor.execute("SELECT student_id FROM students WHERE name = ? AND company = ?", (name, company))
            result = cursor.fetchone()
            if result: match_method = "姓名+公司配對"

    # --- 步驟 3: 判斷結果 (更新或新增) ---
    if result:
        student_id = result['student_id']
        # 執行非空更新邏輯...
        update_fields = []
        params = []
        fields_to_check = ['phone', 'company', 'department', 'job_title', 'line_id', 'email', 'address', 'tel']        
        for field in fields_to_check:
            val = student_data.get(field)
            if val and str(val).lower() not in ['nan', 'none', '']:
                update_fields.append(f"{field} = ?")
                params.append(val)
        
        if update_fields:
            params.append(student_id)
            sql_update = f"UPDATE students SET {', '.join(update_fields)} WHERE student_id = ?"
            cursor.execute(sql_update, params)
            print(f"  [舊學員] 姓名: {name} (ID: {student_id}) - 通過 {match_method} 找到並更新。")
        return student_id
    else:
        # --- 情境 B: 全部配對失敗 -> 執行 INSERT ---
        sql_insert = """
        INSERT INTO students (name, phone, company, department, job_title, line_id, email, address, tel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_insert, (
            name, phone, company, 
            student_data.get('department'),
            student_data.get('job_title'),
            student_data.get('line_id'),
            student_data.get('email'),
            student_data.get('address'),
            student_data.get('tel')
        ))
        new_id = cursor.lastrowid
        # 輸出到終端機供檢查
        print(f"  [新學員] 姓名: {name} - 無法通過手機/Email/地址/公司配對，已建立新資料 (ID: {new_id})")
        return new_id

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
    INSERT INTO course_records (student_id, course_type, class_name, rfa_cert_no, rfa_license_no)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (
        student_id,
        course_data.get('course_type', '一般'), # 預設為一般
        course_data.get('class_name'),
        course_data.get('rfa_cert_no'),
        course_data.get('rfa_license_no')
    ))
    print(f"  -> 新增課程紀錄成功：{course_data.get('class_name')}")

# ==========================================
# 核心函數 3: 新增軟體購買紀錄
# ==========================================
def add_software_record(conn, student_id, software_data):
    cursor = conn.cursor()
    
    # 取得當前要匯入的軟體名稱
    current_name = software_data.get('software_name')
    current_serial = software_data.get('serial_number')

    # --- 邏輯 A：如果有序號，用序號當唯一標記 (最精準) ---
    if current_serial:
        check_sql = "SELECT purchase_id FROM software_purchases WHERE student_id=? AND serial_number=?"
        cursor.execute(check_sql, (student_id, current_serial))
        if cursor.fetchone():
            print(f"  -> 略過：學員 {student_id} 之序號 {current_serial} 已存在")
            return
            
    # --- 邏輯 B：沒有序號或非序號制軟體 (用「完整名字」+「購買日期」) ---
    else:
        # 資管系保險寫法：我們同時比對 名字 + 日期 + 方案，全部一樣才叫重複
        # 如果你其中一個沒資料也沒關係，None = None 在 SQL 中也是一種比對
        check_sql = """
            SELECT purchase_id FROM software_purchases 
            WHERE student_id = ? 
            AND software_name IS ? 
            AND purchase_date IS ?
            AND plan_type IS ?
            AND serial_number IS ?
        """
        cursor.execute(check_sql, (
            student_id, 
            current_name, 
            software_data.get('purchase_date'),
            software_data.get('plan_type'),
            software_data.get('serial_number')
        ))
        
        if cursor.fetchone():
            print(f"  -> 略過：學員 {student_id} 已有相同的 {current_name} 紀錄")
            return

    # --- 執行新增 ---
    sql = """
    INSERT INTO software_purchases (student_id, software_name, purchase_date, plan_type, serial_number)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (
        student_id,
        current_name,
        software_data.get('purchase_date'),
        software_data.get('plan_type'),
        current_serial
    ))
    print(f"  -> 新增軟體紀錄成功：{software_data.get('software_name')}")