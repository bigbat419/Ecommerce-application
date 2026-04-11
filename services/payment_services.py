import os
import requests


def initialize_transaction(email: str, amount_naira: float, callback_url: str = None) -> dict:
    """Initialize a Paystack transaction. Amount in Naira (converted to kobo internally)."""
    secret = os.getenv('PAYSTACK_SECRET_KEY', '')
    headers = {
        'Authorization': f'Bearer {secret}',
        'Content-Type': 'application/json',
    }
    payload = {
        'email': email,
        'amount': int(amount_naira * 100),
        'currency': 'NGN',
    }
    if callback_url:
        payload['callback_url'] = callback_url

    resp = requests.post(
        'https://api.paystack.co/transaction/initialize',
        json=payload,
        headers=headers,
        timeout=15,
    )
    return resp.json()


def verify_transaction(reference: str) -> dict:
    """Verify a Paystack transaction by reference."""
    secret = os.getenv('PAYSTACK_SECRET_KEY', '')
    headers = {'Authorization': f'Bearer {secret}'}
    resp = requests.get(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers=headers,
        timeout=15,
    )
    return resp.json()
