from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class InvoiceItemIn(BaseModel):
    description: str
    quantity: Decimal = 1
    unit_price: Decimal
    tax_rate: Decimal = 0


class InvoiceCreate(BaseModel):
    customer_id: str
    invoice_date: datetime
    due_date: datetime
    items: List[InvoiceItemIn]
    discount_amount: Decimal = 0
