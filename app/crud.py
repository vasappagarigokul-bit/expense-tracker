from email_validator import validate_email, EmailNotValidError
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi import Response
import json
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from sqlalchemy.engine.row import Row

from .models import User, Expense
from .redis import redis_cache, CACHE_TTL
from .twilio import client, TWILIO_PHONE
from .utils import hash_password
from typing import Optional, Any, List


# Register -----

async def verify_email_domain(email: str):
    try:
        result = await run_in_threadpool(
            validate_email, 
            email, 
            check_deliverability=True
        )

        return result.normalized
    except EmailNotValidError:
        return False
    except Exception:
        return None

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_mobile_number(db: Session, mobile_number: str) -> Optional[User]:
    return db.query(User).filter(User.phone == mobile_number).first()

def create_user(db: Session, user: str) -> User:
    db_entry = User(
        email=user.email,
        password=hash_password(user.password),
        phone=user.phone
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return db_entry

# Login -----

def cache_expenses_data(user_id: int, data: Any) -> Optional[dict]:
    try:
        cache_key = f"expenses:{user_id}"
        serialized_data = json.dumps(jsonable_encoder(data))
        redis_cache.setex(
            cache_key,
            CACHE_TTL,
            serialized_data
        )
    except Exception:
        pass

# Expenses -----

def delete_expenses_cache(user_id: int):
    try:
        cache_key = f"expenses:{user_id}"
        redis_cache.delete(cache_key)
    except Exception:
        pass

def add_expenses(
    db: Session,
    expense: str,
    user_id: int
) -> None:
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        owner_id=user_id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    delete_expenses_cache(user_id)
    return None

def get_expenses(db: Session, user_id: int) -> List[Expense]:
    # Fetch from cache
    try:
        cache_key = f"expenses:{user_id}"
        cached_data = redis_cache.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception:
        pass

    # Fallback to database (cache miss)
    expenses = db.query(Expense).filter(Expense.owner_id == user_id).all()

    # Update cache
    if expenses:
        cache_expenses_data(user_id, expenses)
    
    return expenses

def update_expenses(
    db: Session,
    expense_id: int,
    updated_data: str,
    user_id: int
) -> Optional[Expense]:
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_id == user_id
    ).first()
    if expense:
        expense.title = updated_data.title
        expense.amount = updated_data.amount
        db.commit()
        db.refresh(expense)

        delete_expenses_cache(user_id)

    return expense

def delete_expenses(
    db: Session,
    expense_id: int,
    user_id: int
) -> bool:
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_id == user_id
    ).first()
    if expense:
        db.delete(expense)
        db.commit()

        delete_expenses_cache(user_id)
        return True
    
    return False

# Analytics -----

def get_total_analytics(
    db: Session,
    period: str,
    user_id: int
) -> Row:
    return db.query(
        func.coalesce(func.sum(Expense.amount), 0).label('total_amount'),
        func.coalesce(func.round(func.avg(Expense.amount), 2), 0).label('average_amount'),
        func.coalesce(func.min(Expense.amount), 0).label('minimum_spent'),
        func.coalesce(func.max(Expense.amount), 0).label('maximum_spent'),
        func.coalesce(func.count(Expense.amount), 0).label('total_items')
    ).filter(
        Expense.owner_id == user_id,
        cast(Expense.created_at, Date) >= period.from_date,
        cast(Expense.created_at, Date) <= period.to_date
    ).first()

def get_each_item_analytics(
    db: Session,
    period: str,
    user_id: int
) -> List[Row]:
    return db.query(
        Expense.title,
        func.coalesce(func.sum(Expense.amount), 0).label('total_amount'),
        func.coalesce(func.round(func.avg(Expense.amount), 2), 0).label('average_amount'),
        func.coalesce(func.min(Expense.amount), 0).label('minimum_spent'),
        func.coalesce(func.max(Expense.amount), 0).label('maximum_spent'),
        func.coalesce(func.count(Expense.amount), 0).label('total_times')
    ).filter(
        Expense.owner_id == user_id,
        cast(Expense.created_at, Date) >= period.from_date,
        cast(Expense.created_at, Date) <= period.to_date
    ).group_by(Expense.title).all()

# Account Settings -----

def send_twilio_sms(mobile_number: str, otp: str):
    client.messages.create(
        body=f"Your verification code: {otp}. Valid for 10 minutes.",
        from_=TWILIO_PHONE,
        to=mobile_number
    )

def delete_cookie(response: Response) -> bool:
    try:
        response.delete_cookie(
            key="refresh_token",
            path="/refresh",
            httponly=True,
            secure=True,
            samesite="Strict"
        )

        return True
    except Exception:
        return False

def delete_account(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        delete_expenses_cache(user_id)
        
        db.delete(user)
        db.commit()
        return True
    
    return False