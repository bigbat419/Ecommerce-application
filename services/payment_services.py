import requests
from config import PAYSTACK_SECRET

def create_payment(email, amount):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": amount * 100
    }
    res = requests.post(url,json=data,headers=headers)
    return res.json()
