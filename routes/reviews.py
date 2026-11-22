# routes/reviews.py
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import mysql

reviews_bp = Blueprint("reviews", __name__, template_folder="../templates")


@reviews_bp.route("/submit/<int:product_id>", methods=["POST"])
@login_required
def submit_review(product_id):
    """Submit or update a review for a product."""
    try:
        rating = int(request.form.get("rating", 5))
        rating = max(1, min(5, rating))          # clamp 1–5
    except (TypeError, ValueError):
        rating = 5

    title = request.form.get("title", "").strip()[:160]
    body  = request.form.get("body",  "").strip()

    cur = mysql.connection.cursor()

    # Verify product exists
    cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
    if not cur.fetchone():
        flash("Product not found.", "warning")
        cur.close()
        return redirect(url_for("products.list_products"))

    # One review per user per product — upsert
    cur.execute(
        "SELECT id FROM reviews WHERE user_id = %s AND product_id = %s",
        (current_user.id, product_id),
    )
    existing = cur.fetchone()

    if existing:
        cur.execute(
            """UPDATE reviews
               SET rating = %s, title = %s, body = %s, created_at = NOW()
               WHERE id = %s""",
            (rating, title, body, existing["id"]),
        )
        flash("Your review has been updated.", "success")
    else:
        cur.execute(
            """INSERT INTO reviews (product_id, user_id, rating, title, body)
               VALUES (%s, %s, %s, %s, %s)""",
            (product_id, current_user.id, rating, title, body),
        )
        flash("Thanks for your review! 🌟", "success")

    mysql.connection.commit()
    cur.close()

    return redirect(url_for("products.product_detail", product_id=product_id) + "#reviews")


@reviews_bp.route("/delete/<int:review_id>", methods=["POST"])
@login_required
def delete_review(review_id):
    """Let a user delete their own review."""
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, product_id FROM reviews WHERE id = %s AND user_id = %s",
        (review_id, current_user.id),
    )
    row = cur.fetchone()
    if not row:
        flash("Review not found or not yours.", "warning")
        cur.close()
        return redirect(url_for("products.list_products"))

    product_id = row["product_id"]
    cur.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
    mysql.connection.commit()
    cur.close()
    flash("Review deleted.", "info")
    return redirect(url_for("products.product_detail", product_id=product_id) + "#reviews")
