import streamlit as st
import pandas as pd
from utils.upload_excel import process_uploaded_excel # 直接呼叫封裝好的邏輯

st.title("📂 Excel 資料匯入")

upload_type = st.radio("資料類型", ("course", "software"))
uploaded_file = st.file_uploader("上傳 Excel", type=['xlsx'])

if uploaded_file and st.button("確認匯入"):
    df = pd.read_excel(uploaded_file)
    
    df = df.where(pd.notnull(df), None)
    
    # 直接呼叫你之前寫好的那個函數
    with st.spinner('正在匯入中...'):
        process_uploaded_excel(df, data_type=upload_type)
    
    st.success("匯入完成！")