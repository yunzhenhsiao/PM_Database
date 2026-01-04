import streamlit as st
import pandas as pd
from utils.db_logic import get_db_connection

st.set_page_config(page_title="學員查詢", page_icon="🔍")
st.title("🔍 學員資料快速查詢")

# 1. 查詢介面
search_name = st.text_input("輸入學員姓名關鍵字：", placeholder="例如：王小明")

if search_name:
    conn = get_db_connection()
    
    # 2. 搜尋學員基本資料 (使用 LIKE 模糊查詢)
    query = "SELECT * FROM students WHERE name LIKE ?"
    search_term = f"%{search_name}%"
    students_df = pd.read_sql(query, conn, params=(search_term,))

    if not students_df.empty:
        for index, student in students_df.iterrows():
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
            course_query = "SELECT course_type, class_name, class_date, rfa_cert_no FROM course_records WHERE student_id = ?"
            courses = pd.read_sql(course_query, conn, params=(student['student_id'],))
            
            if not courses.empty:
                st.dataframe(courses, use_container_width=True)
            else:
                st.info("尚無上課紀錄")

            # 4. 查詢該學員的軟體購買紀錄
            st.subheader("💻 軟體購買紀錄")
            soft_query = "SELECT software_name, purchase_date, plan_type, serial_number FROM software_purchases WHERE student_id = ?"
            softwares = pd.read_sql(soft_query, conn, params=(student['student_id'],))
            
            if not softwares.empty:
                st.dataframe(softwares, use_container_width=True)
            else:
                st.info("尚無軟體購買紀錄")
            
            st.write("---" * 5) # 分隔不同學員
    else:
        st.warning(f"找不到姓名包含 '{search_name}' 的學員。")
    
    conn.close()