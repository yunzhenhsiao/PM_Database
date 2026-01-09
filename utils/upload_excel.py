# 假設這是你的主程式
import pandas as pd
from utils.db_logic import get_db_connection, upsert_student, add_course_record, add_software_record

def process_uploaded_excel(df, data_type):
    conn = get_db_connection()
    
    try:
        # --- 【核心修正】將清洗邏輯移到迴圈外，避免 index 錯位 ---
        df = df.where(pd.notnull(df), None)  # 將 NaN 轉為 None
        # 標題也要清洗掉 _x000d_
        df.columns = [str(c).replace('_x000d_', '').replace('\n', '').replace('\r', '').strip() for c in df.columns]
        
        # 用迴圈讀取每一列
        for index, row in df.iterrows():
            # 每一圈開始前重置變數
            student_data = {}

            # --- 欄位清理 (只針對這一列的變數處理) ---
            phone_raw = str(row.get('手機') or row.get('手機號碼') or row.get('電話號碼') or '').strip()
            phone = phone_raw.replace('-', '').replace(' ', '').replace('.0', '')

            if len(phone) == 9 and phone.startswith('9'):
                phone = '0' + phone

            # 彈性處理姓名：確保拿到的不是字串 "None"
            name = row.get('姓名') or row.get('學員姓名') or row.get('Name') or row.get('客戶姓名')
            name = str(name).strip() if name and str(name) != 'None' else None
            
            # 2. 基本防呆：沒名字或手機太短就跳過
            if not name or not phone:
                print(f"第 {index+1} 筆資料關鍵欄位缺失或格式錯誤 ({name}/{phone})，已略過。")
                continue

            # --- 準備學員資料 ---
            student_data = {
                'name': name,
                'phone': phone,
                'company': str(row.get('服務公司') or row.get('服務_公司') or '').strip(),
                'department': str(row.get('通訊處單位') or row.get('通訊處_單位') or '').strip(),
                'job_title': str(row.get('職務職稱') or '').strip(),
                'line_id': str(row.get('LINE ID') or '').strip(),
                'email': str(row.get('EMAIL') or '').strip(),                
                'address': str(row.get('住址') or '').strip(),
                'tel': str(row.get('電話') or '').strip(),
            }
            
            # 取得 ID
            current_student_id = upsert_student(conn, student_data)
            
            # --- 課程/軟體邏輯 ---
            if data_type == 'course':
                cert_no = str(row.get('結訓證號') or '')
                course_data = {
                    'class_name': row.get('參與課程'),
                    'course_type': 'RFA' if 'RFA' in cert_no else '一般',
                    'rfa_cert_no': cert_no if 'RFA' in cert_no else None,
                    'rfa_license_no': str(row.get('認證號碼') or '') if 'RFA' in cert_no else None,
                }
                add_course_record(conn, current_student_id, course_data)
                
            elif data_type == 'software':
                order_item = str(row.get('訂購項目') or '')
                status = str(row.get('訂單狀態') or '')
                
                if status in ['轉讓', '取消']:
                    print(f"第 {index+1} 筆資料為{status}訂單，已略過。")
                    continue

                raw_date = row.get('購買日期')
                # 簡單日期處理
                p_date = str(raw_date)[:10] if raw_date and str(raw_date) != 'None' else None

                software_data = {
                    'software_name': order_item,
                    'purchase_date': p_date if '退休理財顧問系統' in order_item else None,
                    'plan_type': row.get('購買方案') if '退休理財顧問系統' in order_item else None,
                    'serial_number': row.get('序號') if '退休理財顧問系統' in order_item else None,
                }
                add_software_record(conn, current_student_id, software_data)
        
        conn.commit()
        print("所有資料匯入完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"匯入失敗，原因：{e}")
    finally:
        conn.close()