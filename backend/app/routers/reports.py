from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.models import Transaction, Category, User
from app.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/monthly")
def monthly_report(year: int, month: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = db.query(Transaction).filter(Transaction.user_id == current_user.id, extract("year", Transaction.tanggal) == year, extract("month", Transaction.tanggal) == month)
    pemasukan = base.filter(Transaction.tipe == "pemasukan").with_entities(func.coalesce(func.sum(Transaction.total), 0)).scalar()
    pengeluaran = base.filter(Transaction.tipe == "pengeluaran").with_entities(func.coalesce(func.sum(Transaction.total), 0)).scalar()
    by_category = db.query(Category.nama, func.coalesce(func.sum(Transaction.total), 0)).join(Transaction, Transaction.kategori_id == Category.id).filter(Transaction.user_id == current_user.id, extract("year", Transaction.tanggal) == year, extract("month", Transaction.tanggal) == month).group_by(Category.nama).all()
    by_merchant = db.query(Transaction.merchant, func.coalesce(func.sum(Transaction.total), 0)).filter(Transaction.user_id == current_user.id, extract("year", Transaction.tanggal) == year, extract("month", Transaction.tanggal) == month).group_by(Transaction.merchant).order_by(func.sum(Transaction.total).desc()).limit(5).all()
    return {
        "year": year,
        "month": month,
        "total_pemasukan": float(pemasukan or 0),
        "total_pengeluaran": float(pengeluaran or 0),
        "selisih": float((pemasukan or 0) - (pengeluaran or 0)),
        "by_category": [{"kategori": n, "total": float(t)} for n, t in by_category],
        "top_merchant": [{"merchant": m, "total": float(t)} for m, t in by_merchant]
    }
