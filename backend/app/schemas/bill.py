from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class BillCreate(BaseModel):
    vendor_id: str
    bill_date: datetime
    due_date: datetime
    total: Decimal
    category_id: str          # which expense category this bill's cost belongs to
    priority: str = "normal"  # low | normal | high
