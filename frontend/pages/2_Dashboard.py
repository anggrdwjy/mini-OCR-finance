import streamlit as st
import requests
import os
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Dashboard - Mini OCR Finance", layout="wide")
st.title("Dashboard Transaksi")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Login dulu di halaman utama.")
    st.stop()

tipe_filter = st.selectbox("Filter Tipe", ["Semua", "pemasukan", "pengeluaran"])
params = {}
if tipe_filter != "Semua":
    params["tipe"] = tipe_filter

headers = {"Authorization": f"Bearer {st.session_state.token}"}
r = requests.get(f"{API_URL}/transactions", params=params, headers=headers)
if r.status_code == 200:
    data = r.json()
    if not data:
        st.info("Belum ada transaksi. Upload struk dulu.")
    else:
        df = pd.DataFrame(data)
        st.dataframe(df[["tanggal", "merchant", "tipe", "total", "metode_bayar"]], use_container_width=True)
        st.subheader("Total per Tipe")
        st.bar_chart(df.groupby("tipe")["total"].sum())
else:
    st.error(r.text)
