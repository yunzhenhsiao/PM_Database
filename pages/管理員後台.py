import streamlit as st
import pandas as pd
import os
from utils.upload_excel import process_uploaded_excel

st.set_page_config(page_title="管理員後台", page_icon="🔐")

# --- 簡單的身分驗證 ---
ADMIN_PASSWORD = "1222" # 這裡改掉，不要讓爸爸猜到
df = pd.DataFrame()  # 預先定義 df，避免未定義錯誤

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

    if uploaded_xlsx:
        xl = pd.ExcelFile(uploaded_xlsx)
        all_sheets = xl.sheet_names
        selected_sheet = st.selectbox("請選擇要匯入的分頁", all_sheets)
        
        # --- 預覽與清洗邏輯 ---
        df_preview = pd.read_excel(uploaded_xlsx, sheet_name=selected_sheet, nrows=10)
        
        # 【關鍵修正 1】清洗預覽表的標題 (讓預覽畫面乾淨)
        df_preview.columns = [
            str(c).replace('_x000d_', '').replace('\n', '').replace('\r', '').strip() 
            for c in df_preview.columns
        ]
        
        # 【關鍵修正 2】將所有欄位轉為字串 (解決 Arrow 報錯，確保能預覽)
        df_preview = df_preview.astype(str).replace('nan', '').replace('None', '')

        st.write("分頁預覽 (前 10 筆)：")
        st.dataframe(df_preview)

        if st.button("確認執行匯入"):
            with st.spinner(f'正在處理 {selected_sheet} 的資料...'):
                try:
                    # 讀取完整資料
                    df = pd.read_excel(uploaded_xlsx, sheet_name=selected_sheet)
                    
                    # 【核心修正】正式清洗所有標題，確保 process_uploaded_excel 抓得到欄位
                    df.columns = [
                        str(c).replace('_x000d_', '').replace('\n', '').replace('\r', '').strip() 
                        for c in df.columns
                    ]
                    
                    # 處理空值轉為 None，方便 SQLite 處理
                    df = df.where(pd.notnull(df), None)

                    # 【資管級別清洗】刪除那些「全都是空值」的列
                    df = df.dropna(how='all')

                    # 或者是：只要「姓名」是空的列就不要
                    name_candidates = ['姓名', '學員姓名', '客戶姓名', 'Name']
                    actual_name_col = next((col for col in name_candidates if col in df.columns), None)
                    df = df[df[actual_name_col].notna()]
                    
                    # 執行匯入
                    process_uploaded_excel(df, data_type=upload_type)
                    
                    st.success(f"✅ 分頁「{selected_sheet}」數據已成功寫入 crm.db！")
                    
                    with open("crm.db", "rb") as f:
                        st.download_button(
                            label="📥 下載更新後的 crm.db 備份到電腦",
                            data=f,
                            file_name="crm.db",
                            mime="application/x-sqlite3"
                        )
                except Exception as e:
                    st.error(f"匯入過程中發生錯誤：{e}")

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