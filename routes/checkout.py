from flask import Blueprint, request, session, jsonify

checkout_bp = Blueprint("checkout", __name__)

@checkout_bp.route("/checkout", methods=["POST"])
def checkout():
    data = request.json
    session_id = session.sid
    email = data["email"]
    amount = data["amount"]
@checkout_bp.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    data = request.json
    if data.get("event")=="charge.success":
        email = data["data"]["customer"]["email"]
            # clear cart
        session["cart"] = {}
        session.modified = True

    return "",200
