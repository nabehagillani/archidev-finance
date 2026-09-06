from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    date: datetime
    vendor_id: Optional[str] = None
    category_id: str
    amount: Decimal
    payment_method: Optional[str] = None
    description: Optional[str] = None


class ExpenseOut(BaseModel):
    id: str
    date: datetime
    amount: Decimal
    status: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
