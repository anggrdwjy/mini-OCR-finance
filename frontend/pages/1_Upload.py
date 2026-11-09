import streamlit as st
import requests
import os
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Upload - Mini OCR Finance", layout="wide")
st.title("Upload Struk")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Login dulu di halaman utama.")
    st.stop()

tipe = st.selectbox("Tipe", ["pengeluaran", "pemasukan"])
metode = st.selectbox("Metode Bayar", ["Tunai", "Transfer", "QRIS", "Kartu"])

tab_gambar, tab_pdf = st.tabs(["Upload Gambar (JPG / PNG)", "Upload PDF"])

with tab_gambar:
    file = st.file_uploader("Foto struk (JPG / PNG)", type=["jpg", "jpeg", "png"], key="img_uploader")
    if file and st.button("Upload dan Proses OCR", type="primary", key="btn_img"):
        with st.spinner("OCR lagi jalan..."):
            files = {"file": (file.name, file.getvalue(), file.type)}
            data = {"tipe": tipe, "metode_bayar": metode}
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            r = requests.post(f"{API_URL}/transactions/upload", files=files, data=data, headers=headers)
            if r.status_code == 200:
                d = r.json()
                st.success("Berhasil disimpan!")
                st.write(f"Merchant: {d.get('merchant')}")
                st.write(f"Tanggal: {d.get('tanggal')}")
                st.write(f"Total: Rp {d.get('total'):,.0f}")
                st.write(f"Kategori ID: {d.get('kategori_id')} | Confidence: {d.get('confidence')}")
            else:
                st.error(r.text)

with tab_pdf:
    st.info("PDF bisa 1 struk atau banyak struk. Kalau PDF 3 halaman struk, akan jadi 3 transaksi. PDF hasil scan juga bisa, akan di-OCR per halaman.")
    pdf_file = st.file_uploader("File PDF (maks 20 MB)", type=["pdf"], key="pdf_uploader")
    if pdf_file and st.button("Upload PDF dan Proses", type="primary", key="btn_pdf"):
        with st.spinner("Baca PDF dan OCR per halaman..."):
            files = {"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")}
            data = {"tipe": tipe, "metode_bayar": metode}
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            r = requests.post(f"{API_URL}/transactions/upload-pdf", files=files, data=data, headers=headers)
            if r.status_code == 200:
                data_list = r.json()
                st.success(f"Berhasil! {len(data_list)} transaksi dibuat dari PDF.")
                if data_list:
                    df = pd.DataFrame(data_list)
                    cols = [c for c in ["tanggal", "merchant", "tipe", "total", "metode_bayar"] if c in df.columns]
                    st.dataframe(df[cols], use_container_width=True)
                    st.write(f"Total gabungan: Rp {df['total'].sum():,.0f}")
                    st.download_button("Download hasil CSV", df.to_csv(index=False), file_name="hasil_pdf.csv", mime="text/csv")
            else:
                st.error(r.text)
