import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Mini OCR Finance", layout="wide")
st.title("Mini OCR Finance")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

if st.session_state.token is None:
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
            if r.status_code == 200:
                data = r.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.success("Login berhasil")
                st.rerun()
            else:
                st.error("Email atau password salah")
    with tab_register:
        nama = st.text_input("Nama", key="reg_nama")
        email2 = st.text_input("Email", key="reg_email")
        pass2 = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Buat Akun"):
            r = requests.post(f"{API_URL}/auth/register", json={"email": email2, "password": pass2, "nama": nama})
            if r.status_code == 200:
                st.success("Akun dibuat, silakan login di tab Login")
            else:
                st.error(r.text)
    st.info("Login dulu untuk buka Upload, Dashboard, dan Laporan Bulanan di sidebar.")
else:
    st.success(f"Halo, {st.session_state.user.get('nama') or st.session_state.user.get('email')}")
    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()
    now = datetime.now()
    try:
        rep = requests.get(f"{API_URL}/reports/monthly", params={"year": now.year, "month": now.month}, headers=headers(), timeout=10)
        if rep.status_code == 200:
            d = rep.json()
            c1, c2, c3 = st.columns(3)
            c1.metric("Pemasukan Bulan Ini", f"Rp {d['total_pemasukan']:,.0f}")
            c2.metric("Pengeluaran Bulan Ini", f"Rp {d['total_pengeluaran']:,.0f}")
            c3.metric("Selisih", f"Rp {d['selisih']:,.0f}")
            if d["by_category"]:
                st.subheader("Per Kategori")
                st.bar_chart(pd.DataFrame(d["by_category"]).set_index("kategori"))
            if d["top_merchant"]:
                st.subheader("Top Merchant")
                st.dataframe(pd.DataFrame(d["top_merchant"]))
    except Exception as e:
        st.error(f"Gagal ambil laporan: {e}")
    st.divider()
    st.write("Lanjut ke halaman di sidebar: Upload untuk tambah struk, Dashboard untuk semua transaksi, Laporan Bulanan untuk rekap per bulan.")
