from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta

from backend.users_db import add_balance, set_subscription, get_user_by_id
from backend.htx_client import HTXClient
import os

# Try to load environment variables from .env file in root directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# Configure HTX API credentials
HTX_ACCESS_KEY = os.environ.get("HTX_ACCESS_KEY", "")
HTX_SECRET_KEY = os.environ.get("HTX_SECRET_KEY", "")
htx_client = HTXClient(HTX_ACCESS_KEY, HTX_SECRET_KEY)

# Deposit addresses provided by the user for different networks
HTX_ADDRESSES = {
    "usdt_trc20": os.environ.get("HTX_USDT_TRC20", "TYourTRC20DepositAddressHere..."),
    "usdt_erc20": os.environ.get("HTX_USDT_ERC20", "0xYourERC20DepositAddressHere..."),
    "usdt_bep20": os.environ.get("HTX_USDT_BEP20", "0xYourBEP20DepositAddressHere...")
}

router = APIRouter(prefix="/api/payments", tags=["payments"])

class PaymentRequest(BaseModel):
    user_id: int
    package_id: str
    gateway: str # "yookassa", "cryptomus", or "htx"
    network: str = None # "usdt_trc20", "usdt_erc20", "usdt_bep20" for htx

class VerifyPaymentRequest(BaseModel):
    user_id: int
    package_id: str
    txid: str
    network: str

PACKAGES = {
    "pack_20": {"type": "balance", "amount": 20, "price_rub": 290, "price_usd": 3},
    "pack_100": {"type": "balance", "amount": 100, "price_rub": 990, "price_usd": 10},
    "sub_week": {"type": "subscription", "days": 7, "price_rub": 1490, "price_usd": 15},
    "sub_month": {"type": "subscription", "days": 30, "price_rub": 3990, "price_usd": 40},
    "sub_year": {"type": "subscription", "days": 365, "price_rub": 29000, "price_usd": 300},
}

@router.post("/create")
def create_payment(req: PaymentRequest):
    """
    Mock endpoint. In reality, it would call YooKassa or Cryptomus API
    to get a payment URL. Here we just return a fake URL that automatically
    confirms payment for testing.
    """
    if req.package_id not in PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package ID")
    
    user = get_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    pkg = PACKAGES[req.package_id]
    price = pkg["price_rub"] if req.gateway == "yookassa" else pkg["price_usd"]
    currency = "RUB" if req.gateway == "yookassa" else "USDT"
    
    if req.gateway == "htx":
        if not req.network or req.network not in HTX_ADDRESSES:
            raise HTTPException(status_code=400, detail="Invalid or missing network for HTX")
        return {
            "status": "pending",
            "deposit_address": HTX_ADDRESSES[req.network],
            "amount": price,
            "currency": currency,
            "network": req.network,
            "method": "manual_transfer"
        }
        
    # Fake payment URL for YooKassa/Cryptomus
    payment_url = f"/mock-payment?user={req.user_id}&pack={req.package_id}&gw={req.gateway}"
    
    return {
        "status": "pending",
        "payment_url": payment_url,
        "amount": price,
        "currency": currency
    }

@router.post("/verify")
def verify_htx_payment(req: VerifyPaymentRequest):
    """
    Verifies a user-provided TxID via HTX API and processes the payment if valid.
    """
    if req.package_id not in PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package ID")
        
    pkg = PACKAGES[req.package_id]
    required_amount = pkg["price_usd"]
    
    # Check HTX API
    result = htx_client.check_deposit_by_txid(req.txid)
    
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Transaction not found on HTX.")
        
    if result["state"] not in ["safe", "confirmed"]:
        raise HTTPException(status_code=400, detail="Transaction is not fully confirmed yet. Please wait a few minutes.")
        
    if result["amount"] < required_amount * 0.99: # Allow minor precision differences
        raise HTTPException(status_code=400, detail=f"Insufficient amount. Required: {required_amount}, Found: {result['amount']}")
        
    # Process payment
    if pkg["type"] == "balance":
        add_balance(req.user_id, pkg["amount"])
    elif pkg["type"] == "subscription":
        user = get_user_by_id(req.user_id)
        current_end = user.get("subscription_end")
        if current_end:
            end_dt = datetime.strptime(current_end, "%Y-%m-%d %H:%M:%S")
            if end_dt < datetime.utcnow():
                end_dt = datetime.utcnow()
        else:
            end_dt = datetime.utcnow()
            
        new_end_dt = end_dt + timedelta(days=pkg["days"])
        set_subscription(req.user_id, new_end_dt)
        
    return {"status": "success", "message": "Payment verified and processed"}

@router.post("/mock-webhook")
def mock_webhook(user_id: int, package_id: str):
    """
    Mock webhook that simulates a successful payment from the gateway.
    """
    if package_id not in PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package ID")
        
    pkg = PACKAGES[package_id]
    if pkg["type"] == "balance":
        add_balance(user_id, pkg["amount"])
    elif pkg["type"] == "subscription":
        # Calculate new end date (extend if already active)
        user = get_user_by_id(user_id)
        current_end = user.get("subscription_end")
        if current_end:
            end_dt = datetime.strptime(current_end, "%Y-%m-%d %H:%M:%S")
            if end_dt < datetime.utcnow():
                end_dt = datetime.utcnow()
        else:
            end_dt = datetime.utcnow()
            
        new_end_dt = end_dt + timedelta(days=pkg["days"])
        set_subscription(user_id, new_end_dt)
        
    return {"status": "success", "message": "Payment processed successfully"}
