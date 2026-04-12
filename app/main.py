from fastapi import (
    FastAPI,
    status,
    Depends,
    HTTPException,
    dependencies,
    Response,
    Request,
    BackgroundTasks
)
from sqlalchemy.orm import Session
from sqlalchemy import func
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from redis.exceptions import ConnectionError, ResponseError
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv
import os
import time

from .database import engine, base
from .models import User, Expense
from . import schemas, redis, utils, auth, crud
from .twilio import client, TWILIO_PHONE
from typing import List


load_dotenv(dotenv_path=".env")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
if not PHONE_NUMBER:
    raise ValueError(
        "Server Misconfiguration."
    )

base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker",
    description="Scalable Expense Analytics Platform."
)

# Middleware -----

@app.middleware("http")
async def get_response_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    response.headers["X-Response-Time-Ms"] = f"{process_time * 1000:.2f}ms"
    return response

# App Health -----

@app.get(
    path="/api",
    tags=['Health'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute.",
    description="This a simple health check for the API."
)
def get_api_health():
    return {
        "message": "Expense Tracker API is running successfully!"
    }

@app.get(
    path="/check_1",
    tags=['Health'],
    status_code=status.HTTP_200_OK,
    summary="Admin only."
)
async def get_database_health(db: Session=Depends(auth.get_db), admin: bool=Depends(utils.authorize)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "Ok",
            "database": "Connected"
        }
    except OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    except ProgrammingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database integrity error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get(
    path="/check_2",
    tags=['Health'],
    status_code=status.HTTP_200_OK,
    summary="Admin only."
)
async def get_cache_db_health(admin: bool=Depends(utils.authorize)):
    try:
        if redis.redis_cache.ping():
            return {
                "status": "Ok",
                "redis_cache_db": "Connected"
            }
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis cache database connection failed: {str(e)}"
        )
    except ResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Redis cache database requests out of limit: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redis cache database error: {str(e)}"
        )

@app.get(
    path="/check_3",
    tags=['Health'],
    status_code=status.HTTP_200_OK,
    summary="Admin only."
)
async def get_rate_limiter_db_health(admin: bool=Depends(utils.authorize)):
    try:
        if redis.redis_rate_limiter.ping():
            return {
                "status": "Ok",
                "redis_rate_limiter_db": "Connected"
            }
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis rate limiter database connection failed: {str(e)}"
        )
    except ResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Redis rate limiter database requests out of limit: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redis rate limiter database error: {str(e)}"
        )

@app.get(
    path="/check_4",
    tags=['Health'],
    status_code=status.HTTP_200_OK,
    summary="Admin only."
)
async def get_otp_storage_db_health(admin: bool=Depends(utils.authorize)):
    try:
        if redis.redis_otp_storage.ping():
            return {
                "status": "Ok",
                "redis_otp_storage_db": "Connected"
            }
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis otp storage database connection failed: {str(e)}"
        )
    except ResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Redis otp storage database requests out of limit: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Redis otp storage database error: {str(e)}'
        )

@app.get(
    "/check_5",
    tags=['Health'],
    status_code=status.HTTP_200_OK,
    summary="Admin only."
)
async def get_twilio_health(admin: bool=Depends(utils.authorize)):
    try:
        otp = utils.generate_otp()
        crud.send_twilio_sms(PHONE_NUMBER, otp)
        return {
            "status": "Ok",
            "message": "OTP sent successfully!"
        }
    except TwilioRestException as e:
        raise HTTPException(
            status_code=e.status,
            detail=f"More information: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Twilio error: {str(e)}"
        )

# Register -----

@app.post(
    path="/signup",
    tags=['Create Account'],
    status_code=status.HTTP_201_CREATED,
    summary="Try it out: enter email, create password, and add phone number, and click Execute.",
    description="Creates an account for the user."
)
async def register(user: schemas.UserCreate, db: Session=Depends(auth.get_db)):
    validated_email = await crud.verify_email_domain(str(user.email))
    if validated_email is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Email."
        )

    if validated_email is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Please try again later."
        )

    if crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is linked with another account."
        )
    
    if crud.get_user_by_mobile_number(db, user.phone):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mobile number is linked with another account."
        )
    
    crud.create_user(db, user)
    return {
        "message": "Registered successfully!"
    }

# Login -----

