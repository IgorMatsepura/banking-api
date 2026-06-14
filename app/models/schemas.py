from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import  Optional, TypeVar
from datetime import datetime

T = TypeVar("T")

class Customer(BaseModel):
    """Model representing a bank customer."""
    customer_id: int
    name: str
    email: EmailStr

class AccountCreate(BaseModel):
    """Model for creating a new bank account."""
    initial_deposit: float = Field(ge=0, le=1_000_000, description="Initial deposit amount must be between 0 and 1000000")
    currency: str = Field(default="UAH", description="Currency code (UAH, USD, EUR, GBP, PLN)")
    
    @field_validator("initial_deposit")
    def check_deposit_precision(cls, value):
        """Validate that initial deposit has at most 2 decimal places.
        
        Args:
            value (float): The initial deposit amount to validate
            
        Returns:
            float: The validated deposit amount
            
        Raises:
            ValueError: If deposit has more than 2 decimal places
        """
        if round(value, 2) != value:
            raise ValueError("Initial deposit must have at most 2 decimal places")
        return value

class Account(BaseModel):
    """Model representing a bank account."""
    account_id: str
    customer_id: int
    balance: float

class TransferRequest(BaseModel):
    """Model for requesting a transfer between accounts."""

    from_account_id: str = Field(..., max_length=36, description="Valid UUID")
    to_account_id: str = Field(..., max_length=36, description="Valid UUID")
    transfer_amount: float = Field(..., gt=0, le=1_000_000, description="Must be positive and reasonable")

    @field_validator("transfer_amount")
    def check_amount_precision(cls, value):
        """Validate that transfer amount has at most 2 decimal places.
        
        Args:
            v (float): The transfer amount to validate
            
        Returns:
            float: The validated transfer amount
            
        Raises:
            ValueError: If amount has more than 2 decimal places
        """

        if round(value, 2) != value:
            raise ValueError("Transfer amount must have at most 2 decimal places")
        return value


class Transfer(BaseModel):
    """Model representing a completed transfer between accounts."""

    transaction_id: str
    from_account_id: str
    to_account_id: str
    transfer_amount: float
    timestamp: datetime


class APIResponse(BaseModel):
    """Generic API response model with optional data."""
    status: str
    data: Optional[T] = None
    message: str
    error_code: Optional[int] = None
    timestamp : datetime

class CustomerCreate(BaseModel):
    name: str
    email: str

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
