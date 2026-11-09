from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.models import Category
from app.routers import auth, transactions, reports

app = FastAPI(title="Mini OCR Finance", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(reports.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            seeds = [
                ("Belanja Harian", "pengeluaran", "#f59e0b"),
                ("Makan dan Minum", "pengeluaran", "#ef4444"),
                ("Transportasi", "pengeluaran", "#3b82f6"),
                ("Tagihan", "pengeluaran", "#8b5cf6"),
                ("Pemasukan", "pemasukan", "#10b981"),
                ("Lainnya", "pengeluaran", "#6b7280"),
            ]
            for nama, tipe, warna in seeds:
                db.add(Category(nama=nama, tipe=tipe, warna=warna))
            db.commit()
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Mini OCR Finance API jalan", "docs": "/docs"}
