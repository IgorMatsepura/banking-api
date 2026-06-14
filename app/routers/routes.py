from fastapi import APIRouter, Depends, Request, status, HTTPException
from app.database import Database, get_db

from app.models.schemas import APIResponse, AccountCreate, Account, TransferRequest, CustomerCreate
from app.services.banking_service import BankingService
from app.models.schemas import UserRegister, UserLogin, Token
from app.utils.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.utils.auth import get_current_user
from app.database import Database, get_db
from app.services.bin_checker import get_card_info
import logging
from app.utils.exceptions import SelfTransferException
from datetime import datetime, timezone
from app.database_sqlite import get_db as get_sqlite_db
from app.database_sqlite import CustomerDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["banking"])


def get_banking_service(request: Request)->BankingService:
    """Dependency injection function to provide BankingService instance.
    
    Args:

        request (Request): The FastAPI request object containing app state
        
    Returns:

        BankingService: The banking service instance from app state
    """
    return request.app.state.banking_service

@router.post("/accounts", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    service: BankingService = Depends(get_banking_service),
    current_user: dict = Depends(get_current_user),  # <-- ДОДАТИ ЦЕЙ РЯДОК
):
    """Create a new bank account for a customer.

    Args:
        account (AccountCreate): The account creation request containing initial_deposit.
        service (BankingService): The banking service dependency.
        current_user (dict): The authenticated user from token.

    Returns:
        APIResponse: Response containing the created account details.

    Raises:
        CustomerNotFoundException: If the customer_id doesn't exist.
        ValueError: If initial_deposit has more than 2 decimal places.
    """
    
    # Використовуємо customer_id з токена, а не з запиту
    created_account = service.create_account(current_user["customer_id"], account.initial_deposit, account.currency)
    account_obj = Account(
    account_id=created_account.account_id,
    customer_id=created_account.customer_id,
    balance=created_account.balance,
    currency=created_account.currency
    )
    return APIResponse(  
        status="success", 
        data=account_obj,
        message="Account created successfully",
        timestamp=datetime.now(timezone.utc)
    )

