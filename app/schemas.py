from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
    Field,
    ConfigDict,
    model_validator
)
import re
from decimal import Decimal
from datetime import datetime, date

# Password Description
PASSWORD_RULE_1 = "Password must be atleast 8 characters long."
PASSWORD_RULE_2 = "Password must contain atleast one lowercase letter."
PASSWORD_RULE_3 = "Password must contain atleast one uppecase letter."
PASSWORD_RULE_4 = "Password must contain atleast one digit."
PASSWORD_RULE_5 = "Password must contain atleast one special character (~`!@#$%^&*()_-+={}|:;'<,>.?/)."

MOBILE_DESCRIPTION = "Use international format +[COUNTRY CODE][MOBILE NUMBER]."

# Register -----

class UserCreate(BaseModel): 
    # Email
    email: EmailStr
    
    # Password
    password: str
    
    # Mobile Number
    phone: str

    @field_validator("password")
    def validate_password(cls, i) -> str:
        if len(i) < 8:
            raise ValueError(PASSWORD_RULE_1)
        
        if not re.search(r"[a-z]", i):
            raise ValueError(PASSWORD_RULE_2)
        
        if not re.search(r"[A-Z]", i):
            raise ValueError(PASSWORD_RULE_3)
        
        if not re.search(r"\d", i):
            raise ValueError(PASSWORD_RULE_4)
        
        if not re.search(r"[~`!@#$%^&*()_\-+={}|:;'<,>.?/]", i):
            raise ValueError(PASSWORD_RULE_5)
        
        return i
    
    @field_validator("phone")
    def validate_mobile_number(cls, i):
        if not re.match(r"^\+[1-9]\d{6,14}$", i):
            raise ValueError(MOBILE_DESCRIPTION)
        
        return i

# Login -----

class UserAuthorize(BaseModel):
    # Email
    email: str

    # Password
    password: str

# Expenses -----

class ExpenseCreate(BaseModel):
    title: str = Field(...,
        min_length=1,
        max_length=100
    )
    amount: Decimal = Field(...,
        gt=0,
        max_digits=12,
        decimal_places=2
    )

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExpenseUpdateResponse(ExpenseCreate):
    id: int

    class Config:
        from_attributes = True

# Analytics -----

class TotalAnalytics(BaseModel):
    from_date: date
    to_date: date

    @model_validator(mode="after")
    def check_date_range(i) -> TotalAnalytics:
        if i.to_date < i.from_date:
            raise ValueError(
                "'to_date' cannot be earlier than 'from_date'"
            )

        return i

class TotalAnalyticsResponse(BaseModel):
    total_amount: float
    average_amount: float
    minimum_spent: float
    maximum_spent: float
    total_items: int

    model_config = ConfigDict(from_attributes=True)

class ItemAnalyticsResponse(BaseModel):
    title: str
    total_amount: float
    average_amount: float
    minimum_spent: float
    maximum_spent: float
    total_times: int
    
    model_config = ConfigDict(from_attributes=True)

# Account -----

class UpdateEmail(BaseModel):
    # New Email
    new_email: EmailStr

class ChangePassword(BaseModel):
    # Old Password
    old_password: str
    
    # New Password
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, i) -> str:
        if len(i) < 8:
            raise ValueError(PASSWORD_RULE_1)
        
        if not re.search(r"[a-z]", i):
            raise ValueError(PASSWORD_RULE_2)
        
        if not re.search(r"[A-Z]", i):
            raise ValueError(PASSWORD_RULE_3)
        
        if not re.search(r"\d", i):
            raise ValueError(PASSWORD_RULE_4)
        
        if not re.search(r"[~`!@#$%^&*()_\-+={}|:;'<,>.?/]", i):
            raise ValueError(PASSWORD_RULE_5)
        
        return i

class ChangeMobileNumber(BaseModel):
    # New Mobile Number
    new_mobile_number: str

    @field_validator("new_mobile_number")
    def validate_mobile_number(cls, i):
        if not re.match(r"^\+[1-9]\d{6,14}$", i):
            raise ValueError(MOBILE_DESCRIPTION)
        
        return i

class ForgotPassword(BaseModel):
    registered_mobile_number: str

    @field_validator("registered_mobile_number")
    def validate_mobile_number(cls, i):
        if not re.match(r"^\+[1-9]\d{6,14}$", i):
            raise ValueError(MOBILE_DESCRIPTION)
        
        return i

class ResetPassword(BaseModel):
    registered_mobile_number: str

    @field_validator("registered_mobile_number")
    def validate_mobile_number(cls, i):
        if not re.match(r"^\+[1-9]\d{6,14}$", i):
            raise ValueError(MOBILE_DESCRIPTION)
        
        return i

    # New Password
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, i) -> str:
        if len(i) < 8:
            raise ValueError(PASSWORD_RULE_1)
        
        if not re.search(r"[a-z]", i):
            raise ValueError(PASSWORD_RULE_2)
        
        if not re.search(r"[A-Z]", i):
            raise ValueError(PASSWORD_RULE_3)
        
        if not re.search(r"\d", i):
            raise ValueError(PASSWORD_RULE_4)
        
        if not re.search(r"[~`!@#$%^&*()_\-+={}|:;'<,>.?/]", i):
            raise ValueError(PASSWORD_RULE_5)
        
        return i