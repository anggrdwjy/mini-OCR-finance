import re
import os
import tempfile
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional
from PIL import Image, ImageOps, ImageEnhance

BULAN_ID = {
    "januari": 1, "jan": 1, "january": 1,
    "februari": 2, "feb": 2, "february": 2,
    "maret": 3, "mar": 3, "march": 3,
    "april": 4, "apr": 4,
    "mei": 5, "may": 5,
    "juni": 6, "jun": 6, "june": 6,
    "juli": 7, "jul": 7, "july": 7,
    "agustus": 8, "agu": 8, "aug": 8, "august": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10, "oct": 10, "october": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12, "dec": 12, "december": 12,
}

# Semua uang pakai Decimal, bukan float. 2 digit di belakang koma, dibulatkan HALF_UP.
CENT = Decimal("0.01")
SERIBU = Decimal("1000")
NOL = Decimal("0.00")
MAX_TOTAL = Decimal("100000000.00")

def _to_decimal(value) -> Optional[Decimal]:
    """Ubah float / int / str / Decimal jadi Decimal 2 digit, aman dari float error."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value.quantize(CENT, rounding=ROUND_HALF_UP)
    try:
        # Jangan Decimal(float) langsung, pakai str() biar 0.1 tidak jadi 0.10000000000000000555
        return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return None

def _format_decimal(v: Decimal) -> str:
    """Format Decimal ala Indonesia untuk warning: 958000.00 -> 958.000,00"""
    if v is None:
        return "0,00"
    v = _to_decimal(v)
    # Format US dulu: 958,000.00 lalu tukar , dan .
    us = f"{v:,.2f}"  # contoh: 958,000.00
    return us.replace(",", "X").replace(".", ",").replace("X", ".")

def parse_idr(raw: str) -> Optional[Decimal]:
    # Tangani dalam bentuk Decimal: 958.000 -> 958000.00, 958,000 -> 958000.00, 958 000 -> 958000.00,
    # 958.000,00 -> 958000.00, 958000 -> 958000.00, 15000.50 -> 15000.50
    if raw is None:
        return None
    s = str(raw).strip()
    s = s.replace("Rp", "").replace("RP", "").replace("IDR", "").replace("idr", "").strip()
    s = s.replace("_", "").replace("'", "").replace("\xa0", "")
    s_no_space = s.replace(" ", "")
    s = re.sub(r"[^0-9\.,\-]", "", s_no_space)
    if not s or s in ["-", ".", ","]:
        return None
    is_neg = s.startswith("-")
    s = s.lstrip("-")
    try:
        if "," in s and "." in s:
            # Yang muncul terakhir = desimal. Contoh: 1.250.000,50 -> titik ribuan, koma desimal
            # Contoh US: 1,250,000.50 -> koma ribuan, titik desimal
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            parts = s.split(",")
            if len(parts) > 2:
                # 1,250,000 -> ribuan semua
                s = s.replace(",", "")
            elif len(parts) == 2:
                if len(parts[-1]) == 3:
                    # 958,000 -> ribuan, bukan desimal
                    s = s.replace(",", "")
                elif len(parts[-1]) == 2:
                    # 15000,50 -> desimal
                    s = s.replace(",", ".")
                elif len(parts[-1]) == 1:
                    # 100,5 -> desimal 1 digit
                    s = s.replace(",", ".")
                else:
                    s = s.replace(",", "")
            else:
                s = s.replace(",", "")
        elif "." in s:
            parts = s.split(".")
            if len(parts) > 2:
                # 1.250.000 -> semua titik ribuan
                s = s.replace(".", "")
            elif len(parts) == 2:
                if len(parts[-1]) == 3:
                    # 958.000 -> ribuan
                    s = s.replace(".", "")
                elif len(parts[-1]) in (1, 2):
                    # 15000.50 atau 100.5 -> desimal, biarkan
                    pass
                else:
                    s = s.replace(".", "")
        val = Decimal(s).quantize(CENT, rounding=ROUND_HALF_UP)
        if is_neg:
            val = -val
        return val
    except (InvalidOperation, ValueError):
        return None

def _is_phone_or_id(num_str: str):
    t = num_str.replace(".", "").replace(",", "").replace(" ", "").replace("-", "").replace("+", "")
    if not t.isdigit():
        return False
    if len(t) >= 15:
        return True
    if len(t) >= 10 and (t.startswith("08") or t.startswith("628") or t.startswith("62")):
        return True
    return False

def find_merchant(text: str):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [l for l in lines if not l.startswith("--- Halaman")]
    for line in lines:
        up = line.upper()
        if any(k in up for k in ["JL.", "JALAN", "TELP", "TELPON", "PHONE", "NPWP", "NO.", "NO ", "KASIR", "CASHIER", "TANGGAL", "DATE"]):
            continue
        letters = re.sub(r"[^A-Za-z]", "", line)
        if len(letters) < 3:
            continue
        if all(w in up for w in ["STRUK"]):
            continue
        clean = re.sub(r"^[^A-Za-z0-9]+", "", line).strip()
        if len(clean) >= 3:
            return clean[:100]
    return "Tidak diketahui"

def find_date(text: str):
    lines = text.splitlines()
    candidates = []
    pat_bulan = re.compile(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", re.IGNORECASE)
    pat_iso = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
    pat_slash = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})")
    for line in lines:
        up = line.upper()
        bonus = 10 if any(k in up for k in ["TANGGAL", "DATE", "TGL"]) else 0
        m = pat_bulan.search(line)
        if m:
            d, mon, y = m.groups()
            mon_l = mon.lower()
            if mon_l in BULAN_ID:
                try:
                    dt = date(int(y), BULAN_ID[mon_l], int(d))
                    if 2000 <= dt.year <= 2030:
                        candidates.append((bonus + 5, dt, "bulan"))
                except Exception:
                    pass
        m2 = pat_iso.search(line)
        if m2:
            try:
                y, mo, d = map(int, m2.groups())
                dt = date(y, mo, d)
                if 2000 <= dt.year <= 2030:
                    candidates.append((bonus + 4, dt, "iso"))
            except Exception:
                pass
        for m3 in pat_slash.finditer(line):
            try:
                d, mo, y = m3.groups()
                y = int(y)
                if y < 100:
                    y += 2000
                if not (1 <= int(mo) <= 12 and 1 <= int(d) <= 31 and 2000 <= y <= 2030):
                    continue
                dt = date(y, int(mo), int(d))
                if dt > date.today().replace(year=date.today().year + 1):
                    continue
                candidates.append((bonus, dt, "slash"))
            except Exception:
                continue
    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1], candidates[0][2]
    return date.today(), "fallback_today"

def _extract_number_from_chunk(chunk: str):
    # Chunk bisa: "Rp 958.000", "958 000", "958\n000", "958.000,00", "Rp 15.000,50"
    # Return: (Decimal, raw_str) atau None
    chunk = chunk.replace("\n", " ").replace("\r", " ")
    patterns = re.findall(r"Rp\s*[\d]{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{2})?|[\d]{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{2})?|Rp\s*[\d\.,]+|[\d\.,]+", chunk)
    if not patterns:
        return None
    for cand in reversed(patterns):
        v = parse_idr(cand)
        if v is not None and v > NOL:
            return v, cand
    return None

def find_total(text: str):
    # Return: (Decimal, source_str, candidates)
    # 1. Coba pola lintas baris: TOTAL ... (maks 60 karakter ke depan, termasuk newline)
    cross_pattern = re.compile(r"(GRAND TOTAL|TOTAL BAYAR|TOTAL PEMBAYARAN|JUMLAH BAYAR|TOTAL AKHIR|AMOUNT DUE|TOTAL)[^0-9A-Za-z]{0,5}([\s\S]{0,60}?)", re.IGNORECASE)
    matches = list(cross_pattern.finditer(text))
    filtered = []
    for m in matches:
        start = m.start()
        full_line_start = text[max(0, start-30):start+50].upper()
        if "SUBTOTAL" in full_line_start or "SUB TOTAL" in full_line_start:
            continue
        if "TOTAL ITEM" in full_line_start or "TOTAL QTY" in full_line_start:
            continue
        filtered.append(m)
    if filtered:
        for m in reversed(filtered):
            keyword = m.group(1)
            chunk = m.group(2)
            after = text[m.end():m.end()+100].splitlines()[:2]
            chunk_full = chunk + "\n" + "\n".join(after)
            res = _extract_number_from_chunk(chunk_full)
            if res:
                val, raw_num = res
                return val, f"keyword:{keyword} | chunk: {chunk_full[:80].replace(chr(10),' ')}", [(Decimal("0"), val, chunk_full[:80], keyword)]
    # 2. Fallback per-baris
    lines = text.splitlines()
    cands = []
    for idx, line in enumerate(lines):
        up = line.upper()
        if any(k in up for k in ["SUBTOTAL", "SUB TOTAL", "TOTAL ITEM", "TOTAL QTY", "TOTAL BARANG", "JUMLAH ITEM"]):
            continue
        keywords = ["GRAND TOTAL", "TOTAL BAYAR", "TOTAL PEMBAYARAN", "JUMLAH BAYAR", "JUMLAH YANG DIBAYAR", "TOTAL AKHIR", "AMOUNT DUE", "TOTAL"]
        matched = None
        for kw in keywords:
            if kw in up:
                matched = kw
                break
        if not matched:
            continue
        combined_line = line
        if idx + 1 < len(lines):
            nxt = lines[idx+1].strip()
            if re.match(r"^[.,\s]*\d{2,3}$", nxt):
                combined_line = line + " " + nxt
        res = _extract_number_from_chunk(combined_line)
        if res:
            val, raw_num = res
            score = Decimal("10") if "GRAND" in matched else Decimal("8")
            score += Decimal(str(idx)) / Decimal(str(max(1, len(lines)))) * Decimal("2")
            cands.append((score, val, combined_line.strip(), matched))
    if cands:
        cands.sort(key=lambda x: x[0])
        best = cands[-1]
        return best[1], f"keyword:{best[3]} | baris: {best[2][:80]}", cands
    # 3. Fallback terakhir: cari angka currency, tolak HP
    all_nums = []
    for line in lines:
        if any(k in line.upper() for k in ["TELP", "PHONE", "NPWP", "NIK", "NO.", "KASIR"]):
            continue
        for n in re.findall(r"Rp\s*[\d]{1,3}(?:[.,\s]\d{3})+|[\d]{1,3}(?:[.,\s]\d{3})+|[\d]+", line):
            if _is_phone_or_id(n):
                continue
            v = parse_idr(n)
            if v is not None and Decimal("100") <= v <= MAX_TOTAL:
                all_nums.append(v)
    if all_nums:
        return all_nums[-1], "fallback_last_currency", [(Decimal("0"), v, "", "") for v in all_nums]
    return NOL, "not_found", []

def _preprocess_for_ocr(img: Image.Image):
    try:
        img = img.convert("L")
        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        return img
    except Exception:
        return img

def extract_text(image_path: str) -> str:
    try:
        import pytesseract
        img = Image.open(image_path)
        t1 = pytesseract.image_to_string(img, lang="ind+eng")
        try:
            img2 = _preprocess_for_ocr(img)
            t2 = pytesseract.image_to_string(img2, lang="ind+eng", config="--psm 6")
            if len(t2.strip()) > len(t1.strip()):
                return t2
        except Exception:
            pass
        return t1
    except Exception:
        return ""

def extract_text_from_pdf(pdf_path: str):
    try:
        import fitz
    except ImportError:
        return {"combined_text": "", "pages": [], "page_count": 0}
    doc = fitz.open(pdf_path)
    pages = []
    combined = []
    tmpdir = tempfile.mkdtemp(prefix="ocr_pdf_")
    for i, page in enumerate(doc):
        try:
            text = page.get_text("layout") or ""
        except Exception:
            text = ""
        if len(text.strip()) < 30:
            text = page.get_text() or ""
        if len(text.strip()) < 30:
            try:
                import pytesseract
                pix = page.get_pixmap(dpi=300)
                img_path = os.path.join(tmpdir, f"page_{i+1}.png")
                pix.save(img_path)
                img = Image.open(img_path)
                img = _preprocess_for_ocr(img)
                ocr_text = pytesseract.image_to_string(img, lang="ind+eng", config="--psm 6")
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
            except Exception:
                pass
        pages.append({"page": i + 1, "text": text})
        combined.append(f"\n--- Halaman {i+1} ---\n{text}")
    doc.close()
    return {"combined_text": "\n".join(combined), "pages": pages, "page_count": len(pages)}

def extract_text_auto(path: str) -> str:
    if path.lower().endswith(".pdf"):
        res = extract_text_from_pdf(path)
        return res["combined_text"]
    return extract_text(path)

def parse_receipt(text: str, fallback_total=None):
    # fallback_total boleh float / int / str / Decimal, diubah ke Decimal
    fallback_dec = _to_decimal(fallback_total) if fallback_total else None
    if not text or len(text.strip()) < 5:
        return {"merchant": "Tidak diketahui", "tanggal": date.today(), "total": NOL, "raw_text": text or "", "confidence": 0.1, "total_source": "empty", "date_source": "empty", "warning": "Teks hasil OCR kosong / terlalu pendek.", "candidates_total": []}
    merchant = find_merchant(text)
    tanggal, date_source = find_date(text)
    total, total_source, cands = find_total(text)
    # total sudah Decimal dari find_total
    if total == NOL and fallback_dec:
        total = fallback_dec
        total_source = "fallback_param"
    conf = 0.3
    if total > NOL:
        conf += 0.3
        if total_source.startswith("keyword"):
            conf += 0.15
    if date_source != "fallback_today":
        conf += 0.15
    if merchant != "Tidak diketahui":
        conf += 0.1
    conf = min(0.95, conf)
    warning = None
    if total <= NOL:
        warning = "Total tidak ketemu. Edit manual totalnya."
    elif total < SERIBU:
        # Contoh: 958.00 seharusnya 958000.00
        seharusnya = (total * SERIBU).quantize(CENT, rounding=ROUND_HALF_UP)
        warning = f"Total {_format_decimal(total)} mencurigakan, terlalu kecil untuk struk. Kemungkinan seharusnya {_format_decimal(seharusnya)} (titik .000 hilang). Cek dan edit manual. Contoh: 958 seharusnya 958.000."
        conf = 0.3
    elif total_source.startswith("fallback"):
        warning = "Total diambil dari tebakan fallback, bukan dari baris TOTAL. Cek dan edit manual kalau salah."
    if merchant == "Tidak diketahui":
        warning = (warning or "") + " Merchant tidak ketemu, edit manual."
    # candidates_total dalam Decimal, biar frontend bisa format desimal juga
    candidates_out = []
    for _, v, l, _ in cands[:3]:
        v_dec = _to_decimal(v)
        candidates_out.append({"value": v_dec, "value_str": _format_decimal(v_dec), "line": l})
    return {"merchant": merchant, "tanggal": tanggal, "total": total, "total_str": _format_decimal(total), "raw_text": text, "confidence": round(conf, 2), "total_source": total_source, "date_source": date_source, "warning": warning.strip() if warning else None, "candidates_total": candidates_out}

