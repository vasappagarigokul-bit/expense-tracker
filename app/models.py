from sqlalchemy import (
    Column,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    func
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship
from .database import base

class User(base):
    __tablename__ = "users"

    # Column id
    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        index=True
    )

    # Column email
    email = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    # Column password
    password = Column(
        String(255),
        nullable=False
    )

    # Column phone
    phone = Column(
        String(20),
        unique=True,
        index=True,
        nullable=False
    )

    # Column account_created_at
    account_created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Column email_last_updated_at
    email_last_updated_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Column password_last_updated_at
    password_last_updated_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Column mobile_number_last_updated_at
    mobile_number_last_updated_at = Column(
        DateTime,
        server_default=func.now()
    )

    expenses = relationship(
        "Expense",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

class Expense(base):
    __tablename__ = "expenses"

    # Column id
    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        index=True
    )

    # Column title
    title = Column(
        String(100),
        nullable=False,
        index=True
    )

    # Column amount
    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    # Column created_at
    created_at = Column(
        DateTime,
        server_default=func.now(),
        index=True
    )

    # Column updated_at
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Column owner_id
    owner_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id"),
        index=True
    )

    owner = relationship(
        "User",
        back_populates="expenses"
    )