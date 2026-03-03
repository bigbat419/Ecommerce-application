import os
import stripe
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import mysql

checkout_bp = Blueprint('checkout', __name__, template_folder='../templates')


# ----------------------------------
# Initialize Stripe safely
# ----------------------------------
@checkout_bp.before_app_request
def init_stripe_key():
    """Ensure Stripe API key is set once the app context exists."""
    if not stripe.api_key:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY') or current_app.config.get('STRIPE_SECRET_KEY')


# ----------------------------------
# Checkout page
# ----------------------------------
@checkout_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        total = float(request.form['total'])
        email = current_user.email

        try:
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=email,
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'Order Payment'},
                        'unit_amount': int(total * 100),  # amount in cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=url_for('checkout.success', _external=True),
                cancel_url=url_for('checkout.cancel', _external=True)
            )
            return redirect(session.url, code=303)

        except Exception as e:
            flash(f'Payment failed: {str(e)}', 'danger')
            return redirect(url_for('checkout.checkout'))

    return render_template('checkout/checkout.html')


# ----------------------------------
# Success page
# ----------------------------------
@checkout_bp.route('/checkout/success')
@login_required
def success():
    return render_template('checkout/success.html')


# ----------------------------------
# Cancel page
# ----------------------------------
@checkout_bp.route('/checkout/cancel')
@login_required
def cancel():
    return render_template('checkout/cancel.html')
