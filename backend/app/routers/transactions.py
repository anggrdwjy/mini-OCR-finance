from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import os, uuid
from app.database import get_db
from app.models import Transaction, Category, User
from app.schemas import TransactionOut, TransactionUpdate
from app.auth import get_current_user
from app.config import settings
from app.services.ocr_service import extract_text, extract_text_from_pdf, parse_receipt
from app.services.categorizer import categorize

router = APIRouter(prefix="/transactions", tags=["transactions"])

def _get_kategori(db: Session, merchant: str, raw_text: str):
    kategori_nama = categorize(merchant, raw_text)
    kategori = db.query(Category).filter(Category.nama == kategori_nama).first()
    if not kategori:
        kategori = db.query(Category).filter(Category.nama == "Lainnya").first()
    return kategori

def _create_trx(db: Session, user: User, parsed: dict, raw_text: str, tipe: str, metode_bayar: str, receipt_path: str, confidence: float = 0.85):
    kategori = _get_kategori(db, parsed["merchant"], raw_text)
    trx = Transaction(
        user_id=user.id,
        tanggal=parsed["tanggal"],
        merchant=parsed["merchant"],
        tipe=tipe,
        total=parsed["total"],
        metode_bayar=metode_bayar,
        kategori_id=kategori.id if kategori else None,
        receipt_path=receipt_path,
        confidence=confidence
    )
    db.add(trx)
    db.commit()
    db.refresh(trx)
    return trx

@router.post("/upload", response_model=TransactionOut)
def upload_receipt(
    file: UploadFile = File(...),
    tipe: str = Form("pengeluaran"),
    metode_bayar: str = Form("Tunai"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    # Kalau PDF, pakai ekstraksi PDF lalu gabungkan jadi 1 transaksi (untuk kompatibilitas lama)
    if filename.lower().endswith(".pdf"):
        pdf_res = extract_text_from_pdf(path)
        raw_text = pdf_res["combined_text"]
        parsed = parse_receipt(raw_text)
        return _create_trx(db, current_user, parsed, raw_text, tipe, metode_bayar, path, 0.85)
    raw_text = extract_text(path)
    parsed = parse_receipt(raw_text)
    return _create_trx(db, current_user, parsed, raw_text, tipe, metode_bayar, path, 0.85)

@router.post("/upload-pdf", response_model=list[TransactionOut])
def upload_pdf(
    file: UploadFile = File(...),
    tipe: str = Form("pengeluaran"),
    metode_bayar: str = Form("Tunai"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File harus PDF. Untuk gambar pakai endpoint /upload.")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    pdf_res = extract_text_from_pdf(path)
    results = []
    # 1 PDF banyak halaman: tiap halaman yang punya total valid jadi 1 transaksi
    for p in pdf_res["pages"]:
        text = p["text"]
        if len(text.strip()) < 10:
            continue
        parsed = parse_receipt(text)
        if parsed["total"] <= 0:
            continue
        trx = _create_trx(db, current_user, parsed, text, tipe, metode_bayar, f"{path}#page={p['page']}", 0.85)
        results.append(trx)
    # Fallback: kalau tidak ada halaman yang ke-detect totalnya, buat 1 transaksi dari gabungan teks
    if not results:
        parsed = parse_receipt(pdf_res["combined_text"])
        trx = _create_trx(db, current_user, parsed, pdf_res["combined_text"], tipe, metode_bayar, path, 0.6)
        results.append(trx)
    return results

@router.get("", response_model=list[TransactionOut])
def list_transactions(tipe: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.tanggal.desc())
    if tipe:
        q = q.filter(Transaction.tipe == tipe)
    return q.limit(200).all()

@router.get("/{trx_id}", response_model=TransactionOut)
def get_one(trx_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trx = db.query(Transaction).filter(Transaction.id == trx_id, Transaction.user_id == current_user.id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return trx

@router.put("/{trx_id}", response_model=TransactionOut)
def update_one(trx_id: int, payload: TransactionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trx = db.query(Transaction).filter(Transaction.id == trx_id, Transaction.user_id == current_user.id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(trx, k, v)
    db.commit()
    db.refresh(trx)
    return trx

@router.delete("/{trx_id}")
def delete_one(trx_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trx = db.query(Transaction).filter(Transaction.id == trx_id, Transaction.user_id == current_user.id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    db.delete(trx)
    db.commit()
    return {"message": "Transaksi dihapus"}
