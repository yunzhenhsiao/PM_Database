# 假設這是你的主程式
import pandas as pd
from utils.db_logic import get_db_connection, upsert_student, add_course_record, add_software_record

def process_uploaded_excel(df, data_type):
    """
    df: 已經用 pandas 讀進來的 DataFrame
    data_type: 標記這份 Excel 是 'course' 還是 'software' (你需要自己寫邏輯判斷，或讓使用者選)
    """
    
    conn = get_db_connection()
    
    try:
        # 用迴圈讀取每一列 (Row)
        for index, row in df.iterrows():
            
            phone = str(row.get('手機') or row.get('電話號碼') or '').strip().replace('-', '')
            name = row.get('姓名') or row.get('學員姓名') or row.get('Name')  # 彈性處理
            
            # 2. 基本防呆：如果連名字或手機都沒有，就跳過這一個人
            if not phone or not name or phone == 'None':
                print(f"第 {index+1} 筆資料缺失關鍵欄位，已略過。")
                continue

            # --- 步驟 1: 準備學員資料 (Mapping) ---
            # 這裡就是你發揮的地方：把 Excel 的各種怪欄位名，對應到我們的標準欄位
            student_data = {
                'name': name,
                'phone': phone,
                'company': row.get('公司名稱'),
                'department': row.get('單位'),
                'job_title': row.get('職稱'),
                'line_id': row.get('LINE ID'),
                'email': row.get('電子郵件'),                
                'address': row.get('地址'),
                'tel': str(row.get('電話')).strip(),
            }
            
            # --- 步驟 2: 呼叫資料庫邏輯 (取得 ID) ---
            # 這一行就搞定「舊雨新知」的所有判斷
            current_student_id = upsert_student(conn, student_data)
            
            # --- 步驟 3: 根據檔案類型寫入紀錄 ---
            if data_type == 'course':
                course_data = {
                    'record_id': None,  # 新增不需要 ID
                    'class_name': row.get('班別'),
                    'course_type': 'RFA' if 'RFA' in str(row.get('班別')) else '一般',
                    'rfa_cert_no': row.get('結訓證號') if 'RFA' in str(row.get('班別')) else None,
                    'rfa_training': row.get('持證訓練') if 'RFA' in str(row.get('班別')) else None,
                    'rfa_license_no': row.get('RFA 證號') if 'RFA' in str(row.get('班別')) else None,
                }
                add_course_record(conn, current_student_id, course_data)
                
            elif data_type == 'software':
                raw_date = row.get('購買日期')
                if pd.notnull(raw_date):
                    if hasattr(raw_date, 'strftime'): # 檢查是否有時間格式
                        purchase_date_str = raw_date.strftime('%Y-%m-%d')
                    else:
                        purchase_date_str = str(raw_date)
                else:
                    purchase_date_str = None
                software_data = {
                    'purchase_id': None,  # 新增不需要 ID
                    'software_name': row.get('軟體名稱'),
                    'purchase_date': purchase_date_str if '退休理財顧問系統' in str(row.get('軟體名稱')) else None,
                    'plan_type': row.get('購買方案') if '退休理財顧問系統' in str(row.get('軟體名稱')) else None,
                    'serial_number': row.get('序號') if '退休理財顧問系統' in str(row.get('軟體名稱')) else None,
                }
                add_software_record(conn, current_student_id, software_data)
        
        # 全部跑完再一次 Commit，效率比較高
        conn.commit()
        print("所有資料匯入完成！")
        
    except Exception as e:
        conn.rollback() # 出錯就全部復原，避免只匯入一半
        print(f"匯入失敗，原因：{e}")
        
    finally:
        conn.close()