from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models, schemas
from auth import hash_password, verify_password, create_access_token
from jose import jwt
import redis
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

r = redis.Redis(host=os.getenv('REDIS_HOST'), port=6379)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post('/register')
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed = hash_password(user.password)
    db_user = models.User(email=user.email, password=hashed)
    db.add(db_user)
    db.commit()
    return {'message': 'User created'}

@app.post('/login')
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({'sub': db_user.email})
    return {'access_token': token}

@app.post('/expenses')
def add_expense(exp: schemas.ExpenseCreate, token: str, db: Session = Depends(get_db)):
    payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
    email = payload.get('sub')
    user = db.query(models.User).filter(models.User.email == email).first()
    
    new_exp = models.Expense(title=exp.title, amount=exp.amount, owner_id=user.id)
    db.add(new_exp)
    db.commit()

    r.delete(f'expenses:{user.id}')
    return {'message': 'Expense added'}

@app.get('/expenses')
def get_expenses(token: str, db: Session = Depends(get_db)):
    payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
    email = payload.get('sub')
    user = db.query(models.User).filter(models.User.email == email).first()

    cache_key = f'expenses:{user.id}'
    cached = r.get(cache_key)

    if cached:
        return {'source': 'cache', 'data': cached}

    expenses = db.query(models.Expense).filter(models.Expense.owner_id == user.id).all()
    r.set(cache_key, str([e.title for e in expenses]), ex=60)

    return {'source': 'db', 'data': expenses}