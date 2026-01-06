import streamlit as st
import pandas as pd
import os
from utils.upload_excel import process_uploaded_excel

st.set_page_config(page_title="管理員後台", page_icon="🔐")

# --- 簡單的身分驗證 ---
ADMIN_PASSWORD = "1222" # 這裡改掉，不要讓爸爸猜到

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("請輸入管理員金鑰以開啟匯入功能：", type="password")
    if st.button("登入"):
        if pw == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("金鑰錯誤！")
    st.stop() # 未驗證則停止執行後續代碼

# --- 驗證成功後的內容 ---
st.title("🔐 管理員資料更新中心")

tab1, tab2 = st.tabs(["📊 匯入 Excel 資料", "💾 同步資料庫檔案"])

with tab1:
    st.subheader("從 Excel 批次新增紀錄")
    upload_type = st.radio("選擇匯入類型", ("course", "software"))
    uploaded_xlsx = st.file_uploader("選擇要匯入的 Excel (.xlsx)", type=['xlsx'])

    if uploaded_xlsx and st.button("執行 Excel 匯入"):
        df = pd.read_excel(uploaded_xlsx)
        df = df.where(pd.notnull(df), None)
        with st.spinner('處理中...'):
            try:
                process_uploaded_excel(df, data_type=upload_type)
                st.success("Excel 數據已成功寫入 crm.db！")
                
                # 在 pages/管理員後台.py 匯入成功後的地方加上：
                with open("crm.db", "rb") as f:
                    st.download_button(
                        label="📥 下載最新的 crm.db 到電腦備份",
                        data=f,
                        file_name="crm.db",
                        mime="application/x-sqlite3"
                    )
                    
            except Exception as e:
                st.error(f"匯入失敗：{e}")

with tab2:
    st.subheader("同步本地 crm.db 到雲端")
    st.info("如果你在電腦本地端已經更新好 crm.db，可以直接在此上傳覆蓋雲端檔案。")
    uploaded_db = st.file_uploader("上傳本地 crm.db", type=['db'])

    if uploaded_db and st.button("確認覆蓋雲端資料庫"):
        try:
            with open("crm.db", "wb") as f:
                f.write(uploaded_db.getbuffer())
            st.success("✅ 雲端資料庫已同步更新！")
            # 這裡強迫清除快取，讓爸爸搜尋時抓到新資料
            st.cache_data.clear() 
        except Exception as e:
            st.error(f"同步失敗：{e}")

if st.button("安全登出"):
    st.session_state.authenticated = False
    st.rerun()