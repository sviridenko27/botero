from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    section: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Filling(Base):
    __tablename__ = "fillings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class StoreInfo(Base):
    __tablename__ = "store_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_text: Mapped[str] = mapped_column(Text, nullable=False)
    payment_text: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
