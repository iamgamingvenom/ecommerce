import requests
from app.config import settings

PAYSTACK_API_URL = "https://api.paystack.co"


def initialize_paystack_transaction(email: str, amount_pesewas: int, reference: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "amount": amount_pesewas,
        "reference": reference,
    }
    
    response = requests.post(
        f"{PAYSTACK_API_URL}/transaction/initialize",
        json=payload,
        headers=headers,
        timeout=10,
    )
    
    if not response.ok:
        raise Exception(f"Paystack initialization failed: {response.text}")
        
    data = response.json()
    if not data.get("status"):
        raise Exception(f"Paystack initialization failed status: {data.get('message')}")
        
    return data["data"]["authorization_url"]


def verify_paystack_transaction(reference: str) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }
    
    response = requests.get(
        f"{PAYSTACK_API_URL}/transaction/verify/{reference}",
        headers=headers,
        timeout=10,
    )
    
    if not response.ok:
        raise Exception(f"Paystack verification call failed: {response.text}")
        
    data = response.json()
    if not data.get("status"):
        raise Exception(f"Paystack verification failed: {data.get('message')}")
        
    return data["data"]
