from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    nama = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    transactions = relationship("Transaction", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, nullable=False)
    tipe = Column(String, nullable=False)
    warna = Column(String, default="#3b82f6")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tanggal = Column(Date, nullable=False)
    merchant = Column(String, nullable=True)
    tipe = Column(String, nullable=False)
    total = Column(Float, nullable=False)
    metode_bayar = Column(String, default="Tunai")
    kategori_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    receipt_path = Column(String, nullable=True)
    confidence = Column(Float, default=0.85)
    status = Column(String, default="done")
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")

class TransactionItem(Base):
    __tablename__ = "transaction_items"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    nama_item = Column(String, nullable=False)
    qty = Column(Float, default=1)
    harga = Column(Float, default=0)
    subtotal = Column(Float, default=0)
    transaction = relationship("Transaction", back_populates="items")
