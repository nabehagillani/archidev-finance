from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: Decimal
    type: str  # income | expense | transfer
    category_id: Optional[str] = None
    bank_account_id: str
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class TransactionOut(BaseModel):
    id: str
    date: datetime
    description: str
    amount: Decimal
    type: str
    status: str
    reference: Optional[str] = None

    class Config:
        from_attributes = True
