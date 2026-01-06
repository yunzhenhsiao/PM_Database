import streamlit as st
import pandas as pd
from utils.db_logic import get_db_connection

st.set_page_config(page_title="學員管理系統", page_icon="💼", layout="wide")

# --- 側邊欄與標題 ---
st.title("💼 學員資料管理系統")
st.markdown("---")

# --- 1. 數據統計區 (這部分最能增加專業感) ---
conn = get_db_connection()
try:
    # 取得統計數據
    total_students = pd.read_sql("SELECT COUNT(*) as count FROM students", conn)['count'][0]
    total_courses = pd.read_sql("SELECT COUNT(*) as count FROM course_records", conn)['count'][0]
    total_software = pd.read_sql("SELECT COUNT(*) as count FROM software_purchases", conn)['count'][0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("目前總學員數", f"{total_students} 位", help="系統內所有獨立學員的人數")
    col2.metric("累計上課人次", f"{total_courses} 次", delta=None)
    col3.metric("軟體銷售紀錄", f"{total_software} 筆", delta=None)
except:
    st.warning("資料庫初始化中，暫無數據顯示。")
finally:
    conn.close()

st.markdown("---")
# --- 2. 功能導航區 ---
st.write("### 🔍 查詢與管理")
st.write("快速搜尋學員姓名，查看其完整歷史紀錄。")
if st.button("前往查詢頁面", use_container_width=True):
    st.switch_page("pages/學員檔案查詢.py")

# --- 3. 最近更新紀錄 (選配) ---
st.markdown("---")
st.info("💡 提示：管理員後台需有金鑰才能使用")