@router.post(path="/transfers", response_model=APIResponse)
async def transfer_amount(
    transfer: TransferRequest,
    service: BankingService = Depends(get_banking_service),
):
    """Execute a transfer between two accounts.
    
    Args:

        transfer (TransferRequest): Transfer details including from_account_id, to_account_id, and transfer_amount.

        service (BankingService): The banking service dependency.
        
    Returns:

        APIResponse: Response containing the transfer details.
        
    Raises:

        SelfTransferException: If from_account_id equals to_account_id.

        AccountNotFoundException: If either account doesn't exist.

        InsufficientFundsException: If source account has insufficient funds.

        ValueError: If transfer_amount has more than 2 decimal places.
    """
    if transfer.from_account_id == transfer.to_account_id:
        raise SelfTransferException()
    transfer_response = service.execute_transfer(transfer.from_account_id, transfer.to_account_id, transfer.transfer_amount)
    return APIResponse(
        status= "success",
        data= transfer_response,
        message = "Transfer executed successfully",
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/accounts/{account_id}/balance", response_model=APIResponse)
async def get_balance(
    account_id: str,
    service: BankingService = Depends(get_banking_service),
):
    """Retrieve the current balance for a specific account.
    
    Args:≈

        account_id (str): The ID of the account to check.

        service (BankingService): The banking service dependency.
        
    Returns:

        APIResponse: Response containing the account ID and current balance.
        
    Raises:

        AccountNotFoundException: If the account_id doesn't exist.
    """
    balance = service.get_balance(account_id)
    balance_response = {
        "account_id": account_id,
        "current_balance": balance
    }
    return APIResponse(
        status= "success",
        data= balance_response,
        message = "Account balance retrieved successfully",
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/accounts/{account_id}/transfers", response_model=APIResponse)
async def get_transfer_history(
    account_id: str,
    service: BankingService = Depends(get_banking_service),
):
    """Retrieve the transfer history for a specific account.
    
    Args:

        account_id (str): The ID of the account to get transfer history for.

        service (BankingService): The banking service dependency.
        
    Returns:

        APIResponse: Response containing the list of transfers.
        
    Raises:

        AccountNotFoundException: If the account_id doesn't exist.
    """

    transfer_history_response = service.get_transfers(account_id)
    return APIResponse(
    status= "success",
        data= transfer_history_response,
        message = "Transaction History retrieved successfully",
        timestamp=datetime.now(timezone.utc)
    )

@router.post("/customers", status_code=201)
async def create_customer(customer: CustomerCreate, db: Database = Depends(get_db)):
    """Створює нового клієнта в системі."""
    # Перевірка, чи email вже існує
    for existing in db.customers.values():
        if existing["email"] == customer["email"]:
            raise HTTPException(status_code=400, detail="Customer with this email already exists")
    
    new_customer = db.create_customer(customer.name, customer["email"])
    return new_customer

@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: int, 
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # <-- додали
):
    # Користувач може бачити тільки свої дані
    if customer_id != current_user["customer_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    customer = db.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
    
@router.post("/auth/register", status_code=201)
async def register(user: UserRegister, db: Database = Depends(get_db)):
    """Реєстрація нового користувача."""
    # Перевірка, чи email вже існує (потрібно зробити окремий метод)
    # Поки просто створюємо
    
    hashed_password = get_password_hash(user.password)
    new_customer = db.create_customer(user.name, user.email, hashed_password)
    
    return {"message": "User created successfully", "customer_id": new_customer["customer_id"]}     

@router.post("/auth/login", response_model=Token)
async def login(user: UserLogin, db: Database = Depends(get_db)):
    """Логін користувача, повертає JWT токен."""
    # Отримуємо всіх користувачів (потрібен новий метод)
    # Тимчасове рішення – шукаємо через перебір ID
    found_customer = None
    for i in range(1, 100):  # Перевіряємо ID 1-99
        customer = db.get_customer_by_id(i)
        if customer and customer["email"] == user.email:
            found_customer = customer
            break
    
    if not found_customer:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(user.password, found_customer["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(found_customer["customer_id"])})
    
    return {"access_token": access_token, "token_type": "bearer"}    

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Отримує інформацію про поточного користувача (захищений ендпоінт)."""
    return {
        "customer_id": current_user["customer_id"],
        "name": current_user["name"],
        "email": current_user["email"]
    }

@router.get("/my/accounts")
async def get_my_accounts(
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    accounts = db.get_accounts_by_customer(current_user["customer_id"])
    return [
        {
            "account_id": acc.account_id,
            "balance": acc.balance,
            "currency": acc.currency
        }
        for acc in accounts
    ]
            
@router.get("/check-card/{card_number}")
async def check_card_info(
    card_number: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Перевіряє інформацію про картку за її номером.
    """
    if len(card_number) < 6:
        raise HTTPException(status_code=400, detail="Card number must have at least 6 digits")
    
    bin_number = card_number[:8]
    card_info = await get_card_info(bin_number)
    
    if card_info.get("error"):
        raise HTTPException(status_code=500, detail=card_info["error"])
    
    masked_number = card_number[:4] + "****" + card_number[-4:] if len(card_number) >= 8 else card_number
    
    return {
        "card_number": masked_number,
        "bin": bin_number,
        "brand": card_info.get("brand"),
        "bank": card_info.get("bank"),
        "country": card_info.get("country"),
        "country_code": card_info.get("country_code"),
        "card_type": card_info.get("card_type"),
        "card_level": card_info.get("card_level")
    }

@router.get("/debug/customers")
async def debug_customers(db: Database = Depends(get_db)):
    return {"customers": db.customers}

@router.get("/debug/sqlite-customers")
async def debug_sqlite_customers(db=Depends(get_sqlite_db)):
    customers = db.query(CustomerDB).all()
    return [
        {
            "customer_id": c.customer_id,
            "name": c.name,
            "email": c.email
        }
        for c in customers
    ]

@router.get("/debug/db-instance")
async def debug_db_instance(db: Database = Depends(get_db)):
    return {"db_id": id(db), "customers": db.customers}

@router.post("/topup", response_model=APIResponse)
async def top_up_account(
    topup: TopUpRequest,
    service: BankingService = Depends(get_banking_service),
    current_user: dict = Depends(get_current_user)
):
    """Top up account"""
    account = service.db.get_account(topup.account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.customer_id != current_user["customer_id"]:
        raise HTTPException(status_code=403, detail="You don't own this account")
    
    # Add funds
    account.balance += topup.amount
    
    # Create transaction record
    transfer = {
        "id": str(uuid.uuid4()),
        "from_account_id": "EXTERNAL",
        "to_account_id": topup.account_id,
        "amount": topup.amount,
        "currency": topup.currency,
        "created_at": datetime.now().isoformat()
    }
    service.db.add_transfer(transfer)
    
    return APIResponse(
        status="success",
        data={"balance": account.balance, "currency": account.currency},
        message="Top up successful"
    )
