import uuid

class Account:
    def __init__(self, account_id: str, customer_id: int, balance: float, currency: str = "UAH"):
        self.account_id = account_id
        self.customer_id = customer_id
        self.balance = balance
        self.currency = currency

class Database:
    def __init__(self):
        self.accounts = []
        self.transfers = []
        self.customers = []

    def get_account(self, account_id: str):
        for acc in self.accounts:
            if acc.account_id == account_id:
                return acc
        return None

    def get_accounts_by_customer(self, customer_id: int):
        return [acc for acc in self.accounts if acc.customer_id == customer_id]

    def create_account(self, customer_id: int, initial_deposit: float, currency: str = "UAH"):
        account_id = f"acc-{uuid.uuid4().hex[:8]}"
        account = Account(account_id, customer_id, initial_deposit, currency)
        self.accounts.append(account)
        return account

    def add_transfer(self, transfer: dict):
        if not hasattr(self, 'transfers'):
            self.transfers = []
        self.transfers.append(transfer)
        return transfer

    def get_transfers_by_account(self, account_id: str) -> list:
        if not hasattr(self, 'transfers'):
            return []
        return [
            t for t in self.transfers
            if t.get('from_account_id') == account_id or t.get('to_account_id') == account_id
        ]

    def create_customer(self, name: str, email: str, hashed_password: str):
        customer_id = len(self.customers) + 1
        customer = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "hashed_password": hashed_password
        }
        self.customers.append(customer)
        return customer

    def get_customer_by_id(self, customer_id: int):
        for c in self.customers:
            if c.get("customer_id") == customer_id:
                return c
        return None

    def get_customer_by_email(self, email: str):
        for c in self.customers:
            if c.get("email") == email:
                return c
        return None

    def get_customer(self, customer_id: int):
        return self.get_customer_by_id(customer_id)

_db = None
def get_db():
    global _db
    if _db is None:
        _db = Database()
    return _db
