import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Laporan Bulanan - Mini OCR Finance", layout="wide")
st.title("Laporan Bulanan")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Login dulu di halaman utama.")
    st.stop()

now = datetime.now()
year = st.number_input("Tahun", value=now.year, step=1)
month = st.selectbox("Bulan", list(range(1, 13)), index=now.month - 1)
headers = {"Authorization": f"Bearer {st.session_state.token}"}

if st.button("Tampilkan Laporan", type="primary"):
    r = requests.get(f"{API_URL}/reports/monthly", params={"year": int(year), "month": int(month)}, headers=headers)
    if r.status_code == 200:
        d = r.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Pemasukan", f"Rp {d['total_pemasukan']:,.0f}")
        c2.metric("Total Pengeluaran", f"Rp {d['total_pengeluaran']:,.0f}")
        c3.metric("Selisih", f"Rp {d['selisih']:,.0f}")
        if d["by_category"]:
            df_cat = pd.DataFrame(d["by_category"])
            st.subheader("Per Kategori")
            st.bar_chart(df_cat.set_index("kategori"))
            st.dataframe(df_cat, use_container_width=True)
            st.download_button("Download CSV Kategori", df_cat.to_csv(index=False), file_name=f"laporan_{year}_{month}.csv", mime="text/csv")
        if d["top_merchant"]:
            st.subheader("Top Merchant")
            st.dataframe(pd.DataFrame(d["top_merchant"]), use_container_width=True)
    else:
        st.error(r.text)
