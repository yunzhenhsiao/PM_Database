import streamlit as st
import pandas as pd
from utils.db_logic import get_db_connection

st.set_page_config(page_title="學員查詢", page_icon="🔍")
st.title("🔍 學員資料快速查詢")

# 1. 查詢介面
search_name = st.text_input("輸入學員姓名關鍵字：", placeholder="例如：王小明")

conn = get_db_connection()
if search_name:
    
    query = """
    SELECT * FROM students 
    WHERE name LIKE ? OR phone LIKE ? 
    LIMIT 100
    """
    # 加上 LIMIT 100 是保護機制，避免像搜尋「陳」結果跑出 2000 個人把瀏覽器灌爆
    params = (f"%{search_name}%", f"%{search_name}%")
    df = pd.read_sql(query, conn, params=params)
    
    if not df.empty:
        st.success(f"找到 {len(df)} 筆資料")
        st.dataframe(df)
        for index, student in df.iterrows():
            st.markdown(f"### 👤 學員：{student['name']}")
            
            # 用 Columns 佈局顯示基本資料，看起來比較專業
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**公司：** {student['company']}")
                st.write(f"**單位：** {student['department']}")
            with col2:
                st.write(f"**手機：** {student['phone']}")
                st.write(f"**LINE：** {student['line_id']}")
            with col3:
                st.write(f"**職稱：** {student['job_title']}")
                st.write(f"**地址：** {student['address']}")

            # 3. 查詢該學員的課程紀錄
            st.write("---")
            st.subheader("📚 上課歷史紀錄")
            course_query = "SELECT course_type, class_name, rfa_cert_no, rfa_license_no FROM course_records WHERE student_id = ?"
            courses = pd.read_sql(course_query, conn, params=(student['student_id'],))
            
            if not courses.empty:
                # 定義中文標題對照表
                course_mapping = {
                    'course_type': '課程類別',
                    'class_name': '上課班別',
                    'rfa_cert_no': '結訓證號',
                    'rfa_license_no': '認證號碼'
                }
                # 1. 重新命名欄位 2. 將 None 轉為 "-" 讓介面更美觀
                display_courses = courses.rename(columns=course_mapping).fillna("-")
                # hide_index=True 隱藏最左邊的 0, 1, 2
                st.dataframe(display_courses, use_container_width=True, hide_index=True)
            else:
                st.info("尚無上課紀錄")

            # 4. 查詢該學員的軟體購買紀錄
            st.subheader("💻 軟體購買紀錄")
            soft_query = "SELECT software_name, purchase_date, plan_type, serial_number FROM software_purchases WHERE student_id = ?"
            softwares = pd.read_sql(soft_query, conn, params=(student['student_id'],))
            
            if not softwares.empty:
                # 定義中文標題對照表
                soft_mapping = {
                    'software_name': '訂購項目',
                    'purchase_date': '購買日期',
                    'plan_type': '方案類型',
                    'serial_number': '使用序號'
                }
                # 1. 重新命名欄位 2. 將 None 轉為 "-"
                display_softwares = softwares.rename(columns=soft_mapping).fillna("-")
                st.dataframe(display_softwares, use_container_width=True, hide_index=True)
            else:
                st.info("尚無軟體購買紀錄")
            
            st.write("---" * 5) # 分隔不同學員
    else:
        st.warning("找不到相符的學員")

else:
    # --- 沒搜尋時：只顯示最新 20 筆 (預覽模式) ---
    st.info("請輸入關鍵字進行查詢。以下顯示最新加入的 20 位學員：")
    query = "SELECT * FROM students ORDER BY student_id DESC LIMIT 20"
    df = pd.read_sql(query, conn)
    st.dataframe(df)