@app.post(
    path="/signin",
    tags=['Account Login'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter registered email and password, and click Execute. Copy-paste the access token in into the 'Authorize' button at the top of the page and click Enter.",
    description="Login user and generate access token for user authentication.",
    dependencies=[Depends(utils.rate_limiter)]
)
def login(
    user: schemas.UserAuthorize,
    response: Response,
    db: Session=Depends(auth.get_db)
):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found. If new, Create Account."
        )
    
    try:
        utils.verify_password(user.password, db_user.password)
    except VerifyMismatchError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Pre-cache the expenses
    expenses = db.query(Expense).filter(Expense.owner_id == db_user.id).all()
    crud.cache_expenses_data(db_user.id, expenses)

    # Generate access token
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})

    # Generate refresh token
    refresh_token = auth.create_refresh_token({"sub": str(db_user.id)})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        path="/refresh",
        httponly=True,
        secure=True,
        samesite="Strict"
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }

@app.post(
    path="/refresh",
    tags=['Account Login'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute. Log out, copy-paste the new access token in into the 'Authorize' button at the top of the page, and click Enter.",
    description="Generates a new access token for user authentication."
)
def refresh(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please Login.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )
    
    payload = auth.decode_token(refresh_token)
    if payload == "expired":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired. Please login again.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )
    
    # Generate new access token
    new_access_token = auth.create_access_token({"sub": payload.get("sub")})
    return {
        "access_token": new_access_token,
        "token_type": "Bearer"
    }

# Expenses -----

