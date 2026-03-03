from flask import Blueprint, request, jsonify, current_app
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    ev = request.get_json()
    current_app.logger.info('Stripe webhook received: %s', ev)
    return jsonify({'received': True}), 200
