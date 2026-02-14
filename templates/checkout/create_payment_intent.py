import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

stripe.api_key = "sk_test_your_secret_key"

@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.json

    intent = stripe.PaymentIntent.create(
        amount=data["amount"],  # e.g 5000 = ₦50 or $50 (depends on currency)
        currency="usd",          # or "ngn"
        automatic_payment_methods={
            "enabled": True,
        },
    )

    return jsonify({
        "clientSecret": intent["client_secret"]
    })

if __name__ == "__main__":
    app.run(debug=True)
