from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str


class ExpenseCreate(BaseModel):
    title: str
    amount: float


class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float

    model_config = {
        'from_attributes': True
    }