@app.post(
    path="/expenses",
    tags=['Expenses'],
    status_code=status.HTTP_201_CREATED,
    summary="Try it out: add expense title and amount, and click Execute.",
    description="Creates a new expense record for the authorized user."
)
def new_expenses(
    expense: schemas.ExpenseCreate,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    crud.add_expenses(db, expense, user.id)
    return {
        "message": "Expense added successfully!"
    }

@app.get(
    path="/expenses",
    response_model=List[schemas.ExpenseResponse],
    tags=['Expenses'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute.",
    description="Retrieves a list of all expenses containing the expense ID, title, and amount for the authorized user."
)
def expenses(
    response: Response,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    return crud.get_expenses(db, user.id)

@app.put(
    path="/expenses/{expense_id}",
    response_model=schemas.ExpenseUpdateResponse,
    tags=['Expenses'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter expense ID, updated title, and updated amount, and click Execute.",
    description="Updates a specific expense title and amount by ID for the authorized user."
)
def expenses_update(
    expense_id: int,
    updated_data: schemas.ExpenseCreate,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    updated_expense = crud.update_expenses(db, expense_id, updated_data, user.id)
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )

    return updated_expense

@app.delete(
    path="/expenses/{expense_id}",
    tags=['Expenses'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter expense ID and click Execute.",
    description="Deletes a specific expense by ID for the authorized user."
)
def expenses_delete(
    expense_id: int,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    if not crud.delete_expenses(db, expense_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )

    return {
        "message": "Expense deleted successfully!"
    }

# Analytics -----

@app.post(
    path="/analytics",
    response_model=schemas.TotalAnalyticsResponse,
    tags=['Analytics'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute.",
    description="Calculates and returns total amount, average amount, minimum spent, maximum spent, and total items for the authorized user."
)
def total_analytics(
    period: schemas.TotalAnalytics,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    return crud.get_total_analytics(db, period, user.id)

@app.post(
    path="/item_analytics",
    response_model=List[schemas.ItemAnalyticsResponse],
    tags=['Analytics'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute.",
    description="Calculates and returns total amount, average amount, minimum spent, maximum spent, and total times on each item for the authorized user."
)
def each_item_analytics(
    period: schemas.TotalAnalytics,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    return crud.get_each_item_analytics(db, period, user.id)

# Account Settings -----

@app.put(
    path="/account/email",
    tags=['Account Settings'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter new email and click Execute.",
    description="Updates the email address for the authorized user.",
    dependencies=[Depends(utils.rate_limiter)]
)
async def update_email(
    request: schemas.UpdateEmail,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    validated_new_email = await crud.verify_email_domain(str(request.new_email))
    if validated_new_email is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Email."
        )

    if validated_new_email is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Please try again later."
        )

    if crud.get_user_by_email(db, request.new_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email is linked with another account."
        )
    
    user.email = request.new_email
    user.email_last_updated_at = func.now()
    db.commit()
    db.refresh(user)

    return {
        "message": "Email updated successfully!"
    }

@app.put(
    path="/account/password",
    tags=['Account Settings'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter old password and new password, and click Execute.",
    description="Changes the password for the authorized user.",
    dependencies=[Depends(utils.rate_limiter)]
)
def change_password(
    request: schemas.ChangePassword,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    try:
        utils.verify_password(request.old_password, user.password)
    except VerifyMismatchError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid old password."
        )
    
    try:
        utils.verify_password(request.new_password, user.password)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password should be different from old password."
        )
    except VerifyMismatchError:
        pass
    
    user.password = utils.hash_password(request.new_password)
    user.password_last_updated_at = func.now()
    db.commit()
    db.refresh(user)

    return {
        "message": "Password changed successfully!"
    }

@app.put(
    path="/account/phone",
    tags=['Account Settings'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter new mobile number and click Execute.",
    description="Changes the mobile number for the authorized user.",
    dependencies=[Depends(utils.rate_limiter)]
)
async def change_mobile_number(
    request: schemas.ChangeMobileNumber,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    if crud.get_user_by_mobile_number(db, request.new_mobile_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New mobile number is linked with another account."
        )

    user.mobile_number = request.new_mobile_number
    user.mobile_number_last_updated_at = func.now()
    db.commit()
    db.refresh(user)

    return {
        "message": "Mobile number changed successfully!"
    }

@app.post(
    path="/logout",
    tags=['Account Settings'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute.",
    description="Logs out by deleting the refresh token cookie for the authorized user."
)
def account_logout(response: Response, user: User=Depends(auth.get_authorized_user)):
    if crud.delete_cookie(response):
        return {
            "Logged out successfully!"
        }
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to logout. Please try again."
    )

@app.delete(
    path="/delete",
    tags=['Account Settings'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: click Execute.",
    description="Permanently deletes the account for the authorized user."
)
def delete_account(
    response: Response,
    db: Session=Depends(auth.get_db),
    user: User=Depends(auth.get_authorized_user)
):
    if crud.delete_cookie(response):
        if crud.delete_account(db, user.id):
            return {
                "Account deleted successfully!"
            }
        
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to delete account. Please try again."
    )

# Account Recovery -----

@app.post(
    path="/request/otp",
    tags=['Account Recovery'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter registered mobile number and click Execute.",
    description="Generates a OTP to the registered mobile number if the user account exist.",
    dependencies=[Depends(utils.rate_limiter)]
)
async def forgot_password(
    request: schemas.ForgotPassword,
    tasks: BackgroundTasks,
    db: Session=Depends(auth.get_db)
):
    if crud.get_user_by_mobile_number(db, request.registered_mobile_number):
        otp = utils.generate_otp()
        otp_key = f"otp:{request.registered_mobile_number}"
        try:
            await redis.redis_otp_storage.setex(
                otp_key,
                redis.OTP_TTL,
                otp
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Try again later."
            )

        tasks.add_task(
            crud.send_twilio_sms,
            request.registered_mobile_number,
            otp
        )

        return {
            "message": "OTP is sent to registered mobile number."
        }
    return {
            "message": "Account not found."
    }

@app.put(
    path="/enter/{otp}",
    tags=['Account Recovery'],
    status_code=status.HTTP_200_OK,
    summary="Try it out: enter the OTP recieved via SMS, registered mobile number and new password, and click Execute.",
    description="Changes the password for user account if the OTP is valid."
)
async def reset_password(
    otp: str,
    request: schemas.ResetPassword,
    db: Session=Depends(auth.get_db)
):
    otp_key = f"otp:{request.registered_mobile_number}"
    try:
        cached_otp = await redis.redis_otp_storage.get(otp_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Try again later."
        )

    if not cached_otp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP expired or never requested."
        )
    
    if cached_otp != otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP. Please check the code and try again."
        )
    
    user = crud.get_user_by_mobile_number(db, request.registered_mobile_number)
    user.password = utils.hash_password(request.new_password)
    user.password_last_updated_at = func.now()
    db.commit()
    db.refresh(user)

    try:
        await redis.redis_otp_storage.delete(otp_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Try again later."
        )

    return {
        "message": "Reset password successfull!"
    }