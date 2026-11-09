def categorize(merchant: str, raw_text: str = "") -> str:
    text = (merchant + " " + raw_text).lower()
    if any(k in text for k in ["indomaret", "alfamart", "minimarket", "sembako", "pasar"]):
        return "Belanja Harian"
    if any(k in text for k in ["kopi", "cafe", "resto", "makan", "warung", "kfc", "mcd"]):
        return "Makan dan Minum"
    if any(k in text for k in ["bensin", "pertamina", "shell", "parkir", "grab", "gojek", "tol"]):
        return "Transportasi"
    if any(k in text for k in ["listrik", "pln", "pdam", "wifi", "internet", "pulsa"]):
        return "Tagihan"
    if any(k in text for k in ["gaji", "transfer masuk", "penjualan", "invoice"]):
        return "Pemasukan"
    return "Lainnya"
