# Flask eCommerce — Complete Starter (Stripe + S3 + Docker + Gunicorn + Tests)

This project is an end-to-end starter scaffold including:
- Stripe PaymentIntent flow server-side endpoints + webhook verification
- S3 file upload helper (boto3) with local fallback
- Bootstrap-based responsive frontend
- Docker + docker-compose with one-shot service to set admin password (`init-admin`)
- Gunicorn as the application server in the container
- pytest tests that run the Flask app in testing mode

Quick start with Docker
1. Copy `.env.example` -> `.env` and fill the values (especially STRIPE_* and AWS_* if you plan to use them)
2. Start services:
   ```bash
   docker-compose up --build
   ```
3. `init-admin` will run `set_admin.py` (it will wait for DB readiness and create/update the admin user using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`)

Running locally without Docker
1. pip install -r requirements.txt
2. Run MySQL and execute `db-init/seed.sql` or create schema manually.
3. Set an admin user with a hashed password using `werkzeug.security.generate_password_hash`.
4. python app.py (or use gunicorn locally)

Stripe integration
- Add your `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` to `.env`
- The endpoint `/checkout/create-payment-intent` creates a PaymentIntent and returns its `clientSecret`.
- Configure webhooks in Stripe to point to `/checkout/webhook` and set `STRIPE_WEBHOOK_SECRET` in `.env`.

S3 uploads
- Provide `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_S3_BUCKET` in `.env` to enable S3 uploads.
- If not configured, uploads fall back to local `uploads/` directory.

Tests
- Run `pytest` to execute the basic test suite.

Notes & Security
- This starter is feature-complete but still needs production hardening (HTTPS, rate limiting, input validation, monitoring, logging, secret management).
- Do not use the placeholder admin password in production. Rotate keys and secure the `.env` file.
