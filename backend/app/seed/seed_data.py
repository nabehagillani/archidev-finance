"""
Generates a realistic (fictional) demo company with several months of
history so the app looks complete immediately after install: customers,
vendors, transactions, expenses, invoices (some overdue), a budget, and
a bank statement CSV pre-loaded for reconciliation testing.

Run with:  python -m app.seed.seed_data
"""
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.database.session import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.tenant import Company
from app.models.user import User, RoleName
from app.models.accounting import Account, DEFAULT_CHART_OF_ACCOUNTS
from app.models.parties import Customer, Vendor
from app.models.transaction import Transaction, TransactionType, TransactionCategory
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.models.budget import Budget
from app.services.ledger_service import post_transaction, post_invoice_issued, post_expense_approved

random.seed(42)


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Company).filter(Company.name == "Archidev").first():
        print("Demo company already exists, skipping.")
        return

    company = Company(name="Archidev", industry="Software & Technology")
    db.add(company)
    db.flush()

    accounts = {}
    for code, name, acct_type, is_bank in DEFAULT_CHART_OF_ACCOUNTS:
        a = Account(company_id=company.id, code=code, name=name, type=acct_type, is_bank_account=is_bank)
        db.add(a)
        db.flush()
        accounts[code] = a

    admin = User(company_id=company.id, email="admin@archidev.com", hashed_password=hash_password("demo1234"),
                 full_name="Sara Malik", role=RoleName.ADMIN)
    fm = User(company_id=company.id, email="finance.manager@archidev.com", hashed_password=hash_password("demo1234"),
              full_name="Bilal Ahmed", role=RoleName.FINANCE_MANAGER)
    acct_user = User(company_id=company.id, email="accountant@archidev.com", hashed_password=hash_password("demo1234"),
                      full_name="Ayesha Raza", role=RoleName.ACCOUNTANT)
    viewer = User(company_id=company.id, email="viewer@archidev.com", hashed_password=hash_password("demo1234"),
                  full_name="Omar Farooq", role=RoleName.VIEWER)
    db.add_all([admin, fm, acct_user, viewer])
    db.flush()

    txn_categories = {}
    for name, code in [("Software/Subscription", "6300"), ("Rent", "6100"), ("Utilities", "6200"),
                        ("Revenue", "4000"), ("Marketing", "6400"), ("Salaries & Wages", "6000")]:
        cat = TransactionCategory(company_id=company.id, name=name, gl_account_id=accounts[code].id,
                                   keyword_rules="netflix,subscription,saas" if "Software" in name else name.lower())
        db.add(cat)
        db.flush()
        txn_categories[name] = cat

    expense_categories = {}
    for name, code, limit in [("Rent", "6100", 3000), ("Utilities", "6200", 800), ("Software/Subscription", "6300", 1500),
                               ("Marketing", "6400", 4000), ("Office Supplies", "6500", 500), ("Salaries & Wages", "6000", 15000)]:
        cat = ExpenseCategory(company_id=company.id, name=name, gl_account_id=accounts[code].id, monthly_limit=limit)
        db.add(cat)
        db.flush()
        expense_categories[name] = cat

    customers = [Customer(company_id=company.id, name=n, email=f"{n.split()[0].lower()}@example.com")
                 for n in ["Bluepeak Retail", "Coral Fashion House", "Metro Garment Traders", "Vantage Wear Ltd"]]
    vendors = [Vendor(company_id=company.id, name=n) for n in ["FabricSource Mills", "CityPower Utilities", "CloudOps SaaS", "PrintWorks Studio"]]
    db.add_all(customers + vendors)
    db.flush()

    now = datetime.utcnow()

    # --- 6 months of income + expense transactions, with a deliberate spike ---
    for months_ago in range(6, 0, -1):
        month_start = now.replace(day=1) - relativedelta(months=months_ago)
        base_revenue = 18000 + months_ago * 800  # gentle growth trend toward present
        income_txn = Transaction(
            company_id=company.id, date=month_start + timedelta(days=3), description="Client payment - wholesale order",
            amount=round(base_revenue, 2), type=TransactionType.INCOME, category_id=txn_categories["Revenue"].id,
            bank_account_id=accounts["1000"].id, created_by=admin.id,
        )
        db.add(income_txn); db.flush()
        entry = post_transaction(db, company.id, income_txn); income_txn.journal_entry_id = entry.id

        rent_txn = Transaction(
            company_id=company.id, date=month_start + timedelta(days=1), description="Office rent",
            amount=2800, type=TransactionType.EXPENSE, category_id=txn_categories["Rent"].id,
            bank_account_id=accounts["1000"].id, created_by=admin.id,
        )
        db.add(rent_txn); db.flush()
        entry = post_transaction(db, company.id, rent_txn); rent_txn.journal_entry_id = entry.id

        # deliberate marketing spend spike in the most recent completed month for AI Insights to catch
        marketing_amount = 3800 if months_ago == 1 else 1600
        mkt_txn = Transaction(
            company_id=company.id, date=month_start + timedelta(days=10), description="Facebook Ads campaign",
            amount=marketing_amount, type=TransactionType.EXPENSE, category_id=txn_categories["Marketing"].id,
            bank_account_id=accounts["1000"].id, created_by=admin.id,
        )
        db.add(mkt_txn); db.flush()
        entry = post_transaction(db, company.id, mkt_txn); mkt_txn.journal_entry_id = entry.id

        subs_txn = Transaction(
            company_id=company.id, date=month_start + timedelta(days=5), description="CloudOps SaaS subscription",
            amount=650, type=TransactionType.EXPENSE, category_id=txn_categories["Software/Subscription"].id,
            bank_account_id=accounts["1000"].id, created_by=admin.id,
        )
        db.add(subs_txn); db.flush()
        entry = post_transaction(db, company.id, subs_txn); subs_txn.journal_entry_id = entry.id

    # --- Invoices: some paid, some open, some overdue >60 days for AR aging demo ---
    inv_specs = [
        (customers[0], 45, "sent", 30),      # 45 days ago issued, due in 30 days from issue -> now overdue ~15 days
        (customers[1], 100, "sent", 30),     # overdue > 60 days -> high risk
        (customers[2], 10, "sent", 30),      # not yet due
        (customers[3], 20, "paid", 15),
    ]
    for i, (cust, days_ago_issued, status, terms) in enumerate(inv_specs):
        issue_date = now - timedelta(days=days_ago_issued)
        due_date = issue_date + timedelta(days=terms)
        subtotal = 4500 + i * 900
        inv = Invoice(
            company_id=company.id, invoice_number=f"INV-{1001+i}", customer_id=cust.id,
            invoice_date=issue_date, due_date=due_date, subtotal=subtotal, tax_amount=0,
            total=subtotal, status=InvoiceStatus.DRAFT,
        )
        db.add(inv); db.flush()
        db.add(InvoiceItem(invoice_id=inv.id, description="Wholesale apparel order", quantity=1, unit_price=subtotal, line_total=subtotal))
        entry = post_invoice_issued(db, company.id, inv)
        inv.journal_entry_id = entry.id
        inv.status = InvoiceStatus.PAID if status == "paid" else InvoiceStatus.SENT
        if status == "paid":
            inv.amount_paid = subtotal
        db.flush()

    # --- Budget for the current month ---
    for name, code, amount in [("Marketing", "6400", 4000), ("Software/Subscription", "6300", 1500), ("Rent", "6100", 3000)]:
        db.add(Budget(company_id=company.id, category_id=expense_categories[name].id,
                       period_year=now.year, period_month=now.month, amount=amount))

    # --- A submitted (not yet approved) expense, to demo the approval workflow ---
    db.add(Expense(
        company_id=company.id, date=now - timedelta(days=2), employee_id=fm.id, vendor_id=vendors[3].id,
        category_id=expense_categories["Marketing"].id, amount=650, description="Print materials for trade show",
        status=ExpenseStatus.SUBMITTED,
    ))

    db.commit()
    print("Seed complete.")
    print("Demo company: Archidev")
    print("Logins (password: demo1234):")
    print("  admin@archidev.com            (Admin)")
    print("  finance.manager@archidev.com  (Finance Manager)")
    print("  accountant@archidev.com       (Accountant)")
    print("  viewer@archidev.com           (Viewer)")


if __name__ == "__main__":
    run()
