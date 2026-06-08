from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta

from backend.users_db import add_balance, set_subscription, get_user_by_id

router = APIRouter(prefix="/api/payments", tags=["payments"])

class PaymentRequest(BaseModel):
    user_id: int
    package_id: str
    gateway: str # "yookassa" or "cryptomus"

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
    
    # Fake payment URL. In frontend we will simulate a redirect or just show success.
    payment_url = f"/mock-payment?user={req.user_id}&pack={req.package_id}&gw={req.gateway}"
    
    return {
        "status": "pending",
        "payment_url": payment_url,
        "amount": price,
        "currency": currency
    }

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
