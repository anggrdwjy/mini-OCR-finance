from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class UserCreate(BaseModel):
    email: str
    password: str
    nama: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    nama: Optional[str] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TransactionItemOut(BaseModel):
    id: int
    nama_item: str
    qty: float
    harga: float
    subtotal: float
    class Config:
        from_attributes = True

class TransactionOut(BaseModel):
    id: int
    tanggal: date
    merchant: Optional[str] = None
    tipe: str
    total: float
    metode_bayar: str
    kategori_id: Optional[int] = None
    confidence: float
    items: List[TransactionItemOut] = []
    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    tanggal: Optional[date] = None
    merchant: Optional[str] = None
    total: Optional[float] = None
    tipe: Optional[str] = None
    metode_bayar: Optional[str] = None
    kategori_id: Optional[int] = None
